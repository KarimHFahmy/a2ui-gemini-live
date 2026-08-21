/**
 * Microphone capture and speech playback for the Live API.
 *
 * The Live API's contract is fixed: 16 kHz PCM16 little-endian in, 24 kHz
 * PCM16 out. Browsers give us Float32 at whatever rate the device runs, so
 * capture downsamples and converts, and playback schedules 24 kHz buffers back
 * to back so speech comes out gapless.
 */

const RECORDER_WORKLET = `
class CaptureProcessor extends AudioWorkletProcessor {
  // ~128 ms at 16 kHz once downsampled — small enough to keep latency low,
  // large enough to avoid flooding the websocket with tiny frames.
  buffer = new Float32Array(2048);
  writeIndex = 0;

  process(inputs) {
    const channel = inputs[0] && inputs[0][0];
    if (!channel) return true;

    for (let i = 0; i < channel.length; i++) {
      this.buffer[this.writeIndex++] = channel[i];
      if (this.writeIndex >= this.buffer.length) {
        this.port.postMessage(this.buffer.slice(0));
        this.writeIndex = 0;
      }
    }
    return true;
  }
}
registerProcessor('capture-processor', CaptureProcessor);
`;

export interface AudioLevel {
  /** 0..1, used to drive the mic indicator. */
  level: number;
}

export class MicrophoneCapture {
  private context: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private node: AudioWorkletNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private workletUrl: string | null = null;

  /** True while frames are actually being forwarded. */
  active = false;

  constructor(
    private readonly targetSampleRate: number,
    private readonly onChunk: (pcm16: ArrayBuffer) => void,
    private readonly onLevel?: (level: number) => void,
  ) {}

  async start(): Promise<void> {
    if (this.active) return;

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: 1,
      },
    });

    this.context = new AudioContext();
    if (this.context.state === 'suspended') await this.context.resume();

    // The worklet is inlined as a blob so the build stays a single bundle and
    // there is no extra request to fail on a cold Cloud Run start.
    this.workletUrl = URL.createObjectURL(
      new Blob([RECORDER_WORKLET], {type: 'application/javascript'}),
    );
    await this.context.audioWorklet.addModule(this.workletUrl);

    this.source = this.context.createMediaStreamSource(this.stream);
    this.node = new AudioWorkletNode(this.context, 'capture-processor');

    this.node.port.onmessage = event => {
      if (!this.active) return;
      const float32 = event.data as Float32Array;
      this.onLevel?.(rms(float32));
      const downsampled = downsample(float32, this.context!.sampleRate, this.targetSampleRate);
      this.onChunk(floatToPcm16(downsampled));
    };

    this.source.connect(this.node);
    // The worklet has no output; connecting through a muted gain node keeps it
    // scheduled in browsers that stop processing disconnected nodes.
    const mute = this.context.createGain();
    mute.gain.value = 0;
    this.node.connect(mute);
    mute.connect(this.context.destination);

    this.active = true;
  }

  /** Stops forwarding without tearing the graph down, for push-to-mute. */
  setMuted(muted: boolean): void {
    this.active = !muted;
    if (muted) this.onLevel?.(0);
  }

  async stop(): Promise<void> {
    this.active = false;
    this.node?.disconnect();
    this.source?.disconnect();
    this.stream?.getTracks().forEach(track => track.stop());
    if (this.workletUrl) URL.revokeObjectURL(this.workletUrl);
    await this.context?.close().catch(() => undefined);

    this.node = null;
    this.source = null;
    this.stream = null;
    this.context = null;
    this.workletUrl = null;
    this.onLevel?.(0);
  }
}

export class SpeechPlayer {
  private context: AudioContext | null = null;
  private gain: GainNode | null = null;
  private scheduled: AudioBufferSourceNode[] = [];
  private nextStartTime = 0;

  /** Small lead so the first chunk does not stutter on a slow first paint. */
  private readonly leadTime = 0.08;

  constructor(
    private readonly sampleRate: number,
    private readonly onLevel?: (level: number) => void,
  ) {}

  private ensureContext(): AudioContext {
    if (!this.context) {
      this.context = new AudioContext();
      this.gain = this.context.createGain();
      this.gain.connect(this.context.destination);
    }
    if (this.context.state === 'suspended') void this.context.resume();
    return this.context;
  }

  enqueue(pcm16: ArrayBuffer): void {
    const context = this.ensureContext();
    const samples = new Int16Array(pcm16);
    if (samples.length === 0) return;

    const float32 = new Float32Array(samples.length);
    for (let i = 0; i < samples.length; i++) float32[i] = samples[i] / 32768;

    const buffer = context.createBuffer(1, float32.length, this.sampleRate);
    buffer.getChannelData(0).set(float32);

    const source = context.createBufferSource();
    source.buffer = buffer;
    source.connect(this.gain!);

    const now = context.currentTime;
    this.nextStartTime = Math.max(now + this.leadTime, this.nextStartTime);
    source.start(this.nextStartTime);
    this.nextStartTime += buffer.duration;

    this.scheduled.push(source);
    this.onLevel?.(rms(float32));
    source.onended = () => {
      this.scheduled = this.scheduled.filter(s => s !== source);
      if (this.scheduled.length === 0) this.onLevel?.(0);
    };
  }

  /**
   * Barge-in: drop everything already scheduled.
   *
   * Without this the agent keeps talking over the client for as long as the
   * buffer runs, which is the single most unnatural thing a voice demo can do.
   */
  interrupt(): void {
    this.scheduled.forEach(source => {
      try {
        source.stop();
      } catch {
        /* already stopped */
      }
    });
    this.scheduled = [];
    this.nextStartTime = this.context?.currentTime ?? 0;
    this.onLevel?.(0);
  }

  async close(): Promise<void> {
    this.interrupt();
    await this.context?.close().catch(() => undefined);
    this.context = null;
    this.gain = null;
  }
}

/** Averages down to the target rate. Cheap, and adequate for speech. */
function downsample(input: Float32Array, from: number, to: number): Float32Array {
  if (to >= from) return input;

  const ratio = from / to;
  const output = new Float32Array(Math.round(input.length / ratio));

  for (let i = 0; i < output.length; i++) {
    const start = Math.round(i * ratio);
    const end = Math.min(Math.round((i + 1) * ratio), input.length);
    let sum = 0;
    for (let j = start; j < end; j++) sum += input[j];
    output[i] = end > start ? sum / (end - start) : 0;
  }

  return output;
}

function floatToPcm16(input: Float32Array): ArrayBuffer {
  const output = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    const clamped = Math.max(-1, Math.min(1, input[i]));
    output[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
  }
  return output.buffer;
}

function rms(samples: Float32Array): number {
  let sum = 0;
  for (let i = 0; i < samples.length; i++) sum += samples[i] * samples[i];
  // Scaled so ordinary speech lands around the middle of the indicator.
  return Math.min(1, Math.sqrt(sum / samples.length) * 4);
}
