/**
 * Adaptive Advisory Experiences — the shell.
 *
 * Two states: the landing page picks a journey, then the session view runs the
 * conversation. Everything on screen after that is built by the agent.
 */

import {useCallback, useEffect, useMemo, useState} from 'react';

import {A2uiHost} from './a2ui/A2uiHost';
import {ContextAside} from './ui/ContextAside';
import {Landing, type JourneyOption} from './ui/Landing';
import {Stage} from './ui/Stage';
import {splitSurfaces} from './ui/surfaces';
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
  const [confirmRestart, setConfirmRestart] = useState(false);

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

  /**
   * Ends the session and returns to the journey choice.
   *
   * Confirmed inline rather than immediately: the advice is not stored
   * anywhere, so a mis-click here throws away the whole conversation.
   */
  const handleRestart = useCallback(() => {
    setConfirmRestart(false);
    advisory.stop();
    setActive(null);
  }, [advisory]);

  // The profile is context, not conversation: it gets its own column.
  const {profile, flow} = splitSurfaces(advisory.surfaces);
  const present = useMemo(
    () => new Set(advisory.surfaces.map(surface => surface.id)),
    [advisory.surfaces],
  );
  const hasContext = advisory.steps.length > 0 || profile !== null;

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
            {confirmRestart ? (
              <span className="session__confirm" role="group" aria-label="Neu starten bestätigen">
                <span className="session__confirm-text">Gespräch verwerfen?</span>
                <button
                  type="button"
                  className="session__control session__control--danger"
                  onClick={handleRestart}
                >
                  Ja, neu starten
                </button>
                <button
                  type="button"
                  className="session__control"
                  onClick={() => setConfirmRestart(false)}
                >
                  Abbrechen
                </button>
              </span>
            ) : (
              <button
                type="button"
                className="session__control"
                onClick={() => setConfirmRestart(true)}
                title="Beratung beenden und eine andere wählen"
              >
                <RestartIcon />
                Neu starten
              </button>
            )}

            {/*
             * Two things the client is entitled to know at a glance, and the
             * reason they are a permanent part of the frame rather than a
             * one-off notice: they speak to an AI, and the figures are
             * illustrative.
             */}
            <span
              className="session__badge session__badge--ai"
              title="Sie sprechen mit einem KI-Berater. Die Beratung ist unverbindlich und ersetzt keine Fachberatung."
            >
              KI-Beratung
            </span>
            <span className="session__badge" title="Alle Zahlen sind Demo-Beispielwerte">
              Demo-Daten
            </span>
          </div>
        </header>

        {advisory.error ? (
          <div className="banner banner--error" role="alert">
            {advisory.error}
          </div>
        ) : null}

        <div className={`session__body${hasContext ? '' : ' session__body--solo'}`}>
          <Stage
            surfaces={flow}
            titles={advisory.surfaceTitles}
            journeyLabel={active.label}
            topics={advisory.topics}
            hasAnySurface={advisory.surfaces.length > 0}
          />
          <ContextAside profile={profile} steps={advisory.steps} present={present} />
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
