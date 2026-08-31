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

import {catalogsFor} from './a2ui/catalog';
import {DEFAULT_LOCALE, texts, type Locale} from './i18n';
import {MicrophoneCapture, SpeechPlayer} from './live/audio';
import {AdvisorySocket, type ConnectionState, type JourneyStep} from './live/session';

const INPUT_SAMPLE_RATE = 16000;
const OUTPUT_SAMPLE_RATE = 24000;

export interface AdvisoryController {
  state: ConnectionState;
  error: string | null;
  surfaces: SurfaceModel<ReactComponentImplementation>[];
  surfaceTitles: Map<string, string>;
  /** The advisory arc, in order, as the backend defines it. */
  steps: JourneyStep[];
  /** What this journey can help with, in the words the agent will speak. */
  topics: string[];
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

export function useAdvisory(locale: Locale = DEFAULT_LOCALE): AdvisoryController {
  const [state, setState] = useState<ConnectionState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [surfaces, setSurfaces] = useState<SurfaceModel<ReactComponentImplementation>[]>([]);
  const [surfaceTitles, setSurfaceTitles] = useState<Map<string, string>>(new Map());
  const [steps, setSteps] = useState<JourneyStep[]>([]);
  const [topics, setTopics] = useState<string[]>([]);
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
      new MessageProcessor<ReactComponentImplementation>(catalogsFor(locale), action => {
        socketRef.current?.sendAction({
          name: action.name,
          surfaceId: action.surfaceId,
          context: action.context ?? {},
        });
      }),
    [locale],
  );

  const syncSurfaces = useCallback(() => {
    setSurfaces(Array.from(processor.model.surfacesMap.values()));
  }, [processor]);

  /**
   * Empties the screen of the previous conversation.
   *
   * The MessageProcessor outlives any one session — it holds the catalogs and
   * the action handler — so surfaces from a finished conversation stay in it
   * unless they are taken out. The renderer then *rejects* the next session's
   * `createSurface` for an id it already has, the `updateComponents` behind it
   * lands in the old surface, and everything the new conversation has not
   * reached yet is still the last person's advice on screen.
   *
   * `deleteSurface` is the protocol's own way to say this, and it disposes each
   * surface's signal graph on the way out.
   */
  const clearSurfaces = useCallback(() => {
    for (const id of Array.from(processor.model.surfacesMap.keys())) {
      processor.model.deleteSurface(id);
    }
    setSurfaceTitles(new Map());
    syncSurfaces();
  }, [processor, syncSurfaces]);

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
      setSteps([]);
      setTopics([]);
      setBusyTool(null);
      // A new conversation starts on an empty screen, whatever ended the last
      // one — the restart button, a dropped socket, or an error.
      clearSurfaces();

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
        onJourney: meta => {
          setSteps(meta.steps);
          setTopics(meta.topics);
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
      socket.connect(journeyId, locale);

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
        setError(texts(locale)('dock.no_mic'));
      }
    },
    [clearSurfaces, locale, processor, syncSurfaces],
  );

  const stop = useCallback(() => {
    socketRef.current?.close();
    socketRef.current = null;
    void micRef.current?.stop();
    micRef.current = null;
    void playerRef.current?.close();
    playerRef.current = null;
    if (toolTimer.current) clearTimeout(toolTimer.current);
    clearSurfaces();
    setMicActive(false);
    setMicLevel(0);
    setAgentLevel(0);
    setBusyTool(null);
    setSteps([]);
    setTopics([]);
    setState('closed');
  }, [clearSurfaces]);

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
    steps,
    topics,
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
