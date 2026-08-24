/**
 * Adaptive Advisory Experiences — the shell.
 *
 * Two states: the landing page picks a journey, then the session view runs the
 * conversation. Everything on screen after that is built by the agent.
 */

import {useCallback, useEffect, useState} from 'react';

import {A2uiHost} from './a2ui/A2uiHost';
import {Landing, type JourneyOption} from './ui/Landing';
import {Stage} from './ui/Stage';
import {TranscriptPanel} from './ui/TranscriptPanel';
import {VoiceDock} from './ui/VoiceDock';
import {useAdvisory} from './useAdvisory';

const BRAND_NAME = import.meta.env.VITE_BRAND_NAME ?? 'Adaptive Advisory';

/** Used until /api/journeys answers, so the first paint is never empty. */
const FALLBACK_JOURNEYS: JourneyOption[] = [
  {
    id: 'energie',
    label: 'Mein Zuhause',
    tagline: 'Von komplexen Sanierungsfragen zur verständlichen persönlichen Energiewende.',
  },
  {
    id: 'mobilitaet',
    label: 'Meine Mobilität',
    tagline: 'Von Reichweitenangst und Tarifdschungel zur passenden E-Mobilitätsentscheidung.',
  },
];

function TranscriptIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      width="15"
      height="15"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      aria-hidden="true"
    >
      <path d="M4 7h16M4 12h10M4 17h13" />
    </svg>
  );
}

function RestartIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      width="15"
      height="15"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M3 12a9 9 0 1 0 3-6.7M3 4v5h5" />
    </svg>
  );
}

export default function App() {
  const [journeys, setJourneys] = useState<JourneyOption[]>(FALLBACK_JOURNEYS);
  const [active, setActive] = useState<JourneyOption | null>(null);
  const [starting, setStarting] = useState<string | null>(null);
  /**
   * The transcript is off by default. Voice leads the experience and a live
   * API needs no reading along, so the 340px it costs belongs to the advisory
   * surfaces — but the briefing asks for a visible transcript, and it is worth
   * being able to show one on demand.
   */
  const [showTranscript, setShowTranscript] = useState(false);

  const advisory = useAdvisory();

  useEffect(() => {
    let cancelled = false;
    fetch('/api/journeys')
      .then(response => (response.ok ? response.json() : null))
      .then(data => {
        if (!cancelled && data?.journeys?.length) setJourneys(data.journeys);
      })
      .catch(() => {
        /* the fallback list is good enough to run the demo */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSelect = useCallback(
    async (journeyId: string) => {
      const journey = journeys.find(item => item.id === journeyId);
      if (!journey) return;

      setStarting(journeyId);
      try {
        await advisory.start(journeyId);
        setActive(journey);
      } finally {
        setStarting(null);
      }
    },
    [advisory, journeys],
  );

  /** Ends the session and returns to the journey choice. */
  const handleRestart = useCallback(() => {
    advisory.stop();
    setActive(null);
    setShowTranscript(false);
  }, [advisory]);

  if (!active) {
    return (
      <Landing
        journeys={journeys}
        brandName={BRAND_NAME}
        onSelect={handleSelect}
        starting={starting}
      />
    );
  }

  return (
    <A2uiHost>
      <div className="session">
        <header className="session__bar">
          <span className="session__wordmark">{BRAND_NAME}</span>
          <span className="session__journey">{active.label}</span>

          <div className="session__actions">
            <button
              type="button"
              className="session__control"
              onClick={() => setShowTranscript(value => !value)}
              aria-pressed={showTranscript}
              title="Mitschrift des Gesprächs ein- oder ausblenden"
            >
              <TranscriptIcon />
              Mitschrift
            </button>

            <button
              type="button"
              className="session__control"
              onClick={handleRestart}
              title="Beratung beenden und eine andere wählen"
            >
              <RestartIcon />
              Neu starten
            </button>

            <span className="session__demo-badge" title="Alle Zahlen sind Demo-Beispielwerte">
              Demo-Daten
            </span>
          </div>
        </header>

        {advisory.error ? (
          <div className="banner banner--error" role="alert">
            {advisory.error}
          </div>
        ) : null}

        <div className={`session__body${showTranscript ? '' : ' session__body--solo'}`}>
          <Stage
            surfaces={advisory.surfaces}
            titles={advisory.surfaceTitles}
            journeyLabel={active.label}
          />
          {showTranscript ? (
            <TranscriptPanel entries={advisory.transcript} busyTool={advisory.busyTool} />
          ) : null}
        </div>

        <VoiceDock
          state={advisory.state}
          micActive={advisory.micActive}
          micLevel={advisory.micLevel}
          agentLevel={advisory.agentLevel}
          agentSpeaking={advisory.agentSpeaking}
          onToggleMic={advisory.toggleMic}
          onSendText={advisory.sendText}
          busyTool={advisory.busyTool}
        />
      </div>
    </A2uiHost>
  );
}
