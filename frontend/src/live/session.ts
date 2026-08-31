/**
 * The browser half of the advisory session.
 *
 * One WebSocket to our own backend carries everything: binary frames are audio
 * in both directions, text frames are JSON — transcripts, status, and the A2UI
 * message stream. Talking to our backend rather than to the Live API directly
 * keeps credentials server-side and lets the backend own tool execution.
 */

import type {A2uiMessage} from '@a2ui/web_core/v0_9';

export type ConnectionState = 'idle' | 'connecting' | 'live' | 'closed' | 'error';

export interface SurfaceMeta {
  surfaceId: string;
  title: string;
}

/** One station of the advisory arc, as the backend defines it. */
export interface JourneyStep {
  surfaceId: string;
  label: string;
}

/** What the journey opens with: its arc, and what it can help with. */
export interface JourneyMeta {
  steps: JourneyStep[];
  topics: string[];
}

export interface SessionCallbacks {
  onState: (state: ConnectionState, detail?: string) => void;
  onAudio: (pcm16: ArrayBuffer) => void;
  onInterrupted: () => void;
  onTurnComplete: () => void;
  onA2ui: (message: A2uiMessage) => void;
  onSurfaceMeta: (meta: SurfaceMeta & {isNew: boolean}) => void;
  onJourney: (meta: JourneyMeta) => void;
  onTool: (name: string) => void;
  onHandover: (summary: unknown) => void;
  onError: (message: string) => void;
}

export class AdvisorySocket {
  private socket: WebSocket | null = null;
  private closedByUser = false;

  constructor(private readonly callbacks: SessionCallbacks) {}

  get connected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  connect(journeyId: string, locale: string): void {
    this.closedByUser = false;
    this.callbacks.onState('connecting');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url =
      `${protocol}//${window.location.host}/ws` +
      `?journey=${encodeURIComponent(journeyId)}&lang=${encodeURIComponent(locale)}`;

    const socket = new WebSocket(url);
    socket.binaryType = 'arraybuffer';
    this.socket = socket;

    socket.onopen = () => this.callbacks.onState('live');

    socket.onmessage = event => {
      if (event.data instanceof ArrayBuffer) {
        this.callbacks.onAudio(event.data);
        return;
      }
      try {
        this.dispatch(JSON.parse(event.data as string));
      } catch {
        // A malformed frame is not worth tearing the session down for.
        console.warn('Ignoring unparseable frame from backend');
      }
    };

    socket.onerror = () => {
      this.callbacks.onError('Die Verbindung zum Berater ist gestört.');
    };

    socket.onclose = () => {
      this.socket = null;
      this.callbacks.onState(this.closedByUser ? 'closed' : 'error');
    };
  }

  private dispatch(event: Record<string, unknown>): void {
    switch (event.type) {
      case 'a2ui':
        this.callbacks.onA2ui(event.payload as A2uiMessage);
        break;
      case 'transcript':
        // The backend transcribes both sides — it is useful in logs and in the
        // handover payload — but the client renders none of it. This is a
        // voice experience; the agent answers by speaking.
        break;
      case 'turn_complete':
        this.callbacks.onTurnComplete();
        break;
      case 'interrupted':
        this.callbacks.onInterrupted();
        break;
      case 'surface_meta':
        this.callbacks.onSurfaceMeta({
          surfaceId: String(event.surfaceId),
          title: String(event.title ?? ''),
          isNew: Boolean(event.isNew),
        });
        break;
      case 'tool':
        this.callbacks.onTool(String(event.name ?? ''));
        break;
      case 'handover':
        this.callbacks.onHandover(event.summary);
        break;
      case 'error':
        this.callbacks.onError(String(event.message ?? 'Unbekannter Fehler'));
        break;
      case 'session': {
        // The arc and the topics arrive with the session, so the client never
        // has to guess which surfaces are steps or restate what the agent can
        // do in its own words.
        const journey = event.journey as Partial<JourneyMeta> | undefined;
        this.callbacks.onJourney({
          steps: journey?.steps ?? [],
          topics: journey?.topics ?? [],
        });
        break;
      }
      case 'status':
        break;
      default:
        console.debug('Unhandled backend event', event.type);
    }
  }

  sendAudio(chunk: ArrayBuffer): void {
    if (this.connected) this.socket!.send(chunk);
  }

  sendText(text: string): void {
    if (this.connected) this.socket!.send(JSON.stringify({type: 'text', text}));
  }

  /** Forwards an A2UI renderer-to-agent action so the agent can react in speech. */
  sendAction(action: {name: string; surfaceId: string; context: Record<string, unknown>}): void {
    if (this.connected) this.socket!.send(JSON.stringify({type: 'action', action}));
  }

  close(): void {
    this.closedByUser = true;
    if (this.connected) this.socket!.send(JSON.stringify({type: 'close'}));
    this.socket?.close();
    this.socket = null;
  }
}
