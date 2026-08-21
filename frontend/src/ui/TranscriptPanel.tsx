/**
 * Live transcript of both sides.
 *
 * The briefing lists a visible transcript as part of the voice layer: it lets
 * the client check that they were understood, and it is what makes the
 * experience feel accountable rather than opaque.
 */

import {useEffect, useRef} from 'react';

import type {TranscriptEntry} from '../live/session';

interface TranscriptPanelProps {
  entries: TranscriptEntry[];
  busyTool: string | null;
}

const TOOL_LABEL: Record<string, string> = {
  profil_aktualisieren: 'Fasst Ihre Situation zusammen …',
  waermepumpen_eignung_zeigen: 'Prüft die Eignung Ihres Hauses …',
  szenarien_vergleichen: 'Stellt die Wege gegenüber …',
  wirtschaftlichkeit_zeigen: 'Rechnet über 20 Jahre …',
  foerderung_und_fahrplan_zeigen: 'Ermittelt Förderung und Fahrplan …',
  alltagstauglichkeit_zeigen: 'Legt Ihre Woche über die Reichweite …',
  ladeloesungen_vergleichen: 'Vergleicht die Ladeoptionen …',
  fahrzeuge_vorschlagen: 'Sucht passende Fahrzeugklassen …',
  kosten_vergleichen: 'Rechnet die Gesamtkosten …',
  bedenken_adressieren: 'Geht auf Ihre Frage ein …',
  naechsten_schritt_anbieten: 'Fasst alles zusammen …',
};

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
            <p className="turn__text">{TOOL_LABEL[busyTool] ?? 'Baut die Ansicht …'}</p>
          </div>
        ) : null}

        <div ref={endRef} />
      </div>
    </aside>
  );
}
