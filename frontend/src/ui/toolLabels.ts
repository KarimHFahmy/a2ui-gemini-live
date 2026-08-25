/**
 * What each advisory tool is doing, in the client's language.
 *
 * Shown while a tool runs so the pause before a surface appears reads as work
 * rather than as a hang. Keys are the tool function names in
 * `backend/app/journeys/`.
 */
export const TOOL_LABEL: Record<string, string> = {
  profil_aktualisieren: 'Fasst Ihre Situation zusammen …',
  waermepumpen_eignung_zeigen: 'Prüft die Eignung Ihres Hauses …',
  szenarien_vergleichen: 'Stellt die Wege gegenüber …',
  wirtschaftlichkeit_zeigen: 'Rechnet über 20 Jahre …',
  foerderung_und_fahrplan_zeigen: 'Ermittelt Förderung und Fahrplan …',
  alltagstauglichkeit_zeigen: 'Legt Ihre Woche über die Reichweite …',
  ladeloesungen_vergleichen: 'Vergleicht die Ladeoptionen …',
  fahrzeuge_vorschlagen: 'Sucht passende Fahrzeugklassen …',
  kosten_vergleichen: 'Rechnet die Gesamtkosten …',
  stellschrauben_zeigen: 'Macht die Rechnung verstellbar …',
  annahmen_uebernehmen: 'Rechnet mit Ihren Werten neu …',
  bedenken_adressieren: 'Geht auf Ihre Frage ein …',
  naechsten_schritt_anbieten: 'Fasst alles zusammen …',
};

export function toolLabel(name: string | null): string | null {
  if (!name) return null;
  return TOOL_LABEL[name] ?? 'Baut die Ansicht …';
}
