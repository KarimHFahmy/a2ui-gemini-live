/**
 * The persistent voice control.
 *
 * Voice leads, but the briefing asks for the experience to stay steerable
 * visually at any moment — hence the mute toggle, the typed fallback and a
 * visible connection state rather than a silent failure.
 */

import {useState, type FormEvent} from 'react';
import {useLocale} from '../LocaleContext';
import type {TextKey} from '../i18n';

import type {ConnectionState} from '../live/session';
import {toolLabel} from './toolLabels';

interface VoiceDockProps {
  state: ConnectionState;
  micActive: boolean;
  micLevel: number;
  agentLevel: number;
  agentSpeaking: boolean;
  onToggleMic: () => void;
  onSendText: (text: string) => void;
  /** The advisory tool currently running, if any. */
  busyTool: string | null;
}

const STATE_KEY: Record<ConnectionState, TextKey> = {
  idle: 'dock.idle',
  connecting: 'dock.connecting',
  live: 'dock.live',
  closed: 'dock.closed',
  error: 'dock.error',
};

export function VoiceDock({
  state,
  micActive,
  micLevel,
  agentLevel,
  agentSpeaking,
  onToggleMic,
  onSendText,
  busyTool,
}: VoiceDockProps) {
  const {t} = useLocale();
  const [draft, setDraft] = useState('');

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSendText(draft);
    setDraft('');
  };

  return (
    <div className="dock">
      {/*
        Nothing else on screen reports progress, so this is where the client
        learns that something is happening between "I understand" and a
        surface appearing. Tool activity takes precedence over connection
        state.
      */}
      <div className="dock__status" aria-live="polite">
        {busyTool ? (
          <>
            <span className="dock__spinner" aria-hidden="true" />
            <span className="dock__status-label">{toolLabel(t, busyTool)}</span>
          </>
        ) : (
          <>
            <span className={`dot dot--${state}`} aria-hidden="true" />
            <span className="dock__status-label">
              {agentSpeaking ? t('dock.speaking') : t(STATE_KEY[state])}
            </span>
          </>
        )}
      </div>

      <button
        type="button"
        className={`mic ${micActive ? 'is-live' : 'is-muted'}`}
        onClick={onToggleMic}
        aria-pressed={micActive}
        aria-label={micActive ? t('dock.mic.off') : t('dock.mic.on')}
      >
        <span
          className="mic__pulse"
          style={{transform: `scale(${1 + (agentSpeaking ? agentLevel : micLevel) * 0.7})`}}
          aria-hidden="true"
        />
        <svg
          viewBox="0 0 24 24"
          width="20"
          height="20"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.8}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          {micActive ? (
            <>
              <path d="M12 3a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z" />
              <path d="M19 11a7 7 0 0 1-14 0M12 18v3" />
            </>
          ) : (
            <>
              <path d="M3 3l18 18" />
              <path d="M9 9v3a3 3 0 0 0 4.5 2.6M15 11V6a3 3 0 0 0-5.9-.7" />
              <path d="M19 11a7 7 0 0 1-1.2 3.9M12 18v3M5 11a7 7 0 0 0 8.2 6.9" />
            </>
          )}
        </svg>
      </button>

      <form className="dock__type" onSubmit={submit}>
        <input
          type="text"
          value={draft}
          onChange={event => setDraft(event.target.value)}
          placeholder="Lieber tippen? Schreiben Sie einfach."
          aria-label="Nachricht an den Berater"
        />
        <button type="submit" className="btn btn--ghost" disabled={!draft.trim()}>
          Senden
        </button>
      </form>
    </div>
  );
}
