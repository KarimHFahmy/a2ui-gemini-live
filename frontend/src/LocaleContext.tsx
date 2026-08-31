/**
 * The chosen language, available to every component without threading it.
 *
 * A prop would be honest but noisy: almost every component in the shell shows
 * words, so `t` would appear in every signature between `App` and a button
 * label. The A2UI surfaces do not go through here at all — they arrive from
 * the backend already written in the client's language.
 */

import {createContext, useContext, useMemo, type ReactNode} from 'react';

import {DEFAULT_LOCALE, texts, type Locale, type Texts} from './i18n';

const LocaleContext = createContext<{locale: Locale; t: Texts}>({
  locale: DEFAULT_LOCALE,
  t: texts(DEFAULT_LOCALE),
});

export function LocaleProvider({locale, children}: {locale: Locale; children: ReactNode}) {
  const value = useMemo(() => ({locale, t: texts(locale)}), [locale]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

/** `const {t} = useLocale()` in anything that shows a word. */
export function useLocale() {
  return useContext(LocaleContext);
}
