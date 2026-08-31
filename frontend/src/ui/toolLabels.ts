/**
 * What each advisory tool is doing, in the client's language.
 *
 * Shown while a tool runs so the pause before a surface appears reads as work
 * rather than as a hang. Keys are the tool function names in
 * `backend/app/journeys/`, prefixed — a tool the catalog has never heard of
 * still gets a sentence rather than a bare spinner.
 */

import type {TextKey, Texts} from '../i18n';

export function toolLabel(t: Texts, name: string | null): string | null {
  if (!name) return null;
  const key = `tool.${name}` as TextKey;
  try {
    return t(key) ?? t('tool.default');
  } catch {
    return t('tool.default');
  }
}
