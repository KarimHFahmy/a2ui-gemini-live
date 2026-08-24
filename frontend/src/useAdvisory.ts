/**
 * The hook that ties the socket, the audio and the A2UI processor together.
 *
 * The MessageProcessor is the single source of truth for what is on screen:
 * A2UI messages go in, surfaces come out, and React only re-renders when the
 * set of surfaces changes. Per-component updates are handled inside the
 * renderer's own reactivity, so a data patch never re-renders the whole page.
 */

import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {MessageProcessor, type SurfaceModel} from '@a2ui/web_core/v0_9';
import type {ReactComponentImplementation} from '@a2ui/react/v0_9';

import {CATALOGS} from './a2ui/catalog';
import {MicrophoneCapture, SpeechPlayer} from './live/audio';
import {AdvisorySocket, type ConnectionState} from './live/session';

const INPUT_SAMPLE_RATE = 16000;
const OUTPUT_SAMPLE_RATE = 24000;

export interface AdvisoryController {
  state: ConnectionState;
  error: string | null;
  surfaces: SurfaceModel<ReactComponentImplementation>[];
  surfaceTitles: Map<string, string>;
  micActive: boolean;
  micLevel: number;
  agentLevel: number;
  agentSpeaking: boolean;
  busyTool: string | null;
  handover: unknown;
  start: (journeyId: string) => Promise<void>;
  stop: () => void;
  toggleMic: () => void;
  sendText: (text: string) => void;
}

export function useAdvisory(): AdvisoryController {
  const [state, setState] = useState<ConnectionState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [surfaces, setSurfaces] = useState<SurfaceModel<ReactComponentImplementation>[]>([]);
  const [surfaceTitles, setSurfaceTitles] = useState<Map<string, string>>(new Map());
  const [micActive, setMicActive] = useState(false);
  const [micLevel, setMicLevel] = useState(0);
  const [agentLevel, setAgentLevel] = useState(0);
  const [busyTool, setBusyTool] = useState<string | null>(null);
  const [handover, setHandover] = useState<unknown>(null);

  const socketRef = useRef<AdvisorySocket | null>(null);
  const micRef = useRef<MicrophoneCapture | null>(null);
  const playerRef = useRef<SpeechPlayer | null>(null);
  const toolTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const processor = useMemo(
    () =>
      new MessageProcessor<ReactComponentImplementation>(CATALOGS, action => {
        socketRef.current?.sendAction({
          name: action.name,
          surfaceId: action.surfaceId,
          context: action.context ?? {},
        });
      }),
    [],
  );

  const syncSurfaces = useCallback(() => {
    setSurfaces(Array.from(processor.model.surfacesMap.values()));
  }, [processor]);

  useEffect(() => {
    const created = processor.onSurfaceCreated(syncSurfaces);
    const deleted = processor.onSurfaceDeleted(syncSurfaces);
    return () => {
      created.unsubscribe();
      deleted.unsubscribe();
    };
  }, [processor, syncSurfaces]);

  const start = useCallback(
    async (journeyId: string) => {
      setError(null);
      setHandover(null);

      const player = new SpeechPlayer(OUTPUT_SAMPLE_RATE, setAgentLevel);
      playerRef.current = player;

      const socket = new AdvisorySocket({
        onState: next => setState(next),
        onAudio: chunk => player.enqueue(chunk),
        onInterrupted: () => player.interrupt(),
        onTurnComplete: () => {},
        onA2ui: message => {
          try {
            processor.processMessages([message]);
          } catch (err) {
            // One bad message must not take the surface down mid-demo.
            console.error('A2UI message rejected', err, message);
          }
        },
        onSurfaceMeta: meta => {
          setSurfaceTitles(previous => new Map(previous).set(meta.surfaceId, meta.title));
          syncSurfaces();
        },
        onTool: name => {
          setBusyTool(name);
          if (toolTimer.current) clearTimeout(toolTimer.current);
          toolTimer.current = setTimeout(() => setBusyTool(null), 1200);
        },
        onHandover: summary => setHandover(summary),
        onError: message => setError(message),
      });
      socketRef.current = socket;
      socket.connect(journeyId);

      try {
        const mic = new MicrophoneCapture(
          INPUT_SAMPLE_RATE,
          chunk => socket.sendAudio(chunk),
          setMicLevel,
        );
        await mic.start();
        micRef.current = mic;
        setMicActive(true);
      } catch {
        setMicActive(false);
        setError('Ohne Mikrofonfreigabe kann ich Sie nicht hören. Sie können trotzdem tippen.');
      }
    },
    [processor, syncSurfaces],
  );

  const stop = useCallback(() => {
    socketRef.current?.close();
    socketRef.current = null;
    void micRef.current?.stop();
    micRef.current = null;
    void playerRef.current?.close();
    playerRef.current = null;
    setMicActive(false);
    setMicLevel(0);
    setAgentLevel(0);
    setState('closed');
  }, []);

  const toggleMic = useCallback(() => {
    const mic = micRef.current;
    if (!mic) return;
    const next = !micActive;
    mic.setMuted(!next);
    setMicActive(next);
  }, [micActive]);

  const sendText = useCallback((text: string) => {
    if (!text.trim()) return;
    socketRef.current?.sendText(text);
  }, []);

  useEffect(() => () => stop(), [stop]);

  return {
    state,
    error,
    surfaces,
    surfaceTitles,
    micActive,
    micLevel,
    agentLevel,
    agentSpeaking: agentLevel > 0.02,
    busyTool,
    handover,
    start,
    stop,
    toggleMic,
    sendText,
  };
}
