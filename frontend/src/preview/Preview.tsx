/**
 * Offline preview of every advisory surface.
 *
 * Renders A2UI fixtures captured from the backend, with no Live API session in
 * play. It exists so the catalog can be reviewed, restyled and regression-
 * tested without spending a voice session — and so a design change can be
 * checked against every building block at once.
 *
 * Regenerate the fixtures with:  make fixtures
 */

import { useMemo, useState } from "react";
import { MessageProcessor } from "@a2ui/web_core/v0_9";
import { A2uiSurface } from "@a2ui/react/v0_9";
import type { ReactComponentImplementation } from "@a2ui/react/v0_9";

import { A2uiHost } from "../a2ui/A2uiHost";
import { CATALOGS } from "../a2ui/catalog";
import fixtures from "../../fixtures.json";

type Fixtures = Record<string, unknown[]>;

const JOURNEY_LABELS: Record<string, string> = {
  energie: "Mein Zuhause",
  mobilitaet: "Meine Mobilität",
};

export default function Preview() {
  const journeys = Object.keys(fixtures as Fixtures);
  const [active, setActive] = useState(journeys[0]);

  const surfaces = useMemo(() => {
    const processor = new MessageProcessor<ReactComponentImplementation>(
      CATALOGS,
      (action) => console.info("action dispatched:", action),
    );
    processor.processMessages((fixtures as Fixtures)[active] as never);
    return Array.from(processor.model.surfacesMap.values());
  }, [active]);

  return (
    <A2uiHost>
      <div className="session">
        <header className="session__bar">
          <span className="session__wordmark">Katalog-Vorschau</span>
          {journeys.map((journey) => (
            <button
              type="button"
              key={journey}
              className={`btn btn--ghost ${journey === active ? "is-active" : ""}`}
              onClick={() => setActive(journey)}
              aria-pressed={journey === active}
            >
              {JOURNEY_LABELS[journey] ?? journey}
            </button>
          ))}
          <span className="session__demo-badge">Demo-Daten</span>
        </header>

        <main className="stage" data-surface-count={surfaces.length}>
          <div className="stage__flow">
            {surfaces.map((surface) => (
              <section
                className="surface"
                key={surface.id}
                data-surface-id={surface.id}
              >
                <A2uiSurface surface={surface} />
              </section>
            ))}
          </div>
        </main>
      </div>
    </A2uiHost>
  );
}
