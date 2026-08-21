/**
 * Where the agent-generated interface appears.
 *
 * Each A2UI surface is one advisory building block, rendered by the official
 * `A2uiSurface`. Surfaces stack in the order the agent created them, which is
 * the progressive disclosure the briefing asks for: the screen grows with the
 * conversation instead of presenting a dashboard up front.
 */

import {useEffect, useRef} from 'react';
import {A2uiSurface} from '@a2ui/react/v0_9';
import type {ReactComponentImplementation} from '@a2ui/react/v0_9';
import type {SurfaceModel} from '@a2ui/web_core/v0_9';

interface StageProps {
  surfaces: SurfaceModel<ReactComponentImplementation>[];
  titles: Map<string, string>;
  journeyLabel: string;
}

/** The profile summary stays pinned at the top; everything else stacks below. */
const PINNED_SURFACE = 'profil';

export function Stage({surfaces, titles, journeyLabel}: StageProps) {
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

  const pinned = surfaces.filter(surface => surface.id === PINNED_SURFACE);
  const rest = surfaces.filter(surface => surface.id !== PINNED_SURFACE);

  return (
    <main className="stage">
      {pinned.length > 0 ? (
        <div className="stage__pinned">
          {pinned.map(surface => (
            <div className="surface surface--pinned" key={surface.id}>
              <A2uiSurface surface={surface} />
            </div>
          ))}
        </div>
      ) : null}

      {surfaces.length === 0 ? (
        <div className="stage__empty">
          <span className="stage__empty-badge">{journeyLabel}</span>
          <h2>Ich höre zu.</h2>
          <p>
            Sobald ich Ihre Situation verstanden habe, entsteht hier Ihre persönliche
            Beratungsansicht — passend zu dem, worüber wir gerade sprechen.
          </p>
        </div>
      ) : null}

      <div className="stage__flow">
        {rest.map(surface => (
          <section
            className="surface"
            key={surface.id}
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
