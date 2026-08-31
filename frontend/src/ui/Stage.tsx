/**
 * Where the agent-generated conversation appears.
 *
 * Each A2UI surface is one advisory building block. They stack in the order
 * the agent created them, which is the progressive disclosure the briefing
 * asks for: the screen grows with the conversation rather than presenting a
 * dashboard up front. The profile is not here — see `ContextAside`.
 */

import {useEffect, useRef} from 'react';
import {A2uiSurface} from '@a2ui/react/v0_9';
import {useLocale} from '../LocaleContext';

import type {Surface} from './surfaces';

interface StageProps {
  surfaces: Surface[];
  titles: Map<string, string>;
  journeyLabel: string;
  /** What this journey can help with — the same three the agent speaks. */
  topics: string[];
  /** True once anything at all has arrived, including the profile. */
  hasAnySurface: boolean;
}

export function Stage({surfaces, titles, journeyLabel, topics, hasAnySurface}: StageProps) {
  const {t} = useLocale();
  const bottomRef = useRef<HTMLDivElement>(null);
  const previousCount = useRef(0);

  useEffect(() => {
    // Scroll only when a genuinely new surface arrives — a data patch on an
    // existing surface should never yank the page away from the reader.
    if (surfaces.length > previousCount.current) {
      bottomRef.current?.scrollIntoView({behavior: 'smooth', block: 'end'});
    }
    previousCount.current = surfaces.length;
  }, [surfaces.length]);

  return (
    <main className="stage">
      {!hasAnySurface ? (
        <div className="stage__empty">
          <span className="stage__empty-badge">{journeyLabel}</span>
          <h2>{t('stage.empty.title')}</h2>

          {/*
            The agent says these three out loud as it greets you. They are
            here as well because three topics heard once are hard to hold on
            to, and not knowing what you are allowed to say is the most common
            way a voice conversation stalls before it starts.
          */}
          {topics.length > 0 ? (
            <>
              <p className="stage__empty-lead">{t('stage.empty.topics')}</p>
              <ul className="stage__topics">
                {topics.map(topic => (
                  <li key={topic}>{topic}</li>
                ))}
              </ul>
            </>
          ) : null}

          <p>{t('stage.empty.body')}</p>
        </div>
      ) : null}

      <div className="stage__flow">
        {surfaces.map(surface => (
          <section
            className="surface"
            key={surface.id}
            data-surface-id={surface.id}
            aria-label={titles.get(surface.id) ?? surface.id}
          >
            <A2uiSurface surface={surface} />
          </section>
        ))}
      </div>

      <div ref={bottomRef} />
    </main>
  );
}
