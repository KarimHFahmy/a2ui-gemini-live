/**
 * The landing page: "Mein Zuhause" or "Meine Mobilität".
 *
 * Deliberately sparse. The briefing wants the conversation to start with an
 * open question, not with a form, so this page's only job is to pick a topic
 * and hand over to the voice.
 */

export interface JourneyOption {
  id: string;
  label: string;
  tagline: string;
}

const ACCENT_ICONS: Record<string, string> = {
  energie: 'M12 2 5 13h6l-1 9 8-12h-6z',
  mobilitaet:
    'M5 16v2M19 16v2M3 16h18v-4l-2-5H5l-2 5zM7 13h.01M17 13h.01',
};

interface LandingProps {
  journeys: JourneyOption[];
  brandName: string;
  onSelect: (journeyId: string) => void;
  starting: string | null;
}

export function Landing({journeys, brandName, onSelect, starting}: LandingProps) {
  return (
    <main className="landing">
      <div className="landing__inner">
        <header className="landing__head">
          <span className="landing__wordmark">{brandName}</span>
          <h1 className="landing__title">
            Von Antworten zu <em>Beratung</em>, die sich anfühlt wie ein Gespräch.
          </h1>
          <p className="landing__lede">
            Erzählen Sie einfach von Ihrer Situation. Ich höre zu, stelle nur die Fragen,
            die wirklich weiterhelfen — und baue Ihnen währenddessen genau die Übersicht,
            die zu Ihrer Frage passt.
          </p>
        </header>

        <div className="landing__choices">
          {journeys.map(journey => (
            <button
              type="button"
              key={journey.id}
              className="choice"
              onClick={() => onSelect(journey.id)}
              disabled={starting !== null}
              aria-busy={starting === journey.id}
            >
              <span className="choice__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}
                     strokeLinecap="round" strokeLinejoin="round">
                  <path d={ACCENT_ICONS[journey.id] ?? ACCENT_ICONS.energie} />
                </svg>
              </span>
              <span className="choice__label">{journey.label}</span>
              <span className="choice__tagline">{journey.tagline}</span>
              <span className="choice__cta">
                {starting === journey.id ? 'Verbinde …' : 'Gespräch starten'}
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"
                     strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </span>
            </button>
          ))}
        </div>

        <footer className="landing__foot">
          <p>
            Sie brauchen ein Mikrofon. Das Gespräch bleibt in dieser Sitzung und wird nicht
            gespeichert. Alle gezeigten Zahlen sind gekennzeichnete Demo-Beispielwerte und
            ersetzen keine Fachberatung.
          </p>
        </footer>
      </div>
    </main>
  );
}
