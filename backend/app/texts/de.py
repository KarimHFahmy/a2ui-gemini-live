"""German, the language this product was designed in.

The originals: every string here was written for the German market first, and
`en.py` is the translation of it. Keys are grouped by the surface they appear
on. `{placeholders}` are filled by `Texts.__call__`.
"""

from __future__ import annotations

from typing import Any

TEXTS: dict[str, Any] = {
    # -- Data provenance, shown under every figure --------------------------
    "data.as_of": "Demo-Annahmen, Stand Q3/2026",
    "data.source.energie": "Demo-Datensatz Energie (Beispielwerte, keine Angebotsgrundlage)",
    "data.source.mobilitaet": (
        "Demo-Datensatz E-Mobilität (Beispielwerte, keine Angebotsgrundlage)"
    ),
    "data.disclaimer": (
        "Alle Zahlen sind Demo-Beispielwerte zur Veranschaulichung. "
        "Sie ersetzen keine Fachberatung und sind kein verbindliches Angebot."
    ),
    "data.foerderung.hinweis": (
        "Förderhöhe abhängig von Antragstellung, Einkommensnachweis und "
        "Gebäudetyp. Demo-Abbildung, bitte im Einzelfall prüfen."
    ),
    # -- Building blocks used by every surface -------------------------------
    "block.assumptions.trigger": "Annahmen und Datenquellen ansehen",
    "block.assumptions.title": "Annahmen und Datenquellen",
    "block.assumptions.source": "{source} · {as_of}",
    "block.none_open": "Keine offenen Punkte",
    "block.still_open": "Noch offen",
    "block.dash": "–",
    # -- The profile surface, pinned in the context column -------------------
    "profil.eyebrow": "Ihre Situation",
    "profil.title": "Das habe ich verstanden",
    "profil.correct_me": "Sagen Sie einfach, wenn etwas nicht stimmt – ich passe es an.",
    # -- The handover ---------------------------------------------------------
    "handover.eyebrow": "Ihr nächster Schritt",
    "handover.subtitle": "Alles, was wir besprochen haben, in einer Übersicht.",
    "handover.recommendation": "Meine Empfehlung für Sie",
    "handover.pro": "Dafür spricht",
    "handover.open": "Noch zu klären",
    "handover.not_binding": "Sie entscheiden, wie es weitergeht – nichts davon ist verbindlich.",
    "handover.second.energie": "Zusammenfassung per E-Mail",
    "handover.second.mobilitaet": "Angebot anfordern",
    "handover.title.energie": "Ihr Weg zur neuen Heizung",
    "handover.title.mobilitaet": "Ihr Weg zur E-Mobilität",
    "schritt.beratungstermin": "Beratungstermin vereinbaren",
    "schritt.vor_ort_check": "Vor-Ort-Check anfragen",
    "schritt.foerder_check": "Förderfähigkeit prüfen lassen",
    "schritt.probefahrt": "Probefahrt vereinbaren",
    "schritt.ladecheck": "Ladecheck zu Hause anfragen",
    "schritt.angebot": "Persönliches Angebot anfordern",
    "energie.massnahmen.keine": 'Keine Vorbereitung nötig',
    "energie.massnahmen.wp": 'Luft/Wasser-Wärmepumpe',
    "energie.massnahmen.heizkoerper": 'Tausch kritischer Heizkörper',
    "energie.massnahmen.daemmung": 'Dachdämmung',
    "energie.massnahmen.pv": 'PV-Anlage mit Speicher',
    "hinweis.profil": 'Bestätige kurz, was du verstanden hast, ohne alle Werte vorzulesen.',
    "hinweis.foerderung": 'Antrag muss vor Beauftragung gestellt werden — sprich das aus.',
    "hinweis.regler": 'Die Person kann die Regler selbst bewegen. Lade sie dazu ein, statt Zahlen vorzulesen.',
    "hinweis.uebernommen.energie": 'Bestätige kurz, dass ab jetzt mit den Preisen der Person gerechnet wird, und nenne, was sich dadurch verschoben hat.',
    "hinweis.uebernommen.mobilitaet": 'Bestätige kurz, dass ab jetzt mit den Werten der Person gerechnet wird, und nenne, was sich dadurch verschoben hat. Rufe danach `profil_aktualisieren` auf, damit die Zusammenfassung stimmt.',
    "hinweis.teurer": 'Wenn das E-Auto teurer ist, benenne das offen und zeig über die Ladeoptionen, was sich ändern müsste.',
    "energie.massnahmen.abgleich": 'Hydraulischer Abgleich',
    "energie.massnahmen.pv_anlage": 'PV-Anlage 10 kWp',
    "energie.massnahmen.speicher": 'Batteriespeicher 8 kWh',
    "handover.assumptions": [
        "Diese Beratung ist unverbindlich und ersetzt kein Angebot.",
        "Ihre Angaben bleiben in dieser Sitzung und werden nicht gespeichert.",
    ],
    # ======================================================================
    # Mein Zuhause — Energieberatung
    # ======================================================================
    "energie.heizung.gas": "Gasheizung",
    "energie.heizung.oel": "Ölheizung",
    "energie.heizung.fernwaerme": "Fernwärme",
    "energie.heizung.nachtspeicher": "Nachtspeicherheizung",
    "energie.heizung.waermepumpe": "Wärmepumpe",
    "energie.traeger.gas": "Erdgas",
    "energie.traeger.oel": "Heizöl",
    "energie.traeger.fernwaerme": "Fernwärme",
    "energie.traeger.strom": "Strom",
    "energie.stand.unsaniert": "weitgehend unsaniert",
    "energie.stand.teilsaniert": "teilsaniert",
    "energie.stand.saniert": "gut saniert",
    # -- Profile ------------------------------------------------------------
    "energie.profil.gebaeude": "Gebäude",
    "energie.profil.gebaeude_wert": "Baujahr {baujahr}, {flaeche} m²",
    "energie.profil.heizung": "Heizung heute",
    "energie.profil.zustand": "Zustand",
    "energie.profil.haushalt": "Haushalt",
    "energie.profil.haushalt_wert": "{personen} Personen",
    "energie.profil.bedarf": "Wärmebedarf",
    "energie.profil.bedarf_wert": "{bedarf} kWh/Jahr",
    "energie.profil.prioritaeten": "Wichtig für Sie",
    "energie.profil.bedenken": "Ihre Bedenken",
    # -- Suitability check ---------------------------------------------------
    "energie.eignung.eyebrow": "Wärmepumpen-Check",
    "energie.eignung.title": "Ihr Haus ist {urteil}",
    "energie.eignung.subtitle": (
        "Entscheidend ist nicht die Außentemperatur, sondern wie warm das Wasser "
        "in Ihren Heizkörpern sein muss."
    ),
    "energie.eignung.vorlauf": "Nötige Vorlauftemperatur",
    "energie.eignung.vorlauf_label": "im Auslegungsfall",
    "energie.eignung.vorlauf_body": (
        "Je niedriger, desto effizienter arbeitet die Wärmepumpe. Unter 55 °C ist "
        "der Betrieb unkritisch."
    ),
    "energie.eignung.jaz": "Erwartete Jahresarbeitszahl",
    "energie.eignung.jaz_label": "JAZ",
    "energie.eignung.jaz_body": (
        "Aus 1 kWh Strom werden {jaz} kWh Wärme – rund {strom} kWh Strom im Jahr."
    ),
    "energie.eignung.heizlast": "Benötigte Heizleistung",
    "energie.eignung.heizlast_label": "Norm-Heizlast",
    "energie.eignung.heizlast_body": (
        "Danach wird die Wärmepumpe ausgelegt. Zu groß dimensioniert taktet sie "
        "und verschleißt schneller."
    ),
    "energie.eignung.chart_title": "So verteilt sich Ihre Heizlast über den Winter",
    "energie.eignung.chart_sub_stab": (
        "Auch im Januar deckt die Wärmepumpe die Last – an den kältesten Tagen "
        "mit Heizstab."
    ),
    "energie.eignung.chart_sub_allein": "Auch im Januar deckt die Wärmepumpe die Last allein.",
    "energie.eignung.serie_wp": "Wärmepumpe",
    "energie.eignung.serie_heizstab": "Heizstab",
    "energie.eignung.massnahmen": "Was die Effizienz noch verbessert",
    "energie.monate": ["Okt", "Nov", "Dez", "Jan", "Feb", "Mär", "Apr"],
    # -- Scenarios ------------------------------------------------------------
    "energie.szenarien.eyebrow": "Ihre Wege",
    "energie.szenarien.title": "Drei Wege, ein Zuhause",
    "energie.szenarien.subtitle": "Wählen Sie einen Weg – ich rechne ihn für Sie durch.",
    "energie.szenarien.picker": "Szenario",
    "energie.szenarien.keine_investition": "keine Investition",
    "energie.szenarien.button": "Diesen Weg durchrechnen",
    "energie.szenarien.table": "Die Wege im direkten Vergleich",
    "energie.szenarien.row.investition": "Investition",
    "energie.szenarien.row.foerderung": "Förderung",
    "energie.szenarien.row.eigenanteil": "Eigenanteil",
    "energie.szenarien.row.energiekosten": "Energiekosten pro Jahr",
    "energie.szenarien.row.co2": "CO₂ pro Jahr",
    "energie.szenarien.row.komfort": "Komfort",
    "energie.szenarien.row.aufwand": "Aufwand für Sie",
    "energie.komfort.1": "gering",
    "energie.komfort.2": "spürbar",
    "energie.komfort.3": "gut",
    "energie.komfort.4": "hoch",
    "energie.komfort.5": "sehr hoch",
    "energie.aufwand.1": "keiner",
    "energie.aufwand.2": "gering",
    "energie.aufwand.3": "mittel",
    "energie.aufwand.4": "hoch",
    "energie.aufwand.5": "sehr hoch",
    # -- Economics -------------------------------------------------------------
    "energie.wirtschaft.eyebrow": "Wirtschaftlichkeit",
    "energie.wirtschaft.title": "„{szenario}“ über 20 Jahre gerechnet",
    "energie.wirtschaft.subtitle": (
        "Investition, Förderung und laufende Kosten zusammen betrachtet."
    ),
    "energie.wirtschaft.chart_title": "Kumulierte Gesamtkosten",
    "energie.wirtschaft.chart_sub": (
        "Wo sich die Linien kreuzen, liegt Ihr Break-even gegenüber „weiter wie bisher“."
    ),
    "energie.wirtschaft.breakeven": "Break-even",
    "energie.wirtschaft.breakeven_label": "bis zum Ausgleich",
    "energie.wirtschaft.breakeven_jahre": "{jahre} Jahre",
    "energie.wirtschaft.breakeven_body": (
        "Nach rund {jahre} Jahren haben Sie die Mehrinvestition wieder drin. "
        "Ab dann sparen Sie jedes Jahr."
    ),
    "energie.wirtschaft.breakeven_nie": (
        "Über 40 Jahre gleicht sich die Mehrinvestition nicht aus. Dieser Weg "
        "lohnt sich für Sie eher über Komfort und CO₂ als über die Kosten."
    ),
    "energie.wirtschaft.laufend": "Laufende Kosten pro Jahr",
    "energie.wirtschaft.laufend_label": "pro Jahr",
    "energie.wirtschaft.laufend_body": (
        "Statt {alt} zahlen Sie {neu} – Energie und Wartung zusammen."
    ),
    "energie.wirtschaft.gesamt": "Über 20 Jahre",
    "energie.wirtschaft.gesamt_label": "Vorteil gesamt",
    "energie.wirtschaft.gesamt_body": (
        "Differenz gegenüber „weiter wie bisher“, inklusive Investition, Förderung "
        "und angenommener Preissteigerung."
    ),
    # -- Funding ---------------------------------------------------------------
    "energie.foerderung.surface": "Förderung & Fahrplan",
    "energie.foerderung.eyebrow": "Förderung & Umsetzung",
    "energie.foerderung.title": "Was der Staat übernimmt – und in welcher Reihenfolge",
    "energie.foerderung.subtitle": (
        "Die Reihenfolge entscheidet: Wer zu früh beauftragt, verliert den Zuschuss."
    ),
    "energie.foerderung.zuschuss": "Erwarteter Zuschuss",
    "energie.foerderung.quote": "{satz} Förderquote",
    "energie.foerderung.zuschuss_body": (
        "Bezogen auf förderfähige Kosten von {kosten}. Ihr Eigenanteil sinkt damit "
        "auf {eigenanteil}."
    ),
    "energie.foerderung.bausteine": "So setzt sich die Quote zusammen",
    "energie.foerderung.deckel": "Deckelung bei {max} (rechnerisch {roh})",
    "energie.foerderung.baustein.grund": "Grundförderung",
    "energie.foerderung.baustein.klima": "Klimageschwindigkeits-Bonus",
    "energie.foerderung.baustein.einkommen": "Einkommens-Bonus",
    "energie.foerderung.baustein.effizienz": "Effizienz-Bonus",
    "energie.foerderung.plan": "Ihr Weg in fünf Schritten",
    "energie.foerderung.assumptions": [
        "Antragstellung vor Vorhabenbeginn ist zwingend.",
        "Boni sind an Nachweise gebunden (z. B. Einkommen, Austausch der Altanlage).",
    ],
    "energie.schritte": [
        "**1. Energieberatung und Angebot**|Fachbetrieb nimmt das Gebäude auf, "
        "prüft Heizlast und Heizflächen und erstellt ein Angebot.|2–4 Wochen",
        "**2. Förderantrag stellen**|Antrag mit Liefer- und Leistungsvertrag "
        "einreichen. **Wichtig:** vor Beginn der Arbeiten, sonst entfällt die "
        "Förderung.|1–2 Wochen",
        "**3. Förderzusage abwarten**|Erst nach der Zusage verbindlich "
        "beauftragen.|2–6 Wochen",
        "**4. Einbau**|Montage der Wärmepumpe, hydraulischer Abgleich und "
        "Einregulierung der Heizkurve.|2–5 Tage",
        "**5. Nachweis und Auszahlung**|Fachunternehmererklärung einreichen, "
        "Zuschuss wird ausgezahlt.|4–8 Wochen",
    ],
    # -- Verdicts and findings the calculation produces, as keys -------------
    "energie.urteil.gut": "gut geeignet",
    "energie.urteil.vorbereitung": "geeignet mit Vorbereitung",
    "energie.urteil.erst_spaeter": "erst nach Vorbereitung sinnvoll",
    "energie.hinweis.hoher_vorlauf": (
        "Die vorhandenen Heizkörper brauchen im Auslegungsfall eine hohe "
        "Vorlauftemperatur. Das drückt die Effizienz spürbar."
    ),
    "energie.hinweis.standard_vorlauf": (
        "Mit Standard-Heizkörpern läuft die Wärmepumpe gut, aber nicht optimal."
    ),
    "energie.hinweis.guter_vorlauf": "Das Wärmeverteilsystem passt sehr gut zu einer Wärmepumpe.",
    "energie.hinweis.hoher_bedarf": (
        "Der spezifische Wärmebedarf ist hoch — die Gebäudehülle ist der größere "
        "Hebel als die Heiztechnik."
    ),
    "energie.massnahme.heizkoerper": "Austausch einzelner Heizkörper gegen Niedertemperatur-Modelle",
    "energie.massnahme.abgleich": "Hydraulischer Abgleich und Heizkurve absenken",
    "energie.massnahme.daemmung": "Dachdämmung oder Fenstertausch vorziehen",
    "energie.massnahme.dachboden": "Dachbodendämmung als günstige Einstiegsmaßnahme prüfen",
    # -- Scenario names and descriptions ---------------------------------------
    "energie.szenario.bestand": "Weiter wie bisher",
    "energie.szenario.bestand.beschreibung": (
        "Die vorhandene Heizung bleibt. Keine Investition, aber steigende "
        "Energiekosten und CO₂-Bepreisung."
    ),
    "energie.szenario.waermepumpe": "Wärmepumpe",
    "energie.szenario.waermepumpe.beschreibung": (
        "Heiztechnik tauschen, Gebäudehülle unverändert lassen. Der schnellste "
        "Weg raus aus dem fossilen Brennstoff."
    ),
    "energie.szenario.waermepumpe_huelle": "Wärmepumpe + Dachdämmung",
    "energie.szenario.waermepumpe_huelle.beschreibung": (
        "Erst den Bedarf senken, dann die Wärmepumpe kleiner auslegen. Höhere "
        "Investition, dafür dauerhaft niedrigste Betriebskosten."
    ),
    "energie.szenario.waermepumpe_pv": "Wärmepumpe + PV & Speicher",
    "energie.szenario.waermepumpe_pv.beschreibung": (
        "Wärme und Strom zusammen denken. Ein Teil des Wärmestroms kommt vom "
        "eigenen Dach, das entkoppelt von Strompreisen."
    ),
    "energie.jahr": "Jahr {jahr}",
    # -- The assumption list under every figure ---------------------------------
    "energie.annahmen.bedarf": "Wärmebedarf {bedarf} kWh/a",
    "energie.annahmen.preise": (
        "Strompreis Wärmepumpe {strom} €/kWh, {traeger}preis {alt} €/kWh{eigene}"
    ),
    "energie.annahmen.eigene": " (Ihre eigenen Annahmen)",
    "energie.annahmen.steigerung": "Preissteigerung Strom {strom} p. a., fossil {fossil} p. a.",
    "energie.annahmen.jaz": "Jahresarbeitszahl {jaz} bei {vorlauf} °C Vorlauf",
    "energie.annahmen.dauer": "Betrachtungsdauer 20 Jahre, Förderung nach BEG-Demo-Logik",
    # -- What-if ----------------------------------------------------------------
    "energie.wenn.surface": "Was wäre wenn",
    "energie.wenn.title": "Rechnen Sie mit Ihren eigenen Preisen",
    "energie.wenn.subtitle": (
        "Niemand kennt die Energiepreise der nächsten zwanzig Jahre – auch ich "
        "nicht. Stellen Sie ein, was Sie für realistisch halten. Die Zahlen unten "
        "rechnen sofort mit."
    ),
    "energie.wenn.annahmen": "Ihre Annahmen",
    "energie.wenn.regler_alt": "{traeger}preis in Cent je kWh",
    "energie.wenn.regler_strom": "Strompreis für die Wärmepumpe in Cent je kWh",
    "energie.wenn.heute": "Heute mit {heizung}",
    "energie.wenn.danach": "Mit {szenario}",
    "energie.wenn.pro_jahr_wartung": "pro Jahr, mit Wartung",
    "energie.wenn.unterschied": "Unterschied",
    "energie.wenn.pro_monat": "pro Monat",
    "energie.wenn.nach_20": "Nach 20 Jahren",
    "energie.wenn.nach_eigenanteil": "nach Ihrem Eigenanteil von {eigenanteil}",
    "energie.wenn.uebernehmen_title": "Sollen wir so weiterrechnen?",
    "energie.wenn.uebernehmen_body": (
        "Bisher rechne ich mit den Demo-Preisen. Übernehmen Sie Ihre Einstellung, "
        "gilt sie für die ganze Beratung – Vergleich, Wirtschaftlichkeit und "
        "Empfehlung."
    ),
    "energie.wenn.uebernehmen_button": "Mit diesen Preisen weiterrechnen",
    "energie.wenn.assumptions": [
        "Wärmebedarf {bedarf} kWh/a",
        "Daraus {alt} kWh {traeger} heute gegenüber {neu} kWh Strom danach",
        "Die Regler verändern nur die beiden Preise – Bedarf, Jahresarbeitszahl "
        "und Investition bleiben, wie berechnet.",
        "Preissteigerungen sind hier bewusst nicht enthalten: Sie stellen den "
        "Preis ein, der über die Laufzeit im Mittel gelten soll.",
    ],
    # ======================================================================
    # Meine Mobilität — E-Mobilitätsberatung
    # ======================================================================
    "mob.lade.wallbox_zuhause": "Wallbox zu Hause",
    "mob.lade.steckdose_zuhause": "Haushaltssteckdose",
    "mob.lade.arbeitsplatz": "Laden beim Arbeitgeber",
    "mob.lade.nur_oeffentlich": "Nur öffentlich",
    "mob.lade.nur_oeffentlich.lang": "Nur öffentlich laden",
    "mob.quelle.zuhause": "Zu Hause",
    "mob.quelle.arbeit": "Beim Arbeitgeber",
    "mob.quelle.ac_oeffentlich": "Öffentlich AC",
    "mob.quelle.dc_schnell": "Schnellladen DC",
    "mob.kraftstoff.benzin": "Benzin",
    "mob.kraftstoff.diesel": "Diesel",
    "mob.ja": "ja",
    "mob.nein": "nein",
    # -- Profile --------------------------------------------------------------
    "mob.profil.eyebrow": "Ihr Alltag",
    "mob.profil.correct_me": "Korrigieren Sie mich jederzeit – ich rechne sofort neu.",
    "mob.profil.taeglich": "Täglich",
    "mob.profil.taeglich_wert": "{km} km an {tage} Tagen",
    "mob.profil.langstrecke": "Langstrecke",
    "mob.profil.langstrecke_wert": "{mal}× im Monat, ~ {km} km",
    "mob.profil.laden": "Laden",
    "mob.profil.jahr": "Im Jahr",
    "mob.profil.wunsch": "Fahrzeugwunsch",
    "mob.profil.budget": "Budget",
    "mob.profil.budget_wert": "bis {budget} im Monat",
    "mob.profil.bedenken": "Ihre Bedenken",
    # -- Everyday practicality --------------------------------------------------
    "mob.alltag.eyebrow": "Alltagstauglichkeit",
    "mob.alltag.title": "Ihre Woche mit einem E-Auto",
    "mob.alltag.subtitle": (
        "Nicht der Katalogwert zählt, sondern die Reichweite an einem kalten "
        "Januarmorgen."
    ),
    "mob.alltag.puffer": "Puffer im Alltag",
    "mob.alltag.puffer_label": "Ihres Tagesbedarfs",
    "mob.alltag.puffer_gut": (
        "Ihre {km} km am Tag sind selbst im Winter kein Thema. Sie laden etwa {laden}."
    ),
    "mob.alltag.puffer_ok": (
        "Ihre Tagesstrecke passt, im Winter bleibt ein solider Puffer. Sie laden "
        "etwa {laden}."
    ),
    "mob.alltag.puffer_knapp": (
        "Im Winter wird es knapp – Sie müssten nahezu täglich laden. Eine größere "
        "Batterie oder eine verlässliche Lademöglichkeit ist hier wichtig."
    ),
    "mob.alltag.laden_woche": "einmal pro Woche",
    "mob.alltag.laden_tage": "alle {tage} Tage",
    "mob.alltag.laden_zwei": "alle zwei Tage",
    "mob.alltag.winter": "Reichweite im Winter",
    "mob.alltag.winter_label": "{fahrzeug}, {batterie} kWh",
    "mob.alltag.winter_body": (
        "Bei Kälte steigt der Verbrauch auf {verbrauch} kWh/100 km. Im Sommer sind "
        "es {sommer} km."
    ),
    "mob.alltag.autobahn": "Autobahn im Winter",
    "mob.alltag.autobahn_label": "{verbrauch} kWh/100 km",
    "mob.alltag.autobahn_body": (
        "Der ehrlichste Wert: kalt, bei Richtgeschwindigkeit. Danach planen sich "
        "Langstrecken zuverlässig."
    ),
    "mob.alltag.chart_title": "Ihre typische Woche",
    "mob.alltag.chart_sub": (
        "Die Linie ist die Winterreichweite. Solange die Balken darunter bleiben, "
        "kommen Sie ohne Zwischenladen aus."
    ),
    "mob.alltag.serie_bedarf": "Fahrbedarf",
    "mob.alltag.serie_reichweite": "Reichweite im Winter",
    "mob.tage": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
    "mob.ls.eyebrow": "Langstrecke",
    "mob.ls.title": "Ihre {km}-km-Fahrt konkret",
    "mob.ls.subtitle": (
        "{stopps} Ladestopp(s), zusammen {minuten} Minuten mehr als mit einem Verbrenner."
    ),
    "mob.ls.ohne_stopp": "Ohne Ladestopp erreichbar.",
    "mob.ls.start": "Start mit 100 %",
    "mob.ls.start_detail": (
        "Vollgeladen zu Hause losgefahren – {km} km Autobahnreichweite im Winter."
    ),
    "mob.ls.stopp": "Ladestopp {nr}",
    "mob.ls.stopp_detail": (
        "{kwh} kWh in {minuten} Minuten bei rund {kw} kW – Zeit für Kaffee und Pause."
    ),
    "mob.ls.ankunft": "Ankunft",
    "mob.ls.ankunft_detail": "{km} km gesamt, reine Fahrzeit rund {stunden} h {minuten} min.",
    "mob.ls.ankunft_dauer": "{stunden} h {minuten} min gesamt",
    "mob.ls.min": "{minuten} min",
    # -- Charging ---------------------------------------------------------------
    "mob.laden.surface": "Ladelösungen",
    "mob.laden.eyebrow": "Laden",
    "mob.laden.title": "Wo Sie laden, entscheidet über die Kosten",
    "mob.laden.subtitle": (
        "Zwischen der günstigsten und der teuersten Ladeart liegt bei Ihrer "
        "Fahrleistung ein Vielfaches der Fahrzeugunterschiede."
    ),
    "mob.laden.hebel": "Ihr größter Hebel",
    "mob.laden.hebel_label": "Ersparnis pro Jahr",
    "mob.laden.hebel_body": (
        "Der Wechsel von „{aktuell}“ zu „{beste}“ spart Ihnen rund {betrag} im Jahr "
        "– mehr als die meisten Fahrzeugentscheidungen ausmachen."
    ),
    "mob.laden.hebel_schon_gut": (
        "Ihre Ladesituation ist bereits gut. Die Fahrzeugwahl ist bei Ihnen der "
        "größere Hebel."
    ),
    "mob.laden.table": "Ladeoptionen im Vergleich",
    "mob.laden.row.mischpreis": "Mischpreis",
    "mob.laden.row.kosten_a": "Energiekosten pro Jahr",
    "mob.laden.row.kosten_100": "Kosten je 100 km",
    "mob.laden.row.invest": "Einmalige Investition",
    "mob.laden.row.verfuegbar": "Für Sie verfügbar",
    "mob.laden.bedarf": "Jahresenergiebedarf rund {kwh} kWh",
    # -- Vehicles ----------------------------------------------------------------
    "mob.fahrzeuge.surface": "Fahrzeugvorschläge",
    "mob.fahrzeuge.eyebrow": "Fahrzeugwahl",
    "mob.fahrzeuge.title": "Diese Klassen passen zu Ihrem Alltag",
    "mob.fahrzeuge.subtitle": (
        "Sortiert nach Passung zu Ihrem Profil, nicht nach Reichweite oder Preis allein."
    ),
    "mob.fahrzeuge.passung": "Passung {score}/100",
    "mob.fahrzeuge.kennzahlen": (
        "{batterie} kWh · {winter} km im Winter · {stopps} Ladestopp(s) · ab {rate}/Monat"
    ),
    "mob.fahrzeuge.pro": "**Dafür spricht**",
    "mob.fahrzeuge.contra": "**Zu bedenken**",
    "mob.fahrzeuge.assumptions": [
        "Passung berücksichtigt Winterreichweite, Ladestopps, Budget und Ihre Fahrzeugklasse.",
        "Generische Fahrzeugklassen statt konkreter Modelle – bewusst herstellerneutral.",
    ],
    "mob.pro.reichweite_gut": "{km} km Winterreichweite – {faktor}× Ihr täglicher Bedarf",
    "mob.pro.reichweite_ok": "{km} km im Winter reichen für Ihre Pendelstrecke",
    "mob.contra.taeglich_laden": "Im Winter müssten Sie fast täglich laden",
    "mob.pro.langstrecke": "Ihre {km}-km-Strecke mit {stopps} Ladestopp",
    "mob.contra.langstrecke": "{stopps} Ladestopps auf der Langstrecke",
    "mob.pro.budget": "Liegt mit {rate}/Monat in Ihrem Budget",
    "mob.contra.budget": "{rate}/Monat liegen über Ihrem Budget von {budget}",
    "mob.pro.guenstiger": (
        "Über {jahre} Jahre rund {betrag} günstiger als ein vergleichbarer Verbrenner"
    ),
    "mob.contra.teurer": "Teurer als ein vergleichbarer Verbrenner",
    "mob.pro.klasse": "Entspricht Ihrer gewünschten Fahrzeugklasse",
    "mob.contra.keine": "Keine relevanten Einschränkungen für Ihr Profil",
    # -- Cost --------------------------------------------------------------------
    "mob.kosten.surface": "Kostenvergleich",
    "mob.kosten.eyebrow": "Kosten",
    "mob.kosten.title": "Über {jahre} Jahre gerechnet",
    "mob.kosten.subtitle": (
        "Alle Posten einzeln – Wertverlust, Energie, Wartung, Versicherung, Steuer "
        "und THG-Quote."
    ),
    "mob.kosten.vergleich": "Elektro gegen Verbrenner",
    "mob.kosten.vorteil": "Vorteil Elektro",
    "mob.kosten.nachteil": "Nachteil Elektro",
    "mob.kosten.guenstiger_body": (
        "Das E-Auto ist bei Ihrem Profil insgesamt günstiger – das entspricht "
        "{monat} im Monat."
    ),
    "mob.kosten.teurer_body": (
        "Mit Ihrer heutigen Ladesituation ist das E-Auto insgesamt teurer – rund "
        "{monat} im Monat. Mit einer eigenen Lademöglichkeit dreht sich das Bild."
    ),
    "mob.kosten.energie": "Energie je 100 km",
    "mob.kosten.energie_label": "elektrisch, je 100 km",
    "mob.kosten.energie_body": "Strom {strom} gegenüber Kraftstoff {sprit}.",
    "mob.kosten.co2": "CO₂ pro Jahr",
    "mob.kosten.co2_label": "gegenüber Verbrenner",
    "mob.kosten.co2_body": (
        "Gerechnet mit dem deutschen Strommix. Mit eigener PV-Anlage oder "
        "Ökostromtarif fällt die Bilanz besser aus."
    ),
    "mob.kosten.chart_title": "Kostenposten im Vergleich",
    "mob.kosten.chart_sub": "Gesamtkosten über {jahre} Jahre bei {km} km im Jahr.",
    "mob.kosten.serie_elektro": "Elektro",
    "mob.kosten.serie_verbrenner": "Verbrenner",
    "mob.kosten.posten.wertverlust": "Wertverlust",
    "mob.kosten.posten.energie": "Energie",
    "mob.kosten.posten.wartung": "Wartung",
    "mob.kosten.posten.versicherung": "Versicherung",
    "mob.kosten.posten.steuer": "Kfz-Steuer",
    "mob.kosten.posten.wallbox": "Wallbox",
    "mob.kosten.posten.thg": "THG-Quote",
    "mob.kosten.assumptions": [
        "Gesamtkosten Elektro {elektro}, Verbrenner {verbrenner}",
        "Wertverlust auf Basis angenommener Restwerte nach vier Jahren.",
    ],
    # -- What-if ------------------------------------------------------------------
    "mob.wenn.surface": "Was wäre wenn",
    "mob.wenn.title": "Ihre Strecke, Ihr Ladeort",
    "mob.wenn.subtitle": (
        "Zwei Zahlen entscheiden über die Kosten, und bei beiden haben wir bisher "
        "geschätzt. Stellen Sie ein, was wirklich zu Ihnen passt – die Rechnung "
        "unten folgt sofort."
    ),
    "mob.wenn.einstellung": "Ihre Einstellung",
    "mob.wenn.regler_km": "Kilometer an einem typischen Tag",
    "mob.wenn.regler_zuhause": "Anteil, den Sie zu Hause laden, in Prozent",
    "mob.wenn.preise": (
        "Zu Hause rechne ich mit {zuhause} €/kWh, unterwegs mit {unterwegs} €/kWh "
        "im Mix aus AC und Schnellladen."
    ),
    "mob.wenn.km_jahr": "Kilometer im Jahr",
    "mob.wenn.km_jahr_hint": "mit Langstrecken und Freizeit",
    "mob.wenn.strom": "Strom",
    "mob.wenn.pro_jahr": "pro Jahr",
    "mob.wenn.kraftstoff": "{kraftstoff} zum Vergleich",
    "mob.wenn.kraftstoff_hint": "pro Jahr, gleiche Strecke",
    "mob.wenn.unterschied": "Unterschied",
    "mob.wenn.unterschied_hint": "pro Monat, nur Energie",
    "mob.wenn.uebernehmen_title": "Sollen wir so weiterrechnen?",
    "mob.wenn.uebernehmen_body": (
        "Übernehmen Sie Ihre Einstellung, gilt sie für die ganze Beratung – "
        "Reichweite, Ladeoptionen und Gesamtkosten."
    ),
    "mob.wenn.uebernehmen_button": "Mit diesen Werten weiterrechnen",
    "mob.wenn.assumptions": [
        "{fahrzeug}, {verbrauch} kWh/100 km im Realbetrieb",
        "Verbrenner-Vergleich mit {liter} l/100 km {kraftstoff}",
        "Neben der Tagesstrecke rechne ich fest mit {km} km im Jahr für Langstrecken "
        "und Freizeit.",
        "Die Regler verändern nur Strecke und Ladeort – Verbrauch, Preise und "
        "Fahrzeugklasse bleiben, wie berechnet.",
        "Nur Energiekosten. Wertverlust, Wartung, Versicherung und Steuer stehen im "
        "Kostenvergleich.",
    ],
    # -- The assumption list ---------------------------------------------------------
    "mob.annahmen.km": "Jahresfahrleistung {km} km",
    "mob.annahmen.preis": "Mischladepreis {preis} €/kWh ({herkunft})",
    "mob.annahmen.herkunft_eigen": "{anteil} zu Hause, von Ihnen gesetzt",
    "mob.annahmen.herkunft_mix": "Mix für „{lademoeglichkeit}“",
    "mob.annahmen.mehrverbrauch": (
        "Winter-Mehrverbrauch {winter}, Autobahn-Mehrverbrauch {autobahn}"
    ),
    "mob.annahmen.ladefenster": "Ladefenster 10–80 % SoC, Haltedauer {jahre} Jahre",
    "mob.annahmen.kraftstoff": "Kraftstoff Benzin {benzin} €/l, Diesel {diesel} €/l",
    # -- What the agent is told is on the screen (`readback`) ------------------
    "readback.surface": "„{titel}“:",
    "readback.empty": "„{titel}“ — Text ohne Kennzahlen.",
    "readback.truncated": "  … (gekürzt)",
    "readback.chart.line": "Liniendiagramm",
    "readback.chart.bar": "Balkendiagramm",
    "readback.chart.groupedBar": "gruppiertes Balkendiagramm",
    "readback.chart.stackedBar": "gestapeltes Balkendiagramm",
    "readback.chart.other": "Diagramm",
    "readback.chart.axis": "{kind}; Achse: {kategorien}.",
    "readback.chart.named": "{kind} „{titel}“",
    "readback.series.flat": "{wert}, durchgehend",
    "readback.series.line": "{start} → {ende}",
    "readback.series.line_peak": "{start} → {ende}, Höchstwert {peak}{wo}",
    "readback.series.bars": "{min} bis {peak}, am höchsten{wo}",
    "readback.crossing": (
        "die Linien kreuzen sich zwischen „{vorher}“ und „{nachher}“; danach liegt "
        "„{fuehrend}“ günstiger"
    ),
    "readback.table": "Vergleichstabelle{titel}; Spalten: {spalten}.",
    "readback.table.named": " „{titel}“",
    "readback.table.highlight": "  · hervorgehoben ist die Spalte „{spalte}“",
    "readback.stat": "Kennzahl „{titel}“: {metric}{label} [{tone}]",
    "readback.stat.plain": "Kennzahlkarte „{titel}“",
    "readback.stat.live": "Kennzahl „{titel}“: rechnet live mit den Reglern mit",
    "readback.slider": "Regler „{label}“{bereich}{stand} — die Person kann ihn selbst bewegen",
    "readback.slider.range": ", Bereich {min}–{max}",
    "readback.slider.value": " steht bei {wert}",
    "readback.picker": "Auswahl „{label}“: {optionen}",
    "readback.picker.plain": "Auswahl: {optionen}",
    "readback.picker.chosen": " (gewählt: {wert})",
    "readback.tone.positive": "spricht dafür",
    "readback.tone.caution": "Nachteil",
    "readback.tone.neutral": "neutral",
    # ======================================================================
    # Prompts — the agent's own words about how to behave
    # ======================================================================
    "prompt.haltung": """
## Deine Haltung

Du bist ein persönlicher Berater, kein Chatbot und kein Verkäufer. Du sprichst
Deutsch, natürlich und in ganzen Sätzen, wie ein erfahrener Mensch am Telefon.

- **Zuhören vor Fragen.** Lass die Person erzählen. Stelle immer nur EINE Frage
  auf einmal, und nur wenn die Antwort die Beratung wirklich verändert.
- **Alltagssprache.** Keine Fachbegriffe ohne Erklärung, kein Produktjargon,
  keine Abkürzungen, die man nachschlagen muss.
- **Empathie ohne Druck.** Wenn jemand eine Sorge äußert, nimm sie ernst und
  benenne sie, bevor du sie einordnest. Verkaufe nichts. Dränge zu nichts.
- **Kurz sprechen.** Zwei bis vier Sätze pro Redebeitrag. Die Details stehen
  auf dem Bildschirm, du erklärst sie, du liest sie nicht vor.
- **Ehrlich bleiben.** Wenn etwas nicht passt, sag es. Ein „das lohnt sich für
  Sie so nicht" schafft mehr Vertrauen als eine schöngerechnete Empfehlung.

## Wie du den Bildschirm nutzt

Du baust die Oberfläche über deine Werkzeuge auf, während ihr sprecht. Das ist
kein Nachtrag zum Gespräch, sondern Teil davon.

- Rufe ein Werkzeug auf, sobald du genug verstanden hast — nicht erst am Ende.
- **Nie Zahlen erfinden.** Alle Zahlen kommen aus den Werkzeugen zurück. Sprich
  nur über Werte, die dir ein Werkzeug geliefert hat.
- Nach einem Werkzeugaufruf sagst du in ein bis zwei Sätzen, was jetzt zu sehen
  ist und was es für die Person bedeutet. Zähle nicht alle Zahlen auf.
- Aktualisiere `profil_aktualisieren`, sobald du etwas Neues verstanden hast.
  Die Person soll auf dem Schirm sehen, dass du sie richtig verstanden hast.
- Wenn eine Sorge im Raum steht, beantworte sie mit `bedenken_adressieren`,
  bevor du weiterrechnest.

## Was gerade auf dem Bildschirm steht

Jedes Werkzeug gibt dir `auf_dem_schirm` zurück: was die Person in diesem
Moment vor sich sieht, von oben nach unten — mit den Achsen der Diagramme, dem
Verlauf jeder Linie und der Stelle, an der sich zwei Linien kreuzen.

- Fragt jemand „was ist die obere Linie?" oder „warum knickt das da?", steht
  die Antwort dort. Rate nicht.
- Es ist eine Notiz für dich, keine Sprechvorlage. Lies sie nicht vor.
- Zeig mit Worten hin — „die obere Linie", „die letzte Zeile". Die Reihenfolge
  stimmt mit dem Bildschirm überein.
- `[Nachteil]` heißt: die Zahl spricht **gegen** die Person. Nicht schönreden.
- „rechnet live mit den Reglern mit" heißt: diese Karte hat gerade keinen
  festen Wert. Nenne keinen, lade zum Ziehen ein.

## Wie du führst

Die Person weiß nicht, was sie sagen darf. Führen heißt: nach jedem Schritt
weiß sie, was als Nächstes kommt.

- **Gib den Ball konkret zurück.** Nicht „Haben Sie noch Fragen?", sondern
  „Wenn Sie wollen, rechne ich als Nächstes durch, ab wann sich das lohnt."
- **Ein Schritt, dann Pause.** Nie zwei Ansichten hintereinander ohne ein Wort
  dazwischen.
- **Regler gehören der Person.** Steht einer auf dem Schirm, sag einmal, dass
  sie selbst ziehen kann und alles sofort mitrechnet.
- **Sag, wo ihr steht**, wenn ein Abschnitt endet: „Technisch passt es —
  bleibt die Frage, ob es sich rechnet."
- **Bei Schweigen** wiederhol dich nicht, biete den nächsten Schritt an.
- **Bei „weiß ich nicht"** rechne mit einem klaren Näherungswert weiter, sag
  welchen, und zeig die Regler. Niemand kennt seinen Verbrauch auswendig.

## Grenzen

- Du gibst eine Orientierung, kein verbindliches Angebot. Sag das, wenn es
  relevant wird — nicht in jedem Satz.
- Alle Werte sind gekennzeichnete Demo-Beispieldaten.
- Frage nicht nach Namen, Adresse, Vertragsnummern oder anderen persönlichen
  Daten. Für die Beratung brauchst du sie nicht.
""".strip(),
    "prompt.opening": (
        "Begrüße die Person kurz und warm auf Deutsch. Sag ihr dann in einem "
        "Satz, wobei du helfen kannst: {themen}. Stelle danach genau eine "
        "offene Frage {frage}. Insgesamt höchstens drei Sätze."
    ),
    "prompt.join": "{vorher} und {letzter}",
    "prompt.interaction": (
        "[Interaktion auf dem Bildschirm] Die Person hat \u201e{name}\u201c "
        "ausgelöst{werte}. "
        "Reagiere kurz und passend darauf. Wenn ein Werkzeug genau diese Werte "
        "entgegennimmt, rufe es mit ihnen auf – unverändert."
    ),
    "prompt.interaction.values": " mit diesen Werten: {werte}.",
    "status.connected": "verbunden",
    "status.ended": "beendet",
    "error.connection": (
        "Die Verbindung zum Sprachdienst ist abgebrochen. Bitte laden Sie die "
        "Seite neu."
    ),
    # -- The two journeys, as the client meets them ---------------------------
    "journey.energie.label": "Mein Zuhause",
    "journey.energie.tagline": (
        "Von komplexen Sanierungsfragen zur verständlichen persönlichen Energiewende."
    ),
    "journey.energie.topics": [
        "ob eine Wärmepumpe zu Ihrem Haus passt",
        "was der Umstieg kostet und ab wann er sich lohnt",
        "welche Förderung Sie bekommen",
    ],
    "journey.energie.frage": "zum Zuhause der Person",
    "journey.energie.steps": [
        "profil|Ihre Situation",
        "eignung|Eignung",
        "szenarien|Wege",
        "wirtschaftlichkeit|Wirtschaftlichkeit",
        "foerderung|Förderung",
        "naechster_schritt|Nächster Schritt",
    ],
    "journey.energie.instruction": """
Du bist der persönliche Energieberater einer deutschen Energie-Experience.
Du hilfst Menschen, die über Heizung, Sanierung und ihren Weg zur Energiewende
nachdenken — und dabei oft überfordert sind.

Die typische Person hat ein älteres Einfamilienhaus, eine Gasheizung, die in die
Jahre kommt, und zwei Sorgen: „Reicht eine Wärmepumpe im Winter?" und „Lohnt
sich das für mich überhaupt?" Deine Aufgabe ist es, aus dieser Unsicherheit ein
verständliches Zukunftsbild zu machen.

{haltung}

## Dein Gesprächsbogen

1. **Zuhören.** Lass die Person ihre Situation schildern. Baujahr, Heizung,
   Fläche und die eigentliche Sorge ergeben sich meist von selbst.
2. **Verstehen zeigen.** Sobald du Gebäude und Heizung kennst, rufe
   `profil_aktualisieren` auf. Fehlendes schätzt du plausibel und markierst es
   als offenen Punkt — frag nicht alles ab.
3. **Die Kernsorge zuerst.** Mit `waermepumpen_eignung_zeigen` beantwortest du,
   ob das Haus geeignet ist. Das ist fast immer die eigentliche Frage.
4. **Wege zeigen.** `szenarien_vergleichen` stellt die Optionen nebeneinander.
5. **Rechnen.** `wirtschaftlichkeit_zeigen` für den gewählten Weg.
6. **Nachvollziehbar machen.** `stellschrauben_zeigen` gibt die zwei
   Preisannahmen an die Person ab. Nutze das, sobald jemand zweifelt — und
   sag dazu, dass sie selbst ziehen darf.
7. **Förderung und Reihenfolge.** `foerderung_und_fahrplan_zeigen`.
8. **Abschluss.** `naechsten_schritt_anbieten` fasst zusammen und übergibt.

Du musst diese Reihenfolge nicht erzwingen. Wenn jemand direkt nach Kosten
fragt, geh dorthin. Aber lass keinen Schritt weg, den die Person braucht.

## Fachliches

- Entscheidend für die Eignung ist die **nötige Vorlauftemperatur**, nicht die
  Außentemperatur. Das ist der wichtigste Satz dieser Beratung.
- Frag nach der Art der Heizkörper (groß und flach, oder alt und schmal?) oder
  ob eine Fußbodenheizung vorhanden ist — daraus folgt die Vorlauftemperatur.
- Bei hohem spezifischen Wärmebedarf ist die Gebäudehülle der größere Hebel als
  die Heiztechnik. Sag das offen, auch wenn es die teurere Antwort ist.
- Die Förderung setzt voraus, dass der Antrag **vor** der Beauftragung gestellt
  wird. Dieser Hinweis gehört in jede Beratung.

## Wenn die Person am Bildschirm etwas einstellt

Löst sie „Mit diesen Preisen weiterrechnen" aus, bekommst du die eingestellten
Werte als Interaktion gemeldet. Rufe dann `annahmen_uebernehmen` mit genau
diesen Werten auf — nicht mit eigenen. Danach gilt ihre Annahme, nicht meine.
Nennt sie im Gespräch selbst einen Preis („bei uns kostet Gas eher 20 Cent"),
gilt dasselbe.

## Eröffnung

Sag als Erstes, wobei du helfen kannst: {themen}. Ohne diesen Satz weiß eine
Person, die zum ersten Mal hier ist, gar nicht, was sie sagen darf — und das
ist der häufigste Grund, warum ein Sprachgespräch stockt.

Stelle danach genau **eine** offene Frage zu ihrem Zuhause. Frage nicht nach
Daten, sondern nach ihrer Situation. Zusammen höchstens drei Sätze.
""".strip(),
    "journey.mobilitaet.label": "Meine Mobilität",
    "journey.mobilitaet.tagline": (
        "Von Reichweitenangst und Tarifdschungel zur passenden E-Mobilitätsentscheidung."
    ),
    "journey.mobilitaet.topics": [
        "ob ein E-Auto zu Ihren Wegen passt",
        "wo Sie laden würden und was das kostet",
        "welches Fahrzeug zu Ihnen passt",
    ],
    "journey.mobilitaet.frage": "zum Alltag und den typischen Wegen der Person",
    "journey.mobilitaet.steps": [
        "profil|Ihr Alltag",
        "alltag|Reichweite",
        "laden|Laden",
        "fahrzeuge|Fahrzeuge",
        "kosten|Kosten",
        "naechster_schritt|Nächster Schritt",
    ],
    "journey.mobilitaet.instruction": """
Du bist der persönliche Mobilitätsberater einer deutschen E-Mobilitäts-
Experience. Du hilfst Menschen, die mit einem Elektroauto liebäugeln, aber
unsicher sind, ob es zu ihrem Alltag passt.

Die typische Person pendelt täglich, fährt am Wochenende gelegentlich lange
Strecken und hat keine eigene Wallbox. Ihre Fragen sind: „Reicht die
Reichweite?", „Wo lade ich?" und „Rechnet sich das überhaupt?"

Dein Leitsatz: Die Person soll kein Elektroauto verstehen müssen. Du verstehst
ihren Alltag und zeigst, wie E-Mobilität konkret für sie funktioniert — oder
eben nicht.

{haltung}

## Dein Gesprächsbogen

1. **Zuhören.** Lass die Person ihren Alltag beschreiben. Pendelstrecke,
   Langstrecken und Lademöglichkeit ergeben sich meist von selbst.
2. **Verstehen zeigen.** Sobald du die Fahrstrecken und die Ladesituation
   kennst, rufe `profil_aktualisieren` auf.
3. **Alltag zuerst.** `alltagstauglichkeit_zeigen` beantwortet die
   Reichweitenfrage mit der eigenen Woche der Person und ihrer konkreten
   Langstrecke. Das ist der Moment, in dem Reichweitenangst kippt.
4. **Laden vor Auto.** `ladeloesungen_vergleichen` — wo geladen wird,
   entscheidet stärker über die Kosten als das Modell. Diese Reihenfolge ist
   wichtig, dreh sie nicht um.
5. **Fahrzeuge.** `fahrzeuge_vorschlagen` zeigt passende Klassen mit offenen
   Trade-offs.
6. **Kosten.** `kosten_vergleichen` stellt Elektro und Verbrenner gegenüber.
7. **Nachvollziehbar machen.** `stellschrauben_zeigen` gibt Tagesstrecke und
   Ladequote an die Person ab. Nutze das, sobald sie bei einer der beiden
   Zahlen unsicher ist — und sag dazu, dass sie selbst ziehen darf.
8. **Abschluss.** `naechsten_schritt_anbieten`.

## Fachliches

- Nenne **realistische Reichweiten**, nie Katalogwerte. Der ehrlichste Wert ist
  Autobahn im Winter — er nimmt der Reichweitenangst die Grundlage, weil er
  überprüfbar ist.
- Ohne eigene Lademöglichkeit rechnet sich ein E-Auto oft **nicht**. Wenn die
  Rechnung das zeigt, sag es klar und zeig, was sich ändern müsste. Genau das
  macht die Beratung glaubwürdig.
- Auf der Langstrecke wird zwischen etwa 10 und 80 Prozent geladen, danach lädt
  jedes Auto spürbar langsamer. Deshalb sind Ladestopps kürzer, als die meisten
  erwarten.
- Sprich über Ladestopps als Pausen, nicht als Wartezeit — aber nur, wenn es
  ehrlich bleibt.

## Wenn die Person am Bildschirm etwas einstellt

Löst sie „Mit diesen Werten weiterrechnen" aus, bekommst du die eingestellten
Werte als Interaktion gemeldet. Rufe dann `annahmen_uebernehmen` mit genau
diesen Werten auf — nicht mit eigenen. Nennt sie im Gespräch selbst eine
Strecke oder eine Ladequote, gilt dasselbe.

## Eröffnung

Sag als Erstes, wobei du helfen kannst: {themen}. Ohne diesen Satz weiß eine
Person, die zum ersten Mal hier ist, gar nicht, was sie sagen darf — und das
ist der häufigste Grund, warum ein Sprachgespräch stockt.

Stelle danach genau **eine** offene Frage zu ihrem Alltag. Frag nicht nach
einem Fahrzeugwunsch, sondern nach ihren Wegen. Zusammen höchstens drei Sätze.
""".strip(),
    # -- A concern, answered on its own surface -------------------------------
    "bedenken.eyebrow": "Ihre Frage",
}
