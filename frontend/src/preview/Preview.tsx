/**
 * Offline preview of every advisory surface.
 *
 * Renders A2UI fixtures captured from the backend, with no Live API session in
 * play. It exists so the catalog can be reviewed, restyled and regression-
 * tested without spending a voice session — and so a design change can be
 * checked against every building block at once.
 *
 * It mounts the real `Stage`, not a simplified stand-in, so the sticky pinned
 * profile and the scrolling flow behave here exactly as they do in a session.
 * Layout bugs that only appear while scrolling are only catchable that way.
 *
 * Regenerate the fixtures with:  make fixtures
 */

import {useMemo, useState} from 'react';
import {MessageProcessor} from '@a2ui/web_core/v0_9';
import type {ReactComponentImplementation} from '@a2ui/react/v0_9';

import {A2uiHost} from '../a2ui/A2uiHost';
import {catalogsFor} from '../a2ui/catalog';
import {LOCALES, readLocale, type Locale} from '../i18n';
import {LocaleProvider} from '../LocaleContext';
import {ContextAside} from '../ui/ContextAside';
import {Stage} from '../ui/Stage';
import {splitSurfaces} from '../ui/surfaces';
import fixtures from '../../fixtures.json';

import type {JourneyStep} from '../live/session';

type Capture = {steps: JourneyStep[]; messages: unknown[]};
type Fixtures = Record<Locale, Record<string, Capture>>;

export default function Preview() {
  // `?lang=` picks the language, so the catalog check can render each in turn
  // in the same browser without a click.
  const [locale, setLocale] = useState<Locale>(readLocale);
  const journeys = Object.keys((fixtures as Fixtures)[locale]);
  const [active, setActive] = useState(journeys[0]);

  const {surfaces, titles, steps} = useMemo(() => {
    const processor = new MessageProcessor<ReactComponentImplementation>(
      catalogsFor(locale),
      action => console.info('action dispatched:', action),
    );
    const capture = (fixtures as Fixtures)[locale][active];
    processor.processMessages(capture.messages as never);
    const list = Array.from(processor.model.surfacesMap.values());
    return {
      surfaces: list,
      titles: new Map(list.map(surface => [surface.id, surface.id])),
      steps: capture.steps,
    };
  }, [active, locale]);

  const {profile, flow} = splitSurfaces(surfaces);
  const present = new Set(surfaces.map(surface => surface.id));

  return (
    <LocaleProvider locale={locale}>
      <A2uiHost>
        <div className="session">
          <header className="session__bar">
            <span className="session__wordmark">Katalog-Vorschau</span>
            {journeys.map(journey => (
              <button
                type="button"
                key={journey}
                className={`btn btn--ghost ${journey === active ? 'is-active' : ''}`}
                onClick={() => setActive(journey)}
                aria-pressed={journey === active}
              >
                {journey}
              </button>
            ))}
            {LOCALES.map(option => (
              <button
                type="button"
                key={option}
                className={`btn btn--ghost ${option === locale ? 'is-active' : ''}`}
                onClick={() => setLocale(option)}
                aria-pressed={option === locale}
              >
                {option}
              </button>
            ))}
          </header>

          <div className="session__body">
            <Stage
              surfaces={flow}
              titles={titles}
              journeyLabel={active}
              topics={[]}
              hasAnySurface={surfaces.length > 0}
            />
            <ContextAside profile={profile} steps={steps} present={present} />
          </div>
        </div>
      </A2uiHost>
    </LocaleProvider>
  );
}
