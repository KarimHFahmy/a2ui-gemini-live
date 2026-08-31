/**
 * The shell's own words, in both languages.
 *
 * The surfaces arrive from the backend already written in the client's
 * language — the composers do that. What is left here is the chrome around
 * them: the landing page, the voice dock, the progress rail, the labels shown
 * while a tool runs.
 *
 * Same shape as `backend/app/texts/`: two flat objects with identical keys,
 * and a test that fails when they drift. The type is derived from the German
 * one, so TypeScript refuses an English object with a key missing or spelled
 * differently — the compiler does here what a test has to do on the Python
 * side.
 */

export const LOCALES = ['de', 'en'] as const;
export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = 'de';

const de = {
  // -- Landing --------------------------------------------------------------
  'landing.title': 'Die Beratung entsteht, während Sie sprechen.',
  'landing.lede':
    'Erzählen Sie von Ihrer Situation. Was Sie sagen, wird gerechnet — und steht Satz für Satz vor Ihnen.',
  'landing.start': 'Gespräch starten',
  'landing.connecting': 'Verbinde …',
  'landing.disclaimer':
    'Sie sprechen mit einem KI-Berater und brauchen ein Mikrofon. Das Gespräch bleibt in dieser Sitzung und wird nicht gespeichert. Alle Zahlen sind gekennzeichnete Demo-Beispielwerte und ersetzen keine Fachberatung.',
  'landing.language': 'Sprache',
  'landing.language.de': 'Deutsch',
  'landing.language.en': 'English',

  // -- The hero, which is the product doing its one trick --------------------
  'hero.aria': 'Beispiel für eine Beratung',
  'hero.listening': 'hört zu',
  'hero.spoken': 'Unser Haus ist von 1985. Reicht eine Wärmepumpe im Winter?',
  'hero.eyebrow': 'Wärmepumpen-Check',
  'hero.verdict.before': 'Ihr Haus ist ',
  'hero.verdict.strong': 'gut geeignet',
  'hero.readout.1.label': 'Vorlauftemperatur',
  'hero.readout.1.value': '45',
  'hero.readout.1.unit': '°C',
  'hero.readout.1.note': 'Ihre Heizkörper sind großzügig ausgelegt',
  'hero.readout.2.label': 'Jahresarbeitszahl',
  'hero.readout.2.value': '3,8',
  'hero.readout.2.unit': '',
  'hero.readout.2.note': 'aus Vorlauf und Wärmebedarf',
  'hero.caption': 'Entstanden in dem Moment, in dem der Satz oben gesagt wurde – nicht vorher.',

  // -- The session shell ------------------------------------------------------
  'session.restart': 'Neu starten',
  'session.restart.confirm': 'Ja, neu starten',
  'session.restart.cancel': 'Weiter beraten',
  'session.restart.question': 'Gespräch wirklich neu starten?',
  'session.restart.body': 'Alles, was Sie bisher besprochen haben, geht dabei verloren.',
  'session.ai_notice': 'KI-Berater · Demo-Beispielwerte',
  'session.restart.aria': 'Neu starten bestätigen',
  'session.restart.title': 'Beratung beenden und eine andere wählen',
  'session.discard': 'Gespräch verwerfen?',
  'session.cancel': 'Abbrechen',
  'session.badge.ai': 'KI-Beratung',
  'session.badge.ai.title':
    'Sie sprechen mit einem KI-Berater. Die Beratung ist unverbindlich und ersetzt keine Fachberatung.',
  'session.badge.demo': 'Demo-Daten',
  'session.badge.demo.title': 'Alle Zahlen sind Demo-Beispielwerte',

  // -- The empty screen, before the first surface -----------------------------
  'stage.empty.title': 'Erzählen Sie einfach los.',
  'stage.empty.body': 'Was Sie sagen, wird gerechnet und erscheint hier.',
  'stage.empty.topics': 'Ich kann Ihnen helfen bei:',

  // -- Progress ---------------------------------------------------------------
  'progress.next': 'Als Nächstes: {label}',
  'progress.done': 'Alle Schritte durchlaufen',
  'progress.aria': 'Fortschritt der Beratung',

  // -- The voice dock ----------------------------------------------------------
  'dock.idle': 'Bereit',
  'dock.connecting': 'Verbinde …',
  'dock.live': 'Verbunden',
  'dock.closed': 'Beendet',
  'dock.error': 'Verbindung unterbrochen',
  'dock.speaking': 'Berater spricht',
  'dock.mic.on': 'Mikrofon aktivieren',
  'dock.mic.off': 'Mikrofon stummschalten',
  'dock.no_mic': 'Ohne Mikrofonfreigabe kann ich Sie nicht hören. Sie können trotzdem tippen.',

  // -- The context column -------------------------------------------------------
  'aside.title': 'Ihre Situation',

  // -- What a tool is doing, while it runs ---------------------------------------
  'tool.default': 'Baut die Ansicht …',
  'tool.profil_aktualisieren': 'Fasst Ihre Situation zusammen …',
  'tool.waermepumpen_eignung_zeigen': 'Prüft die Eignung Ihres Hauses …',
  'tool.szenarien_vergleichen': 'Stellt die Wege gegenüber …',
  'tool.wirtschaftlichkeit_zeigen': 'Rechnet über 20 Jahre …',
  'tool.foerderung_und_fahrplan_zeigen': 'Ermittelt Förderung und Fahrplan …',
  'tool.alltagstauglichkeit_zeigen': 'Legt Ihre Woche über die Reichweite …',
  'tool.ladeloesungen_vergleichen': 'Vergleicht die Ladeoptionen …',
  'tool.fahrzeuge_vorschlagen': 'Sucht passende Fahrzeugklassen …',
  'tool.kosten_vergleichen': 'Rechnet die Gesamtkosten …',
  'tool.stellschrauben_zeigen': 'Macht die Rechnung verstellbar …',
  'tool.annahmen_uebernehmen': 'Rechnet mit Ihren Werten neu …',
  'tool.bedenken_adressieren': 'Geht auf Ihre Frage ein …',
  'tool.naechsten_schritt_anbieten': 'Fasst alles zusammen …',
} as const;

/** Every key the shell can ask for; the English object has to match it. */
export type TextKey = keyof typeof de;

const en: Record<TextKey, string> = {
  // -- Landing --------------------------------------------------------------
  'landing.title': 'The advice takes shape while you talk.',
  'landing.lede':
    'Tell me about your situation. What you say gets calculated — and appears in front of you, sentence by sentence.',
  'landing.start': 'Start the conversation',
  'landing.connecting': 'Connecting …',
  'landing.disclaimer':
    'You are talking to an AI adviser and will need a microphone. The conversation stays in this session and is not stored. All figures are clearly marked demo examples and do not replace professional advice.',
  'landing.language': 'Language',
  'landing.language.de': 'Deutsch',
  'landing.language.en': 'English',

  // -- The hero, which is the product doing its one trick --------------------
  'hero.aria': 'An example of a session',
  'hero.listening': 'listening',
  'hero.spoken': 'Our house is from 1985. Would a heat pump be enough in winter?',
  'hero.eyebrow': 'Heat pump check',
  'hero.verdict.before': 'Your house is ',
  'hero.verdict.strong': 'a good fit',
  'hero.readout.1.label': 'Flow temperature',
  'hero.readout.1.value': '45',
  'hero.readout.1.unit': '°C',
  'hero.readout.1.note': 'your radiators are generously sized',
  'hero.readout.2.label': 'Seasonal performance',
  'hero.readout.2.value': '3.8',
  'hero.readout.2.unit': '',
  'hero.readout.2.note': 'from flow temperature and heat demand',
  'hero.caption': 'Built the moment that sentence was spoken — not before.',

  // -- The session shell ------------------------------------------------------
  'session.restart': 'Start over',
  'session.restart.confirm': 'Yes, start over',
  'session.restart.cancel': 'Keep going',
  'session.restart.question': 'Really start the conversation over?',
  'session.restart.body': 'Everything you have discussed so far will be lost.',
  'session.ai_notice': 'AI adviser · demo example values',
  'session.restart.aria': 'Confirm starting over',
  'session.restart.title': 'End this session and choose another',
  'session.discard': 'Discard the conversation?',
  'session.cancel': 'Cancel',
  'session.badge.ai': 'AI advice',
  'session.badge.ai.title':
    'You are talking to an AI adviser. This advice is non-binding and does not replace professional advice.',
  'session.badge.demo': 'Demo data',
  'session.badge.demo.title': 'All figures are demo example values',

  // -- The empty screen, before the first surface -----------------------------
  'stage.empty.title': 'Just start talking.',
  'stage.empty.body': 'What you say gets calculated and appears here.',
  'stage.empty.topics': 'I can help you with:',

  // -- Progress ---------------------------------------------------------------
  'progress.next': 'Next: {label}',
  'progress.done': 'All steps covered',
  'progress.aria': 'Progress through the session',

  // -- The voice dock ----------------------------------------------------------
  'dock.idle': 'Ready',
  'dock.connecting': 'Connecting …',
  'dock.live': 'Connected',
  'dock.closed': 'Ended',
  'dock.error': 'Connection lost',
  'dock.speaking': 'Adviser speaking',
  'dock.mic.on': 'Turn the microphone on',
  'dock.mic.off': 'Mute the microphone',
  'dock.no_mic': 'Without microphone access I cannot hear you. You can still type.',

  // -- The context column -------------------------------------------------------
  'aside.title': 'Your situation',

  // -- What a tool is doing, while it runs ---------------------------------------
  'tool.default': 'Building the view …',
  'tool.profil_aktualisieren': 'Summarising your situation …',
  'tool.waermepumpen_eignung_zeigen': 'Checking whether your house suits one …',
  'tool.szenarien_vergleichen': 'Setting the routes side by side …',
  'tool.wirtschaftlichkeit_zeigen': 'Working it out over 20 years …',
  'tool.foerderung_und_fahrplan_zeigen': 'Working out the subsidy and the plan …',
  'tool.alltagstauglichkeit_zeigen': 'Laying your week over the range …',
  'tool.ladeloesungen_vergleichen': 'Comparing the charging options …',
  'tool.fahrzeuge_vorschlagen': 'Looking for classes that fit …',
  'tool.kosten_vergleichen': 'Adding up the total cost …',
  'tool.stellschrauben_zeigen': 'Making the calculation adjustable …',
  'tool.annahmen_uebernehmen': 'Recalculating with your values …',
  'tool.bedenken_adressieren': 'Taking your question on …',
  'tool.naechsten_schritt_anbieten': 'Pulling it all together …',
};

export const CATALOGS: Record<Locale, Record<TextKey, string>> = {de, en};

/** BCP-47 tags, for `<html lang>` and for the renderer's number formatting. */
export const BCP47: Record<Locale, string> = {de: 'de-DE', en: 'en-GB'};

/**
 * Reads the locale the client chose.
 *
 * `?lang=` wins so a link can pin a language for a demo; otherwise the last
 * choice, which survives a reload and a restart. Never the browser's own
 * language: the content is written for the German market and defaulting an
 * English-configured laptop away from it would be the wrong guess more often
 * than not.
 */
export function readLocale(): Locale {
  const fromUrl = new URLSearchParams(window.location.search).get('lang');
  if (isLocale(fromUrl)) return fromUrl;

  try {
    const stored = window.localStorage.getItem('advisory.locale');
    if (isLocale(stored)) return stored;
  } catch {
    // Private windows and blocked site data both throw here; the default is
    // a perfectly good answer.
  }
  return DEFAULT_LOCALE;
}

export function storeLocale(locale: Locale): void {
  try {
    window.localStorage.setItem('advisory.locale', locale);
  } catch {
    // Same as above: remembering the choice is a convenience, not a
    // requirement.
  }
}

function isLocale(value: string | null): value is Locale {
  return value !== null && (LOCALES as readonly string[]).includes(value);
}

/** One locale's words, with `{named}` holes filled in. */
export function texts(locale: Locale) {
  const catalog = CATALOGS[locale] ?? CATALOGS[DEFAULT_LOCALE];
  return (key: TextKey, fields?: Record<string, string | number>): string => {
    const value = catalog[key];
    if (!fields) return value;
    return value.replace(/\{(\w+)\}/g, (whole, name) =>
      name in fields ? String(fields[name]) : whole,
    );
  };
}

export type Texts = ReturnType<typeof texts>;
