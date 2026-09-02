/**
 * Adaptive Advisory Experiences — the shell.
 *
 * Two states: the landing page picks a journey, then the session view runs the
 * conversation. Everything on screen after that is built by the agent.
 */

import {useCallback, useEffect, useMemo, useState} from 'react';

import {A2uiHost} from './a2ui/A2uiHost';
import {BCP47, readLocale, storeLocale, texts, type Locale} from './i18n';
import {LocaleProvider} from './LocaleContext';
import {ContextAside} from './ui/ContextAside';
import {Landing, type JourneyOption} from './ui/Landing';
import {Stage} from './ui/Stage';
import {splitSurfaces} from './ui/surfaces';
import {VoiceDock} from './ui/VoiceDock';
import {useAdvisory} from './useAdvisory';

const BRAND_NAME = import.meta.env.VITE_BRAND_NAME ?? 'Adaptive Advisory';

/**
 * Used until /api/journeys answers, so the first paint is never empty.
 *
 * Only the ids are fixed: the label and tagline are written per language on
 * the backend, so hard-coding German ones here would flash them at an English
 * client for as long as the request takes.
 */
const FALLBACK_JOURNEYS: Record<Locale, JourneyOption[]> = {
  de: [
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
  ],
  en: [
    {
      id: 'energie',
      label: 'My Home',
      tagline: 'From a tangle of renovation questions to an energy transition you can follow.',
    },
    {
      id: 'mobilitaet',
      label: 'My Mobility',
      tagline: 'From range anxiety and tariff confusion to the electric decision that fits.',
    },
  ],
};

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
  const [locale, setLocale] = useState<Locale>(readLocale);
  const [journeys, setJourneys] = useState<JourneyOption[]>(FALLBACK_JOURNEYS[locale]);
  const [active, setActive] = useState<JourneyOption | null>(null);
  const [starting, setStarting] = useState<string | null>(null);
  const [confirmRestart, setConfirmRestart] = useState(false);

  const advisory = useAdvisory(locale);
  const t = useMemo(() => texts(locale), [locale]);

  // Screen readers and hyphenation both key off this, and a German page
  // announced as English is read out with the wrong phonemes.
  useEffect(() => {
    document.documentElement.lang = BCP47[locale];
  }, [locale]);

  useEffect(() => {
    let cancelled = false;
    setJourneys(FALLBACK_JOURNEYS[locale]);
    fetch(`/api/journeys?lang=${locale}`)
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
  }, [locale]);

  const handleLocale = useCallback((next: Locale) => {
    setLocale(next);
    storeLocale(next);
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
      <LocaleProvider locale={locale}>
        <Landing
          journeys={journeys}
          brandName={BRAND_NAME}
          onSelect={handleSelect}
          starting={starting}
          onLocale={handleLocale}
        />
      </LocaleProvider>
    );
  }

  return (
    <LocaleProvider locale={locale}>
      <A2uiHost>
        <div className="session">
          {/*
            The advice is the point of the page and it sits behind a header of
            controls. A keyboard user should not have to tab past the restart
            button and two badges to reach it.
          */}
          <a className="skip-link" href="#stage">
            {t('session.skip')}
          </a>
          <header className="session__bar">
            <span className="session__wordmark">{BRAND_NAME}</span>
            <span className="session__journey">{active.label}</span>

            <div className="session__actions">
              {confirmRestart ? (
                <span
                  className="session__confirm"
                  role="group"
                  aria-label={t('session.restart.aria')}
                >
                  <span className="session__confirm-text">{t('session.discard')}</span>
                  <button
                    type="button"
                    className="session__control session__control--danger"
                    onClick={handleRestart}
                  >
                    {t('session.restart.confirm')}
                  </button>
                  <button
                    type="button"
                    className="session__control"
                    onClick={() => setConfirmRestart(false)}
                  >
                    {t('session.cancel')}
                  </button>
                </span>
              ) : (
                <button
                  type="button"
                  className="session__control"
                  onClick={() => setConfirmRestart(true)}
                  title={t('session.restart.title')}
                >
                  <RestartIcon />
                  {t('session.restart')}
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
                title={t('session.badge.ai.title')}
              >
                {t('session.badge.ai')}
              </span>
              <span className="session__badge" title={t('session.badge.demo.title')}>
                {t('session.badge.demo')}
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
    </LocaleProvider>
  );
}
