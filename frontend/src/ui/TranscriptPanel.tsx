/**
 * Live transcript of both sides.
 *
 * The briefing lists a visible transcript as part of the voice layer: it lets
 * the client check that they were understood, and it is what makes the
 * experience feel accountable rather than opaque.
 */

import {useEffect, useRef} from 'react';

import type {TranscriptEntry} from '../live/session';
import {toolLabel} from './toolLabels';

interface TranscriptPanelProps {
  entries: TranscriptEntry[];
  busyTool: string | null;
}

export function TranscriptPanel({entries, busyTool}: TranscriptPanelProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({behavior: 'smooth', block: 'end'});
  }, [entries, busyTool]);

  return (
    <aside className="transcript" aria-label="Gesprächsverlauf">
      <header className="transcript__head">
        <h2>Gespräch</h2>
        <span className="transcript__hint">Mitschrift, live</span>
      </header>

      <div className="transcript__scroll">
        {entries.length === 0 ? (
          <p className="transcript__empty">
            Sprechen Sie einfach los — erzählen Sie mir von Ihrer Situation.
          </p>
        ) : null}

        {entries.map(entry => (
          <div className={`turn turn--${entry.role}`} key={entry.id}>
            <span className="turn__who">{entry.role === 'user' ? 'Sie' : 'Berater'}</span>
            <p className="turn__text">{entry.text}</p>
          </div>
        ))}

        {busyTool ? (
          <div className="turn turn--tool" aria-live="polite">
            <span className="turn__spinner" aria-hidden="true" />
            <p className="turn__text">{toolLabel(busyTool)}</p>
          </div>
        ) : null}

        <div ref={endRef} />
      </div>
    </aside>
  );
}
