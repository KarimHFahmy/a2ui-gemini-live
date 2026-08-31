/**
 * The three components this demo adds to Google's basic catalog.
 *
 * Everything else on screen — headers, lists, buttons, the choice picker, the
 * sliders, the assumptions modal — is rendered by the official `@a2ui/react`
 * basic catalog, themed through its `--a2ui-*` custom properties. Only a chart,
 * a comparison table and a stat card have no official equivalent, so only those
 * are ours.
 *
 * A2UI keeps a component's API (this Zod schema) separate from its
 * implementation. The schema is the contract the agent writes against, and the
 * Generic Binder reads it to decide which props are data bindings.
 */

import {z} from 'zod';
import {CommonSchemas} from '@a2ui/web_core/v0_9';

import type {Locale} from '../i18n';

const {ComponentId, DynamicString, DynamicValue} = CommonSchemas;

/**
 * The numeric backbone of the advice.
 *
 * `categories` resolves to `string[]` and `series` to
 * `{label, werte: number[]}[]`. Rendered as inline SVG — no chart library, so
 * the bundle stays small and the visual language matches the catalog.
 */
export const MetricChartApi = {
  name: 'MetricChart',
  schema: z.object({
    title: DynamicString.optional(),
    subtitle: DynamicString.optional(),
    chartType: z.enum(['bar', 'groupedBar', 'stackedBar', 'line']).optional(),
    categories: DynamicValue,
    series: DynamicValue,
    unit: DynamicString.optional(),
    valueFormat: z.enum(['number', 'currency', 'percent']).optional(),
  }),
};

/**
 * Options as columns, criteria as rows.
 *
 * `columns` resolves to `{id, label}[]`, `rows` to
 * `{label, werte: string[], hervorheben?, akzent?}[]`. `highlight` carries the
 * id of the column to emphasise; binding it to the same path as a ChoicePicker
 * makes the two track each other client-side.
 */
export const ComparisonTableApi = {
  name: 'ComparisonTable',
  schema: z.object({
    title: DynamicString.optional(),
    columns: DynamicValue,
    rows: DynamicValue,
    highlight: DynamicValue.optional(),
  }),
};

/**
 * One figure, and what it means for the client.
 *
 * The advisory unit that repeats most often, and the reason it is ours rather
 * than a Card wrapping a Column of Texts: `tone` is the whole point. Whether a
 * number is good news, a plain fact, or an honest downside is something the
 * domain calculation knows, and it has to survive the trip to the browser —
 * otherwise the figure that says "the EV costs you 1.907 € more" is painted in
 * exactly the same colour as the one that says "you save 2,5 t of CO₂".
 *
 * The body copy stays a child rather than a prop so it still goes through the
 * official `Text` component and keeps its Markdown.
 */
export const StatCardApi = {
  name: 'StatCard',
  schema: z.object({
    title: DynamicString,
    metric: DynamicString.optional(),
    metricLabel: DynamicString.optional(),
    // A DynamicString rather than an enum so a List template can bind tone per
    // item; `asTone` is what actually narrows it, and treats anything it does
    // not recognise as neutral.
    tone: DynamicString.optional(),
    child: ComponentId.optional(),
    weight: z.number().optional(),
  }),
};

export type Tone = 'positive' | 'neutral' | 'caution';

/** What each tone means, for the people who cannot see the colour. */
/**
 * What a tone means, for a reader who cannot see the colour.
 *
 * Read out before the card's title, so it has to be in the client's language
 * like everything else — this is the one string on a surface that the backend
 * does not compose.
 */
export const TONE_LABEL: Record<Locale, Record<Tone, string>> = {
  de: {
    positive: 'Spricht dafür',
    neutral: 'Zur Einordnung',
    caution: 'Zu beachten',
  },
  en: {
    positive: 'In favour',
    neutral: 'For context',
    caution: 'Worth noting',
  },
};

export function asTone(value: unknown): Tone {
  return value === 'positive' || value === 'caution' ? value : 'neutral';
}

export type Column = {id: string; label: string};
export type Row = {
  label: string;
  werte: string[];
  hervorheben?: boolean;
  akzent?: 'positive' | 'caution';
};
export type Series = {label: string; werte: number[]};

export function asList<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

export function asStrings(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((v): v is string => typeof v === 'string') : [];
}

/**
 * Reads a highlight key.
 *
 * A ChoicePicker writes a *list* of selected values, so a path shared with a
 * picker arrives as an array while a plain literal arrives as a string.
 */
export function asKey(value: unknown): string | undefined {
  if (typeof value === 'string') return value;
  if (Array.isArray(value) && typeof value[0] === 'string') return value[0];
  return undefined;
}

/** de-DE formatting, used everywhere a figure is shown. */
const numberFormat = new Intl.NumberFormat('de-DE', {maximumFractionDigits: 0});
const currencyFormat = new Intl.NumberFormat('de-DE', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 0,
});
const percentFormat = new Intl.NumberFormat('de-DE', {
  style: 'percent',
  maximumFractionDigits: 0,
});

export function formatValue(
  value: number,
  format: 'number' | 'currency' | 'percent' = 'number',
): string {
  if (!Number.isFinite(value)) return '–';
  if (format === 'currency') return currencyFormat.format(value);
  if (format === 'percent') return percentFormat.format(value);
  return numberFormat.format(value);
}
