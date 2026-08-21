/**
 * Adaptive Advisory Experiences — the shell.
 *
 * Two states: the landing page picks a journey, then the session view runs the
 * conversation. Everything on screen after that is built by the agent.
 */

import {useCallback, useEffect, useState} from 'react';

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
    tagline:
      'Von komplexen Sanierungsfragen zur verständlichen persönlichen Energiewende.',
  },
  {
    id: 'mobilitaet',
    label: 'Meine Mobilität',
    tagline:
      'Von Reichweitenangst und Tarifdschungel zur passenden E-Mobilitätsentscheidung.',
  },
];

export default function App() {
  const [journeys, setJourneys] = useState<JourneyOption[]>(FALLBACK_JOURNEYS);
  const [active, setActive] = useState<JourneyOption | null>(null);
  const [starting, setStarting] = useState<string | null>(null);

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

  const handleEnd = useCallback(() => {
    advisory.stop();
    setActive(null);
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
    <div className="session">
      <header className="session__bar">
        <span className="session__wordmark">{BRAND_NAME}</span>
        <span className="session__journey">{active.label}</span>
        <span className="session__demo-badge" title="Alle Zahlen sind Demo-Beispielwerte">
          Demo-Daten
        </span>
      </header>

      {advisory.error ? (
        <div className="banner banner--error" role="alert">
          {advisory.error}
        </div>
      ) : null}

      <div className="session__body">
        <Stage
          surfaces={advisory.surfaces}
          titles={advisory.surfaceTitles}
          journeyLabel={active.label}
        />
        <TranscriptPanel entries={advisory.transcript} busyTool={advisory.busyTool} />
      </div>

      <VoiceDock
        state={advisory.state}
        micActive={advisory.micActive}
        micLevel={advisory.micLevel}
        agentLevel={advisory.agentLevel}
        agentSpeaking={advisory.agentSpeaking}
        onToggleMic={advisory.toggleMic}
        onSendText={advisory.sendText}
        onEnd={handleEnd}
      />
    </div>
  );
}
