/**
 * Component APIs for the Adaptive Advisory catalog.
 *
 * A2UI keeps a component's API (this Zod schema) separate from its
 * implementation. The schema is the contract the agent writes against, and
 * `@a2ui/web_core`'s Generic Binder reads it to decide which props are data
 * bindings, which are actions and which are literals.
 *
 * Props typed with `CommonSchemas.Dynamic*` accept either a literal or a
 * `{path: '/…'}` binding, and arrive at the component already resolved.
 */

import {z} from 'zod';
import {CommonSchemas} from '@a2ui/web_core/v0_9';

const {DynamicString, DynamicNumber, DynamicValue, Action} = CommonSchemas;

const Tone = z.enum(['positive', 'neutral', 'caution']);

/** Section header framing what the client is looking at. */
export const AdvisoryHeaderApi = {
  name: 'AdvisoryHeader',
  schema: z.object({
    eyebrow: DynamicString.optional(),
    title: DynamicString,
    subtitle: DynamicString.optional(),
    icon: z.string().optional(),
  }),
};

/**
 * "Zusammenfassung des Verstandenen".
 *
 * `facts` resolves to `{label, wert, geschaetzt?}[]`; `openPoints` to a list of
 * strings. Estimated values are marked so the client can correct them.
 */
export const ProfileSummaryApi = {
  name: 'ProfileSummary',
  schema: z.object({
    title: DynamicString.optional(),
    facts: DynamicValue,
    openPoints: DynamicValue.optional(),
    note: DynamicString.optional(),
  }),
};

/** One idea, optionally with a headline metric. */
export const InsightCardApi = {
  name: 'InsightCard',
  schema: z.object({
    title: DynamicString,
    body: DynamicString.optional(),
    tone: Tone.optional(),
    icon: z.string().optional(),
    metric: DynamicString.optional(),
    metricLabel: DynamicString.optional(),
  }),
};

/**
 * Options as columns, criteria as rows.
 *
 * `columns` resolves to `{id, label}[]`, `rows` to
 * `{label, werte: string[], hervorheben?, akzent?}[]`. `highlight` carries the
 * id of the column to emphasise and is usually bound to the same path as the
 * scenario selection, so the two stay in sync client-side.
 */
export const ComparisonTableApi = {
  name: 'ComparisonTable',
  schema: z.object({
    title: DynamicString.optional(),
    columns: DynamicValue,
    rows: DynamicValue,
    highlight: DynamicString.optional(),
  }),
};

/**
 * Selectable scenario cards.
 *
 * `selected` is a two-way binding: the Generic Binder injects `setSelected`,
 * so a click updates the data model directly and anything else bound to that
 * path follows immediately, without a round trip to the agent.
 */
export const ScenarioSelectorApi = {
  name: 'ScenarioSelector',
  schema: z.object({
    title: DynamicString.optional(),
    scenarios: DynamicValue,
    selected: DynamicString.optional(),
    action: Action.optional(),
  }),
};

/**
 * The numeric backbone of the advice.
 *
 * `categories` resolves to `string[]` and `series` to
 * `{label, werte: number[]}[]`. Rendered as inline SVG — no chart library, so
 * the bundle stays small and the visual language stays ours.
 */
export const MetricChartApi = {
  name: 'MetricChart',
  schema: z.object({
    title: DynamicString.optional(),
    subtitle: DynamicString.optional(),
    chartType: z.enum(['bar', 'groupedBar', 'stackedBar', 'line', 'donut']).optional(),
    categories: DynamicValue,
    series: DynamicValue,
    unit: DynamicString.optional(),
    valueFormat: z.enum(['number', 'currency', 'percent']).optional(),
  }),
};

/** What happens when, in which order. `steps` resolves to
 * `{titel, detail?, dauer?, status?}[]`. */
export const TimelineApi = {
  name: 'Timeline',
  schema: z.object({
    title: DynamicString.optional(),
    steps: DynamicValue,
  }),
};

/** A ranked option with its trade-offs shown openly. */
export const RecommendationApi = {
  name: 'Recommendation',
  schema: z.object({
    rank: DynamicNumber.optional(),
    title: DynamicString,
    summary: DynamicString.optional(),
    fitScore: DynamicNumber.optional(),
    fitLabel: DynamicString.optional(),
    pros: DynamicValue.optional(),
    cons: DynamicValue.optional(),
  }),
};

/** The handover into a human or digital process. */
export const NextStepCTAApi = {
  name: 'NextStepCTA',
  schema: z.object({
    title: DynamicString,
    body: DynamicString.optional(),
    primaryLabel: DynamicString,
    primaryAction: Action,
    secondaryLabel: DynamicString.optional(),
    secondaryAction: Action.optional(),
  }),
};

/**
 * "Annahmen und Datenquellen sichtbar machen".
 *
 * Collapsed by default so it never competes with the advice, but always one
 * click away from every number on screen.
 */
export const AssumptionNoteApi = {
  name: 'AssumptionNote',
  schema: z.object({
    title: DynamicString.optional(),
    assumptions: DynamicValue,
    source: DynamicString.optional(),
    asOf: DynamicString.optional(),
  }),
};

/** Narrowing helpers — bound values arrive as `unknown` from the data model. */
export type Fact = {label: string; wert: string; geschaetzt?: boolean};
export type Column = {id: string; label: string};
export type Row = {
  label: string;
  werte: string[];
  hervorheben?: boolean;
  akzent?: 'positive' | 'caution';
};
export type ScenarioCard = {
  id: string;
  label: string;
  beschreibung?: string;
  kennzahl?: string;
  kennzahlLabel?: string;
  empfohlen?: boolean;
  massnahmen?: string[];
};
export type Series = {label: string; werte: number[]};
export type Step = {titel: string; detail?: string; dauer?: string; status?: string};

export function asList<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

export function asStrings(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((v): v is string => typeof v === 'string') : [];
}
