"""Journey 02 — Der persönliche Autoberater."""

from __future__ import annotations

from typing import Any, Literal

from google.adk.tools import ToolContext

from ..a2ui import composer_mobilitaet as compose
from ..a2ui import composer_shared as shared
from ..config import get_settings
from ..domain import mobilitaet as calc
from ..texts import DEFAULT_LOCALE, Locale, Texts
from .base import (
    Journey,
    apply,
    join_list,
    load_profile,
    open_points,
    opening_line,
    save_profile,
    shown,
    texts_for,
)

Laden = Literal[
    "wallbox_zuhause", "steckdose_zuhause", "arbeitsplatz", "nur_oeffentlich"
]
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
    t = texts_for(tool_context)
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

    return shown(
        tool_context,
        compose.profil_surface(t, profil, offen),
        jahres_km=profil.jahresfahrleistung_km(),
        hinweis=t("hinweis.profil"),
    )


def alltagstauglichkeit_zeigen(tool_context: ToolContext) -> dict[str, Any]:
    """Zeigt die typische Woche gegen die reale Winterreichweite.

    Dazu die konkrete Langstrecke als Ablauf mit Ladestopps und Zeitaufwand.
    Das ist die Antwort auf Reichweitenangst. Rufe das auf, sobald du
    Tagesstrecke und Langstrecke kennst.
    """
    t = texts_for(tool_context)
    profil = _profil(tool_context)
    r = calc.reichweite(profil)
    ls = calc.langstrecke(profil, t)

    return shown(
        tool_context,
        compose.alltag_surface(t, profil),
        reichweite_winter_km=r["reichweite_winter_km"],
        reichweite_autobahn_winter_km=r["reichweite_autobahn_winter_km"],
        puffer_faktor_winter=r["puffer_faktor_winter"],
        taeglich_laden_noetig=r["taeglich_laden_noetig"],
        ladestopps_langstrecke=ls["ladestopps"],
        mehrzeit_min=ls["mehrzeit_min"],
    )


def ladeloesungen_vergleichen(tool_context: ToolContext) -> dict[str, Any]:
    """Vergleicht Wallbox, Laden beim Arbeitgeber und öffentliches Laden.

    Mischpreis je kWh, Kosten pro Jahr und je 100 km, und welcher Hebel am
    größten ist. Rufe das vor der Fahrzeugwahl auf — der Ladeort entscheidet
    stärker über die Kosten als das Modell.
    """
    t = texts_for(tool_context)
    profil = _profil(tool_context)
    lade = calc.ladeoptionen(profil, t)

    return shown(
        tool_context,
        compose.laden_surface(t, profil),
        aktuell=lade["aktuell_id"],
        beste_option=lade["beste_id"],
        ersparnis_eur_a=lade["ersparnis_beste_eur_a"],
        optionen=[
            {
                "id": o["id"],
                "label": o["label"],
                "kosten_eur_a": o["kosten_eur_a"],
                "kosten_eur_100km": o["kosten_eur_100km"],
                "verfuegbar": o["verfuegbar"],
            }
            for o in lade["optionen"]
        ],
    )


def fahrzeuge_vorschlagen(tool_context: ToolContext) -> dict[str, Any]:
    """Schlägt passende Fahrzeugklassen vor, sortiert nach Passung.

    Mit Winterreichweite, Ladestopps auf der Langstrecke, Monatsrate und offen
    benannten Vor- und Nachteilen.
    """
    t = texts_for(tool_context)
    profil = _profil(tool_context)
    vorschlaege = calc.fahrzeugvorschlaege(profil, t)

    return shown(
        tool_context,
        compose.fahrzeuge_surface(t, profil),
        vorschlaege=[
            {
                "label": v["label"],
                "score": v["score"],
                "reichweite_winter_km": v["reichweite_winter_km"],
                "ladestopps_langstrecke": v["ladestopps_langstrecke"],
                "leasing_eur_monat": v["leasing_eur_monat"],
                "contra": v["contra"],
            }
            for v in vorschlaege
        ],
    )


def kosten_vergleichen(tool_context: ToolContext) -> dict[str, Any]:
    """Stellt die Gesamtkosten von Elektro und Verbrenner gegenüber.

    Aufgeschlüsselt nach Wertverlust, Energie, Wartung, Versicherung, Steuer
    und THG-Quote. Nutze das für die Frage, ob es sich rechnet.
    """
    t = texts_for(tool_context)
    profil = _profil(tool_context)
    k = calc.kostenvergleich(profil, t)

    return shown(
        tool_context,
        compose.kosten_surface(t, profil),
        gesamt_elektro_eur=k["gesamt_elektro_eur"],
        gesamt_verbrenner_eur=k["gesamt_verbrenner_eur"],
        differenz_eur=k["differenz_eur"],
        differenz_eur_monat=k["differenz_eur_monat"],
        elektro_guenstiger=k["differenz_eur"] > 0,
        energie_elektro_eur_100km=k["energie_elektro_eur_100km"],
        energie_verbrenner_eur_100km=k["energie_verbrenner_eur_100km"],
        hinweis=t("hinweis.teurer"),
    )


def stellschrauben_zeigen(tool_context: ToolContext) -> dict[str, Any]:
    """Übergibt der Person die zwei Zahlen, bei denen sie bisher geschätzt hat.

    Zeigt zwei Regler — Kilometer an einem typischen Tag und Anteil, den sie zu
    Hause lädt — und rechnet Jahresfahrleistung, Strom- und Kraftstoffkosten
    live mit, während sie zieht.

    Rufe das auf, wenn jemand bei der Tagesstrecke oder beim Ladeort unsicher
    ist („so ungefähr", „mal so, mal so"), oder nachdem du die Kosten gezeigt
    hast. Sag danach in einem Satz, dass die Person selbst ziehen kann.
    """
    t = texts_for(tool_context)
    profil = _profil(tool_context)
    werte = calc.stellschrauben(profil)
    return shown(
        tool_context,
        compose.stellschrauben_surface(t, profil),
        taeglich_km=werte["taeglich_km"],
        anteil_zuhause=werte["anteil_zuhause"],
        hinweis=t("hinweis.regler"),
    )


def annahmen_uebernehmen(
    tool_context: ToolContext,
    taeglich_km: float,
    anteil_zuhause: float,
) -> dict[str, Any]:
    """Macht die eingestellte Strecke und Ladequote für die Beratung verbindlich.

    Danach rechnen alle Ansichten damit, und die Annahmenliste weist die Quote
    als die der Person aus. Rufe das auf, wenn die Person „Mit diesen Werten
    weiterrechnen" ausgelöst oder im Gespräch eigene Werte genannt hat.

    Args:
        taeglich_km: Kilometer an einem typischen Tag.
        anteil_zuhause: Anteil der Ladeenergie zu Hause, in Prozent.
    """
    # Auf ganze Einheiten gerundet: die Regler springen in Einerschritten, und
    # ein Wert dazwischen ließe Reglerstellung und Rechnung auseinanderlaufen.
    t = texts_for(tool_context)
    taeglich_km = float(round(taeglich_km))
    anteil_zuhause = float(min(100, max(0, round(anteil_zuhause))))

    profil = apply(
        _profil(tool_context),
        taeglich_km=taeglich_km,
        anteil_zuhause_laden=anteil_zuhause,
    )
    save_profile(tool_context, profil)

    # Alles, was schon auf dem Schirm steht, rechnet mit den alten Werten —
    # also neu aufbauen, damit nichts Widersprüchliches stehen bleibt.
    k = calc.kostenvergleich(profil, t)
    return shown(
        tool_context,
        compose.stellschrauben_surface(t, profil),
        compose.kosten_surface(t, profil),
        uebernommen={"taeglich_km": taeglich_km, "anteil_zuhause": anteil_zuhause},
        jahres_km=profil.jahresfahrleistung_km(),
        mischpreis_eur_kwh=round(calc.mischpreis_eur_kwh(profil), 3),
        differenz_eur_monat=k["differenz_eur_monat"],
        elektro_guenstiger=k["differenz_eur"] > 0,
        hinweis=t("hinweis.uebernommen.mobilitaet"),
    )


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
    t = texts_for(tool_context)
    return shown(
        tool_context,
        shared.bedenken_surface(t, titel=titel, einordnung=einordnung, punkte=punkte),
        status="angezeigt",
    )




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
    t = texts_for(tool_context)
    offen = offene_punkte or open_points(tool_context, None)
    return shown(
        tool_context,
        shared.handover_surface(
            t,
            journey="mobilitaet",
            titel=t("handover.title.mobilitaet"),
            empfehlung=empfehlung,
            begruendung=begruendung,
            offene_punkte=offen,
            schritt_label=t(f"schritt.{schritt}"),
            schritt_event=f"handover_{schritt}",
        ),
        status="abgeschlossen",
        zusammenfassung=summary(tool_context),
    )


def summary(tool_context: ToolContext) -> dict[str, Any]:
    """The structured handover payload a CRM or a human advisor picks up."""
    t = texts_for(tool_context)
    profil = _profil(tool_context)
    r = calc.reichweite(profil)
    lade = calc.ladeoptionen(profil, t)
    kosten = calc.kostenvergleich(profil, t)
    vorschlaege = calc.fahrzeugvorschlaege(profil, t, anzahl=1)
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
    stellschrauben_zeigen,
    annahmen_uebernehmen,
    bedenken_adressieren,
    naechsten_schritt_anbieten,
]


def build(locale: Locale = DEFAULT_LOCALE) -> Journey:
    """One journey, in one language.

    Everything the client reads or hears is looked up per locale; the tools and
    the arithmetic are the same either way.
    """
    t = Texts(locale)
    topics = t.list("journey.mobilitaet.topics")
    steps = [tuple(step.split("|")) for step in t.list("journey.mobilitaet.steps")]

    return Journey(
        journey_id="mobilitaet",
        locale=t.locale,
        label=t("journey.mobilitaet.label"),
        tagline=t("journey.mobilitaet.tagline"),
        opener=opening_line(t, topics, t("journey.mobilitaet.frage")),
        instruction=t(
            "journey.mobilitaet.instruction",
            haltung=t("prompt.haltung"),
            themen=join_list(t, topics),
        ),
        tools=TOOLS,
        model=get_settings().model,
        steps=steps,
        topics=topics,
    )
