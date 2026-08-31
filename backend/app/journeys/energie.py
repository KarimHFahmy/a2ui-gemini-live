"""Journey 01 — Der persönliche Energieberater.

Each tool is a plain Python function. ADK builds the declaration the model sees
from the signature and docstring, runs the domain calculation, and pushes the
composed A2UI surface to the browser. The model chooses *when*; it never
chooses the numbers or the layout.
"""

from __future__ import annotations

from typing import Any, Literal

from google.adk.tools import ToolContext

from ..a2ui import composer_energie as compose
from ..a2ui import composer_shared as shared
from ..config import get_settings
from ..domain import energie as calc
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

Heizung = Literal["gas", "oel", "fernwaerme", "nachtspeicher", "waermepumpe"]
Zustand = Literal["unsaniert", "teilsaniert", "saniert"]
Verteilung = Literal[
    "fussbodenheizung",
    "flaechenheizkoerper_gross",
    "heizkoerper_standard",
    "heizkoerper_klein_alt",
]
Weg = Literal["waermepumpe", "waermepumpe_huelle", "waermepumpe_pv"]


def _profil(tool_context: ToolContext) -> calc.Gebaeudeprofil:
    return load_profile(tool_context, calc.Gebaeudeprofil)


def _szenarien(tool_context: ToolContext) -> list[calc.Szenario]:
    return calc.szenarien(
        _profil(tool_context),
        einkommensbonus=bool(tool_context.state.get("_einkommensbonus", False)),
    )


def _gewaehlt(tool_context: ToolContext, requested: str | None) -> str:
    """Remembers which path the conversation is currently working on."""
    if requested:
        tool_context.state["_gewaehltes_szenario"] = requested
        return requested
    return str(tool_context.state.get("_gewaehltes_szenario", "waermepumpe"))


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def profil_aktualisieren(
    tool_context: ToolContext,
    baujahr: int | None = None,
    wohnflaeche_qm: float | None = None,
    heizung: Heizung | None = None,
    sanierungsstand: Zustand | None = None,
    waermesystem: Verteilung | None = None,
    personen: int | None = None,
    verbrauch_kwh_a: float | None = None,
    pv_vorhanden: bool | None = None,
    prioritaeten: list[str] | None = None,
    bedenken: list[str] | None = None,
    offene_punkte: list[str] | None = None,
) -> dict[str, Any]:
    """Zeigt auf dem Bildschirm, was du über das Zuhause verstanden hast.

    Rufe das früh auf und danach jedes Mal, wenn du etwas Neues erfährst oder
    die Person dich korrigiert. Übergib nur, was du tatsächlich weißt.

    Args:
        baujahr: Baujahr des Gebäudes.
        wohnflaeche_qm: Beheizte Wohnfläche in Quadratmetern.
        heizung: Die heutige Heizung.
        sanierungsstand: Zustand der Gebäudehülle, z. B. teilsaniert wenn
            Fenster oder Dach schon erneuert wurden.
        waermesystem: Wie die Wärme im Haus verteilt wird. Bestimmt die nötige
            Vorlauftemperatur und damit die Eignung.
        personen: Personen im Haushalt.
        verbrauch_kwh_a: Gemessener Jahresverbrauch in kWh, falls bekannt.
            Schlägt jede Schätzung — frag ruhig danach.
        pv_vorhanden: Ob bereits eine PV-Anlage auf dem Dach ist.
        prioritaeten: Was der Person wichtig ist, in ihren Worten.
        bedenken: Geäußerte Sorgen, in den Worten der Person.
        offene_punkte: Was du noch nicht weißt und geschätzt hast. Wird der
            Person transparent angezeigt.
    """
    t = texts_for(tool_context)
    profil = apply(
        _profil(tool_context),
        baujahr=baujahr,
        wohnflaeche_qm=wohnflaeche_qm,
        heizung=heizung,
        sanierungsstand=sanierungsstand,
        waermesystem=waermesystem,
        personen=personen,
        verbrauch_kwh_a=verbrauch_kwh_a,
        pv_vorhanden=pv_vorhanden,
        prioritaeten=prioritaeten,
        bedenken=bedenken,
    )
    save_profile(tool_context, profil)
    offen = open_points(tool_context, offene_punkte)

    return shown(
        tool_context,
        compose.profil_surface(t, profil, offen),
        waermebedarf_kwh_a=calc.waermebedarf_kwh_a(profil),
        hinweis=t("hinweis.profil"),
    )


def waermepumpen_eignung_zeigen(tool_context: ToolContext) -> dict[str, Any]:
    """Zeigt, ob das Haus für eine Wärmepumpe geeignet ist.

    Nötige Vorlauftemperatur, erwartete Jahresarbeitszahl, Heizlast und der
    Verlauf der Heizlast über den Winter. Beantwortet die Sorge, ob es im
    Winter reicht. Rufe das auf, sobald du Gebäude, Heizung und Wärmeverteilung
    kennst.
    """
    t = texts_for(tool_context)
    profil = _profil(tool_context)
    check = calc.eignung(profil)
    return shown(
        tool_context,
        compose.eignung_surface(t, profil),
        urteil=check["urteil"],
        score=check["score"],
        vorlauftemperatur_c=check["vorlauftemperatur_c"],
        jaz=check["jaz"],
        heizlast_kw=check["heizlast_kw"],
        hinweise=check["hinweise"],
        massnahmen=check["massnahmen"],
    )


def szenarien_vergleichen(
    tool_context: ToolContext,
    empfohlen: Literal["bestand", "waermepumpe", "waermepumpe_huelle", "waermepumpe_pv"]
    | None = None,
) -> dict[str, Any]:
    """Stellt die möglichen Wege nebeneinander.

    Weiter wie bisher, Wärmepumpe, Wärmepumpe mit Dämmung, Wärmepumpe mit PV —
    mit Investition, Förderung, Eigenanteil, laufenden Kosten und CO2. Die
    Person kann auf dem Bildschirm einen Weg auswählen.

    Args:
        empfohlen: Welchen Weg du auf Basis des Gesprächs hervorhebst.
            Orientiere dich an den Prioritäten der Person.
    """
    t = texts_for(tool_context)
    szenarien = _szenarien(tool_context)
    verfuegbar = {s.id for s in szenarien}
    gewaehlt = _gewaehlt(tool_context, empfohlen if empfohlen in verfuegbar else None)

    return shown(
        tool_context,
        compose.szenarien_surface(t, _profil(tool_context), szenarien, empfohlen_id=gewaehlt),
        hervorgehoben=gewaehlt,
        szenarien=[
            {
                "id": s.id,
                "label": s.label,
                "eigenanteil_eur": s.eigenanteil_eur,
                "energiekosten_eur_a": s.energiekosten_eur_a,
                "co2_kg_a": s.co2_kg_a,
            }
            for s in szenarien
        ],
    )


def wirtschaftlichkeit_zeigen(
    tool_context: ToolContext,
    szenario: Weg = "waermepumpe",
) -> dict[str, Any]:
    """Rechnet einen Weg über 20 Jahre durch.

    Kumulierte Gesamtkosten gegenüber „weiter wie bisher", Break-even-Punkt und
    jährliche Ersparnis. Nutze das, wenn die Person wissen will, ob es sich lohnt.

    Args:
        szenario: Der Weg, der durchgerechnet werden soll.
    """
    t = texts_for(tool_context)
    szenarien = _szenarien(tool_context)
    fokus_id = _gewaehlt(tool_context, szenario)
    if fokus_id not in {s.id for s in szenarien}:
        fokus_id = _gewaehlt(tool_context, "waermepumpe")

    bestand = next(s for s in szenarien if s.id == "bestand")
    fokus = next(s for s in szenarien if s.id == fokus_id)
    amort = calc.amortisation(bestand, fokus)

    return shown(
        tool_context,
        compose.wirtschaftlichkeit_surface(t, _profil(tool_context), szenarien, fokus_id=fokus_id),
        szenario=fokus.label,
        eigenanteil_eur=fokus.eigenanteil_eur,
        ersparnis_eur_a=round(bestand.betriebskosten_eur_a - fokus.betriebskosten_eur_a),
        break_even_jahre=amort["jahre"],
        break_even_erreichbar=amort["erreichbar"],
    )


def foerderung_und_fahrplan_zeigen(
    tool_context: ToolContext,
    szenario: Weg = "waermepumpe",
    einkommensbonus: bool = False,
) -> dict[str, Any]:
    """Zeigt den erwarteten Zuschuss und den Umsetzungsfahrplan.

    Wie sich die Förderquote zusammensetzt, und die fünf Schritte inklusive des
    Hinweises, dass der Antrag vor der Beauftragung gestellt werden muss.

    Args:
        szenario: Der Weg, für den gefördert wird.
        einkommensbonus: Nur auf true setzen, wenn die Person von sich aus
            gesagt hat, dass das Haushaltseinkommen unter der Bonusgrenze
            liegt. Frag nicht aktiv danach.
    """
    t = texts_for(tool_context)
    tool_context.state["_einkommensbonus"] = einkommensbonus
    szenarien = _szenarien(tool_context)
    szenario_id = _gewaehlt(tool_context, szenario)
    if szenario_id not in {s.id for s in szenarien}:
        szenario_id = _gewaehlt(tool_context, "waermepumpe")
    gewaehlt = next(s for s in szenarien if s.id == szenario_id)

    details = calc.foerderung(
        min(gewaehlt.investition_eur, calc.dd.FOERDERUNG["hoechstkosten_efh_eur"]),
        einkommensbonus=einkommensbonus,
    )

    return shown(
        tool_context,
        compose.foerderung_surface(t, _profil(tool_context), gewaehlt, details),
        foerderquote=details["satz"],
        betrag_eur=details["betrag_eur"],
        eigenanteil_eur=gewaehlt.eigenanteil_eur,
        hinweis=t("hinweis.foerderung"),
    )


def stellschrauben_zeigen(tool_context: ToolContext) -> dict[str, Any]:
    """Übergibt der Person die zwei Preisannahmen, an denen alles hängt.

    Zeigt zwei Regler — Preis des heutigen Brennstoffs und Strompreis der
    Wärmepumpe — und rechnet Heizkosten, monatlichen Unterschied und die Bilanz
    nach 20 Jahren live mit, während die Person zieht.

    Rufe das auf, sobald jemand die Zahlen anzweifelt („da rechnet ihr euch das
    schön", „und wenn der Strompreis steigt?"), oder nach
    `wirtschaftlichkeit_zeigen`, um die Rechnung überprüfbar zu machen. Sag
    danach in einem Satz, dass die Person selbst am Regler ziehen kann.
    """
    t = texts_for(tool_context)
    profil = _profil(tool_context)
    szenarien = _szenarien(tool_context)
    fokus_id = _gewaehlt(tool_context, None)
    if fokus_id not in {s.id for s in szenarien}:
        fokus_id = "waermepumpe"

    bestand = next(s for s in szenarien if s.id == "bestand")
    fokus = next(s for s in szenarien if s.id == fokus_id)

    werte = calc.stellschrauben(profil, bestand, fokus)
    return shown(
        tool_context,
        compose.stellschrauben_surface(t, profil, bestand, fokus),
        szenario=fokus.label,
        preis_alt_ct=werte["preis_alt_ct"],
        preis_strom_ct=werte["preis_strom_ct"],
        hinweis=t("hinweis.regler"),
    )


def annahmen_uebernehmen(
    tool_context: ToolContext,
    preis_alt_ct: float,
    preis_strom_ct: float,
) -> dict[str, Any]:
    """Macht die eingestellten Preise für die ganze Beratung verbindlich.

    Danach rechnen alle Ansichten mit diesen Preisen, und die Annahmenliste
    weist sie als die Annahmen der Person aus. Rufe das auf, wenn die Person
    „Mit diesen Preisen weiterrechnen" ausgelöst oder im Gespräch eigene Preise
    genannt hat.

    Args:
        preis_alt_ct: Preis des heutigen Brennstoffs in Cent je Kilowattstunde.
        preis_strom_ct: Strompreis der Wärmepumpe in Cent je Kilowattstunde.
    """
    # Auf ganze Cent gerundet: die Regler springen in Einerschritten, und ein
    # Preis dazwischen ließe Reglerstellung und Rechnung auseinanderlaufen.
    t = texts_for(tool_context)
    preis_alt_ct = float(round(preis_alt_ct))
    preis_strom_ct = float(round(preis_strom_ct))

    profil = apply(
        _profil(tool_context),
        preis_alt_ct=preis_alt_ct,
        preis_strom_ct=preis_strom_ct,
    )
    save_profile(tool_context, profil)

    # Alles, was schon auf dem Schirm steht, rechnet mit den alten Preisen —
    # also neu aufbauen, damit nichts Widersprüchliches stehen bleibt.
    szenarien = _szenarien(tool_context)
    fokus_id = _gewaehlt(tool_context, None)
    if fokus_id not in {s.id for s in szenarien}:
        fokus_id = "waermepumpe"
    bestand = next(s for s in szenarien if s.id == "bestand")
    fokus = next(s for s in szenarien if s.id == fokus_id)

    amort = calc.amortisation(bestand, fokus)
    return shown(
        tool_context,
        compose.stellschrauben_surface(t, profil, bestand, fokus),
        compose.szenarien_surface(t, profil, szenarien, empfohlen_id=fokus_id),
        compose.wirtschaftlichkeit_surface(t, profil, szenarien, fokus_id=fokus_id),
        uebernommen={"preis_alt_ct": preis_alt_ct, "preis_strom_ct": preis_strom_ct},
        ersparnis_eur_a=round(bestand.betriebskosten_eur_a - fokus.betriebskosten_eur_a),
        break_even_jahre=amort["jahre"],
        break_even_erreichbar=amort["erreichbar"],
        hinweis=t("hinweis.uebernommen.energie"),
    )


def bedenken_adressieren(
    tool_context: ToolContext,
    titel: str,
    einordnung: str,
    punkte: list[dict[str, str]],
) -> dict[str, Any]:
    """Beantwortet eine konkrete Sorge mit einer eigenen Ansicht.

    Nutze das, sobald jemand eine Unsicherheit äußert („ich habe Sorge,
    dass…", „lohnt sich das überhaupt", „was ist wenn…"). Formuliere die Sorge
    in der Sprache der Person, nicht in Fachsprache.

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
    schritt: Literal["beratungstermin", "vor_ort_check", "foerder_check"],
    offene_punkte: list[str] | None = None,
) -> dict[str, Any]:
    """Schließt die Beratung ab und übergibt.

    Zusammenfassung, Empfehlung mit Begründung, offene Punkte und ein konkreter
    nächster Schritt. Rufe das auf, wenn die Person genug gesehen hat oder
    selbst nach dem nächsten Schritt fragt.

    Args:
        empfehlung: Zwei bis drei Sätze in Alltagssprache: was du empfiehlst
            und warum es zu dieser Person passt.
        begruendung: Zwei bis vier Gründe, die für diesen Weg sprechen.
        schritt: Der konkrete nächste Schritt.
        offene_punkte: Was vor einer Entscheidung noch zu klären ist. Ehrlich
            benennen, nicht beschönigen.
    """
    t = texts_for(tool_context)
    offen = offene_punkte or open_points(tool_context, None)
    return shown(
        tool_context,
        shared.handover_surface(
            t,
            journey="energie",
            titel=t("handover.title.energie"),
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
    check = calc.eignung(profil)
    szenarien = _szenarien(tool_context)
    gewaehlt = next(
        (s for s in szenarien if s.id == _gewaehlt(tool_context, None)), szenarien[1]
    )
    return {
        "journey": "energie",
        "gebaeude": {
            "baujahr": profil.baujahr,
            "wohnflaeche_qm": profil.wohnflaeche_qm,
            "heizung": profil.heizung,
            "sanierungsstand": profil.sanierungsstand,
            "waermebedarf_kwh_a": calc.waermebedarf_kwh_a(profil),
        },
        "eignung": {
            "urteil": check["urteil"],
            "score": check["score"],
            "jaz": check["jaz"],
            "vorlauftemperatur_c": check["vorlauftemperatur_c"],
        },
        "empfehlung": {
            "szenario": gewaehlt.label,
            "eigenanteil_eur": gewaehlt.eigenanteil_eur,
            "energiekosten_eur_a": gewaehlt.energiekosten_eur_a,
            # Resolved rather than passed as keys: this payload leaves the
            # system for a CRM or a human advisor, who has no catalog.
            "massnahmen": [t(key) for key in gewaehlt.massnahmen],
        },
        "prioritaeten": profil.prioritaeten,
        "bedenken": profil.bedenken,
        "offene_punkte": open_points(tool_context, None),
    }


TOOLS = [
    profil_aktualisieren,
    waermepumpen_eignung_zeigen,
    szenarien_vergleichen,
    wirtschaftlichkeit_zeigen,
    foerderung_und_fahrplan_zeigen,
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
    topics = t.list("journey.energie.topics")
    steps = [tuple(step.split("|")) for step in t.list("journey.energie.steps")]

    return Journey(
        journey_id="energie",
        locale=t.locale,
        label=t("journey.energie.label"),
        tagline=t("journey.energie.tagline"),
        opener=opening_line(t, topics, t("journey.energie.frage")),
        instruction=t(
            "journey.energie.instruction",
            haltung=t("prompt.haltung"),
            themen=join_list(t, topics),
        ),
        tools=TOOLS,
        model=get_settings().model,
        steps=steps,
        topics=topics,
    )
