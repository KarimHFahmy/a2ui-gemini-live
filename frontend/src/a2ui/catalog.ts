/**
 * The approved catalog this renderer accepts.
 *
 * A2UI's security model is a whitelist: the agent can only ask for components
 * that exist here. Anything else renders as an explicit "unknown component"
 * rather than executing.
 *
 * A2UI v0.9 resolves every component against the *surface's* catalog — there
 * is no per-component `catalogId` override (that arrives in v1.0). So the
 * Adaptive Advisory catalog is a superset: the official basic catalog's
 * components and functions, plus our advisory building blocks, under one id.
 * The agent composes layout with `Row`/`Column` and content with the advisory
 * blocks, and both resolve from the same catalog.
 */

import {Catalog} from '@a2ui/web_core/v0_9';
import {createBasicCatalogFunctions} from '@a2ui/web_core/v0_9/basic_catalog';
import {basicCatalog} from '@a2ui/react/v0_9';
import type {ReactComponentImplementation} from '@a2ui/react/v0_9';

import {BCP47, type Locale} from '../i18n';
import {ADVISORY_COMPONENTS} from './components/blocks';

/** Must match `ADVISORY_CATALOG_ID` in `backend/app/a2ui/protocol.py`. */
export const ADVISORY_CATALOG_ID = 'urn:a2ui:catalog:adaptive-advisory:1.0';

const BASIC_COMPONENTS = Array.from(basicCatalog.components.values());

/**
 * The catalog's functions run in the browser, and some of them format numbers.
 *
 * The default set closes over the *viewer's* locale, which would print a
 * figure as "€1,234.00" on an English browser inside a German session. So the
 * locale is pinned to the one the client chose — the same one the surfaces
 * were composed in, so a slider-driven figure and the card above it agree.
 *
 * Built per locale rather than once, because the choice is made before the
 * first surface arrives and never changes inside a session.
 */
const catalogsByLocale = new Map<Locale, Catalog<ReactComponentImplementation>[]>();

export function catalogsFor(locale: Locale): Catalog<ReactComponentImplementation>[] {
  const cached = catalogsByLocale.get(locale);
  if (cached) return cached;

  const advisory = new Catalog<ReactComponentImplementation>(
    ADVISORY_CATALOG_ID,
    [...BASIC_COMPONENTS, ...ADVISORY_COMPONENTS],
    createBasicCatalogFunctions({locale: BCP47[locale]}),
  );
  // The basic catalog stays registered under its own id too, so a surface the
  // agent creates against the standard catalog id still renders.
  const catalogs = [advisory, basicCatalog];
  catalogsByLocale.set(locale, catalogs);
  return catalogs;
}

export {basicCatalog};
