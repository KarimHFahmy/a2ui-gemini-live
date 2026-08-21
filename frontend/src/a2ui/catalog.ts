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
import {BASIC_FUNCTIONS} from '@a2ui/web_core/v0_9/basic_catalog';
import {basicCatalog} from '@a2ui/react/v0_9';
import type {ReactComponentImplementation} from '@a2ui/react/v0_9';

import {ADVISORY_COMPONENTS} from './components/blocks';

/** Must match `ADVISORY_CATALOG_ID` in `backend/app/a2ui/protocol.py`. */
export const ADVISORY_CATALOG_ID = 'urn:a2ui:catalog:adaptive-advisory:1.0';

const BASIC_COMPONENTS = Array.from(basicCatalog.components.values());

export const advisoryCatalog = new Catalog<ReactComponentImplementation>(
  ADVISORY_CATALOG_ID,
  [...BASIC_COMPONENTS, ...ADVISORY_COMPONENTS],
  BASIC_FUNCTIONS,
);

/**
 * The basic catalog stays registered under its own id too, so a surface the
 * agent creates against the standard catalog id still renders.
 */
export const CATALOGS = [advisoryCatalog, basicCatalog];

export {basicCatalog};
