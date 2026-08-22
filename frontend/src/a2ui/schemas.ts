/**
 * The two components this demo adds to Google's basic catalog.
 *
 * Everything else on screen — headers, cards, lists, buttons, the choice
 * picker, the assumptions modal — is rendered by the official `@a2ui/react`
 * basic catalog, themed through its `--a2ui-*` custom properties. Only a chart
 * and a comparison table have no official equivalent, so only those are ours.
 *
 * A2UI keeps a component's API (this Zod schema) separate from its
 * implementation. The schema is the contract the agent writes against, and the
 * Generic Binder reads it to decide which props are data bindings.
 */

import {z} from 'zod';
import {CommonSchemas} from '@a2ui/web_core/v0_9';

const {DynamicString, DynamicValue} = CommonSchemas;

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
