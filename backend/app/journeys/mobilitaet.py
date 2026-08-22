"""Journey 02 — Der persönliche Autoberater."""

from __future__ import annotations

from typing import Any, Literal

from google.adk.tools import ToolContext

from ..a2ui import composer_mobilitaet as compose
from ..a2ui import composer_shared as shared
from ..config import get_settings
from ..domain import mobilitaet as calc
from .base import HALTUNG, Journey, apply, load_profile, open_points, push, save_profile

Laden = Literal["wallbox_zuhause", "steckdose_zuhause", "arbeitsplatz", "nur_oeffentlich"]
Klasse = Literal["kompakt", "mittelklasse", "suv", "van"]


def _profil(tool_context: ToolContext) -> calc.Mobilitaetsprofil:
    return load_profile(tool_context, calc.Mobilitaetsprofil)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def profil_aktualisieren(
    tool_context: ToolContext,
    taeglich_km: float | None = None,
    pendeltage_pro_woche: int | None = None,
    langstrecken_pro_monat: int | None = None,
    langstrecke_km: float | None = None,
    lademoeglichkeit: Laden | None = None,
    stellplatz_vorhanden: bool | None = None,
    fahrzeugklasse: Klasse | None = None,
    haltedauer_jahre: int | None = None,
    budget_eur_monat: float | None = None,
    aktueller_verbrauch_l_100km: float | None = None,
    bedenken: list[str] | None = None,
    prioritaeten: list[str] | None = None,
    offene_punkte: list[str] | None = None,
) -> dict[str, Any]:
    """Zeigt auf dem Bildschirm, was du über den Alltag verstanden hast.

    Rufe das früh auf und danach jedes Mal, wenn du etwas Neues erfährst oder
    korrigiert wirst.

    Args:
        taeglich_km: Typische Tagesstrecke in Kilometern.
        pendeltage_pro_woche: An wie vielen Tagen pro Woche diese Strecke anfällt.
        langstrecken_pro_monat: Wie oft im Monat längere Fahrten anstehen.
        langstrecke_km: Die typische Langstrecke einfach, in Kilometern. Frag
            nach einer konkreten Strecke, die die Person wirklich fährt.
        lademoeglichkeit: Wo die Person heute laden könnte.
        stellplatz_vorhanden: Ob ein eigener Stellplatz oder eine Garage da ist.
            Entscheidet, ob eine Wallbox überhaupt möglich wäre.
        fahrzeugklasse: Welche Fahrzeuggröße zur Person passt.
        haltedauer_jahre: Wie lange das Fahrzeug gefahren werden soll.
        budget_eur_monat: Monatsbudget in Euro, falls genannt.
        aktueller_verbrauch_l_100km: Verbrauch des heutigen Fahrzeugs.
        bedenken: Geäußerte Sorgen, in den Worten der Person.
        prioritaeten: Was der Person wichtig ist, in ihren Worten.
        offene_punkte: Was du noch nicht weißt und geschätzt hast.
    """
    profil = apply(
        _profil(tool_context),
        taeglich_km=taeglich_km,
        pendeltage_pro_woche=pendeltage_pro_woche,
        langstrecken_pro_monat=langstrecken_pro_monat,
        langstrecke_km=langstrecke_km,
        lademoeglichkeit=lademoeglichkeit,
        stellplatz_vorhanden=stellplatz_vorhanden,
        fahrzeugklasse=fahrzeugklasse,
        haltedauer_jahre=haltedauer_jahre,
        budget_eur_monat=budget_eur_monat,
        aktueller_verbrauch_l_100km=aktueller_verbrauch_l_100km,
        bedenken=bedenken,
        prioritaeten=prioritaeten,
    )
    save_profile(tool_context, profil)
    offen = open_points(tool_context, offene_punkte)

    push(tool_context, compose.profil_surface(profil, offen))
    return {
        "jahres_km": profil.jahresfahrleistung_km(),
        "hinweis": "Bestätige kurz, was du verstanden hast, ohne alle Werte vorzulesen.",
    }


def alltagstauglichkeit_zeigen(tool_context: ToolContext) -> dict[str, Any]:
    """Zeigt die typische Woche gegen die reale Winterreichweite.

    Dazu die konkrete Langstrecke als Ablauf mit Ladestopps und Zeitaufwand.
    Das ist die Antwort auf Reichweitenangst. Rufe das auf, sobald du
    Tagesstrecke und Langstrecke kennst.
    """
    profil = _profil(tool_context)
    r = calc.reichweite(profil)
    ls = calc.langstrecke(profil)

    push(tool_context, compose.alltag_surface(profil))
    return {
        "reichweite_winter_km": r["reichweite_winter_km"],
        "reichweite_autobahn_winter_km": r["reichweite_autobahn_winter_km"],
        "puffer_faktor_winter": r["puffer_faktor_winter"],
        "taeglich_laden_noetig": r["taeglich_laden_noetig"],
        "ladestopps_langstrecke": ls["ladestopps"],
        "mehrzeit_min": ls["mehrzeit_min"],
    }


def ladeloesungen_vergleichen(tool_context: ToolContext) -> dict[str, Any]:
    """Vergleicht Wallbox, Laden beim Arbeitgeber und öffentliches Laden.

    Mischpreis je kWh, Kosten pro Jahr und je 100 km, und welcher Hebel am
    größten ist. Rufe das vor der Fahrzeugwahl auf — der Ladeort entscheidet
    stärker über die Kosten als das Modell.
    """
    profil = _profil(tool_context)
    lade = calc.ladeoptionen(profil)

    push(tool_context, compose.laden_surface(profil))
    return {
        "aktuell": lade["aktuell_id"],
        "beste_option": lade["beste_id"],
        "ersparnis_eur_a": lade["ersparnis_beste_eur_a"],
        "optionen": [
            {
                "id": o["id"],
                "label": o["label"],
                "kosten_eur_a": o["kosten_eur_a"],
                "kosten_eur_100km": o["kosten_eur_100km"],
                "verfuegbar": o["verfuegbar"],
            }
            for o in lade["optionen"]
        ],
    }


def fahrzeuge_vorschlagen(tool_context: ToolContext) -> dict[str, Any]:
    """Schlägt passende Fahrzeugklassen vor, sortiert nach Passung.

    Mit Winterreichweite, Ladestopps auf der Langstrecke, Monatsrate und offen
    benannten Vor- und Nachteilen.
    """
    profil = _profil(tool_context)
    vorschlaege = calc.fahrzeugvorschlaege(profil)

    push(tool_context, compose.fahrzeuge_surface(profil))
    return {
        "vorschlaege": [
            {
                "label": v["label"],
                "score": v["score"],
                "reichweite_winter_km": v["reichweite_winter_km"],
                "ladestopps_langstrecke": v["ladestopps_langstrecke"],
                "leasing_eur_monat": v["leasing_eur_monat"],
                "contra": v["contra"],
            }
            for v in vorschlaege
        ]
    }


def kosten_vergleichen(tool_context: ToolContext) -> dict[str, Any]:
    """Stellt die Gesamtkosten von Elektro und Verbrenner gegenüber.

    Aufgeschlüsselt nach Wertverlust, Energie, Wartung, Versicherung, Steuer
    und THG-Quote. Nutze das für die Frage, ob es sich rechnet.
    """
    profil = _profil(tool_context)
    k = calc.kostenvergleich(profil)

    push(tool_context, compose.kosten_surface(profil))
    return {
        "gesamt_elektro_eur": k["gesamt_elektro_eur"],
        "gesamt_verbrenner_eur": k["gesamt_verbrenner_eur"],
        "differenz_eur": k["differenz_eur"],
        "differenz_eur_monat": k["differenz_eur_monat"],
        "elektro_guenstiger": k["differenz_eur"] > 0,
        "energie_elektro_eur_100km": k["energie_elektro_eur_100km"],
        "energie_verbrenner_eur_100km": k["energie_verbrenner_eur_100km"],
        "hinweis": (
            "Wenn das E-Auto teurer ist, benenne das offen und zeig über die "
            "Ladeoptionen, was sich ändern müsste."
        ),
    }


def bedenken_adressieren(
    tool_context: ToolContext,
    titel: str,
    einordnung: str,
    punkte: list[dict[str, str]],
) -> dict[str, Any]:
    """Beantwortet eine konkrete Sorge mit einer eigenen Ansicht.

    Nutze das, sobald jemand eine Unsicherheit äußert. Formuliere die Sorge in
    der Sprache der Person, nicht in Fachsprache.

    Args:
        titel: Die Sorge als Frage, so wie die Person sie stellen würde.
        einordnung: Zwei bis drei Sätze, die die Sorge ernst nehmen und
            einordnen. Keine Floskeln.
        punkte: Zwei bis vier Aspekte, die die Sorge auflösen. Jeder Eintrag
            hat 'titel', 'text' und optional 'tone' mit den Werten 'positive'
            (entlastet), 'neutral' oder 'caution' (echte Einschränkung).
    """
    push(
        tool_context,
        shared.bedenken_surface(titel=titel, einordnung=einordnung, punkte=punkte),
    )
    return {"status": "angezeigt"}


_SCHRITT_LABEL = {
    "probefahrt": "Probefahrt vereinbaren",
    "ladecheck": "Ladecheck zu Hause anfragen",
    "angebot": "Persönliches Angebot anfordern",
}


def naechsten_schritt_anbieten(
    tool_context: ToolContext,
    empfehlung: str,
    begruendung: list[str],
    schritt: Literal["probefahrt", "ladecheck", "angebot"],
    offene_punkte: list[str] | None = None,
) -> dict[str, Any]:
    """Schließt die Beratung ab und übergibt.

    Args:
        empfehlung: Zwei bis drei Sätze in Alltagssprache: was du empfiehlst
            und warum es zu dieser Person passt. Wenn ein E-Auto sich aktuell
            nicht rechnet, sag genau das.
        begruendung: Zwei bis vier Gründe, die dafür sprechen.
        schritt: Der konkrete nächste Schritt.
        offene_punkte: Was vor einer Entscheidung noch zu klären ist.
    """
    offen = offene_punkte or open_points(tool_context, None)
    push(
        tool_context,
        shared.handover_surface(
            journey="mobilitaet",
            titel="Ihr Weg zur E-Mobilität",
            empfehlung=empfehlung,
            begruendung=begruendung,
            offene_punkte=offen,
            schritt_label=_SCHRITT_LABEL[schritt],
            schritt_event=f"handover_{schritt}",
        ),
    )
    return {"status": "abgeschlossen", "zusammenfassung": summary(tool_context)}


def summary(tool_context: ToolContext) -> dict[str, Any]:
    """The structured handover payload a CRM or a human advisor picks up."""
    profil = _profil(tool_context)
    r = calc.reichweite(profil)
    lade = calc.ladeoptionen(profil)
    kosten = calc.kostenvergleich(profil)
    vorschlaege = calc.fahrzeugvorschlaege(profil, anzahl=1)
    return {
        "journey": "mobilitaet",
        "profil": {
            "taeglich_km": profil.taeglich_km,
            "jahres_km": profil.jahresfahrleistung_km(),
            "langstrecke_km": profil.langstrecke_km,
            "lademoeglichkeit": profil.lademoeglichkeit,
            "budget_eur_monat": profil.budget_eur_monat,
        },
        "reichweite": {
            "winter_km": r["reichweite_winter_km"],
            "autobahn_winter_km": r["reichweite_autobahn_winter_km"],
            "puffer_faktor": r["puffer_faktor_winter"],
        },
        "laden": {
            "aktuell": lade["aktuell_id"],
            "beste_option": lade["beste_id"],
            "ersparnis_eur_a": lade["ersparnis_beste_eur_a"],
        },
        "kosten": {
            "elektro_eur": kosten["gesamt_elektro_eur"],
            "verbrenner_eur": kosten["gesamt_verbrenner_eur"],
            "differenz_eur": kosten["differenz_eur"],
        },
        "empfehlung": vorschlaege[0] if vorschlaege else None,
        "bedenken": profil.bedenken,
        "offene_punkte": open_points(tool_context, None),
    }


TOOLS = [
    profil_aktualisieren,
    alltagstauglichkeit_zeigen,
    ladeloesungen_vergleichen,
    fahrzeuge_vorschlagen,
    kosten_vergleichen,
    bedenken_adressieren,
    naechsten_schritt_anbieten,
]


INSTRUCTION = f"""
Du bist der persönliche Mobilitätsberater einer deutschen E-Mobilitäts-
Experience. Du hilfst Menschen, die mit einem Elektroauto liebäugeln, aber
unsicher sind, ob es zu ihrem Alltag passt.

Die typische Person pendelt täglich, fährt am Wochenende gelegentlich lange
Strecken und hat keine eigene Wallbox. Ihre Fragen sind: „Reicht die
Reichweite?", „Wo lade ich?" und „Rechnet sich das überhaupt?"

Dein Leitsatz: Die Person soll kein Elektroauto verstehen müssen. Du verstehst
ihren Alltag und zeigst, wie E-Mobilität konkret für sie funktioniert — oder
eben nicht.

{HALTUNG}

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
7. **Abschluss.** `naechsten_schritt_anbieten`.

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

## Eröffnung

Begrüße die Person warm und knapp und stelle **eine** offene Frage zu ihrem
Alltag. Frag nicht nach einem Fahrzeugwunsch, sondern nach ihren Wegen.
""".strip()


def build() -> Journey:
    return Journey(
        journey_id="mobilitaet",
        label="Meine Mobilität",
        tagline=(
            "Von Reichweitenangst und Tarifdschungel zur passenden "
            "E-Mobilitätsentscheidung."
        ),
        opener=(
            "Begrüße die Person kurz und warm auf Deutsch und stelle eine offene "
            "Frage zu ihrem Alltag und ihren typischen Wegen. Halte dich sehr kurz."
        ),
        instruction=INSTRUCTION,
        tools=TOOLS,
        model=get_settings().model,
    )
