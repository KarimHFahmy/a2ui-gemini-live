"""English, translated from `de.py`.

Not a literal translation. The German copy addresses a client as *Sie* and
carries the register of a German utility advisor; the English is written to do
the same job for an English speaker rather than to mirror the sentence. Where
German names a thing the English-speaking market calls something else — the
BEG subsidy, the Jahresarbeitszahl — the English uses the working term and
keeps the German in brackets, because the client will meet the German word on
every document they are sent afterwards.

Key set must match `de.py` exactly; `test_texts.py` fails if it does not.
"""

from __future__ import annotations

from typing import Any

TEXTS: dict[str, Any] = {
    # -- Data provenance, shown under every figure --------------------------
    "data.as_of": "Demo assumptions, as of Q3/2026",
    "data.source.energie": "Energy demo dataset (example values, not a basis for quotes)",
    "data.source.mobilitaet": (
        "E-mobility demo dataset (example values, not a basis for quotes)"
    ),
    "data.disclaimer": (
        "All figures are illustrative demo values. They do not replace "
        "professional advice and are not a binding offer."
    ),
    "data.foerderung.hinweis": (
        "The subsidy depends on when you apply, proof of income and the type of "
        "building. Illustrative here — have your own case checked."
    ),
    # -- Building blocks used by every surface -------------------------------
    "block.assumptions.trigger": "See assumptions and sources",
    "block.assumptions.title": "Assumptions and sources",
    "block.assumptions.source": "{source} · {as_of}",
    "block.none_open": "Nothing outstanding",
    "block.still_open": "Still open",
    "block.dash": "–",
    # -- The profile surface, pinned in the context column -------------------
    "profil.eyebrow": "Your situation",
    "profil.title": "Here is what I understood",
    "profil.correct_me": "Just say so if anything is wrong — I will correct it.",
    # -- The handover ---------------------------------------------------------
    "handover.eyebrow": "Your next step",
    "handover.subtitle": "Everything we discussed, on one page.",
    "handover.recommendation": "What I recommend for you",
    "handover.pro": "In favour",
    "handover.open": "Still to clarify",
    "handover.not_binding": "You decide how this goes on — none of it is binding.",
    "handover.second.energie": "Email me the summary",
    "handover.second.mobilitaet": "Request a quote",
    "handover.title.energie": "Your route to a new heating system",
    "handover.title.mobilitaet": "Your route to driving electric",
    "schritt.beratungstermin": "Book an advisory appointment",
    "schritt.vor_ort_check": "Request a survey at your home",
    "schritt.foerder_check": "Have your eligibility checked",
    "schritt.probefahrt": "Book a test drive",
    "schritt.ladecheck": "Request a charging check at home",
    "schritt.angebot": "Request a personal quote",
    "energie.massnahmen.keine": 'No preparation needed',
    "energie.massnahmen.wp": 'Air-to-water heat pump',
    "energie.massnahmen.heizkoerper": 'Replace the critical radiators',
    "energie.massnahmen.daemmung": 'Roof insulation',
    "energie.massnahmen.pv": 'Solar with battery storage',
    "hinweis.profil": 'Briefly confirm what you understood, without reading out every value.',
    "hinweis.foerderung": 'The application must be made before the work is commissioned — say so out loud.',
    "hinweis.regler": 'They can move the sliders themselves. Invite them to, rather than reading figures out.',
    "hinweis.uebernommen.energie": 'Briefly confirm that you are now calculating with their prices, and say what that shifted.',
    "hinweis.uebernommen.mobilitaet": 'Briefly confirm that you are now calculating with their values, and say what that shifted. Then call `profil_aktualisieren` so the summary is right.',
    "hinweis.teurer": 'If the electric car is more expensive, say so openly and use the charging options to show what would have to change.',
    "energie.massnahmen.abgleich": 'Hydraulic balancing',
    "energie.massnahmen.pv_anlage": 'Solar array, 10 kWp',
    "energie.massnahmen.speicher": 'Battery storage, 8 kWh',
    "handover.assumptions": [
        "This advice is non-binding and is not a quote.",
        "What you tell me stays in this session and is not stored.",
    ],
    # ======================================================================
    # My Home — energy advice
    # ======================================================================
    "energie.heizung.gas": "gas boiler",
    "energie.heizung.oel": "oil boiler",
    "energie.heizung.fernwaerme": "district heating",
    "energie.heizung.nachtspeicher": "night storage heating",
    "energie.heizung.waermepumpe": "heat pump",
    "energie.traeger.gas": "natural gas",
    "energie.traeger.oel": "heating oil",
    "energie.traeger.fernwaerme": "district heat",
    "energie.traeger.strom": "electricity",
    "energie.stand.unsaniert": "largely unrenovated",
    "energie.stand.teilsaniert": "partly renovated",
    "energie.stand.saniert": "well renovated",
    # -- Profile ------------------------------------------------------------
    "energie.profil.gebaeude": "Building",
    "energie.profil.gebaeude_wert": "built {baujahr}, {flaeche} m²",
    "energie.profil.heizung": "Heating today",
    "energie.profil.zustand": "Condition",
    "energie.profil.haushalt": "Household",
    "energie.profil.haushalt_wert": "{personen} people",
    "energie.profil.bedarf": "Heat demand",
    "energie.profil.bedarf_wert": "{bedarf} kWh/year",
    "energie.profil.prioritaeten": "Matters to you",
    "energie.profil.bedenken": "Your concerns",
    # -- Suitability check ---------------------------------------------------
    "energie.eignung.eyebrow": "Heat pump check",
    "energie.eignung.title": "Your house is {urteil}",
    "energie.eignung.subtitle": (
        "What decides this is not the outside temperature but how hot the water "
        "in your radiators has to be."
    ),
    "energie.eignung.vorlauf": "Flow temperature needed",
    "energie.eignung.vorlauf_label": "on the coldest design day",
    "energie.eignung.vorlauf_body": (
        "The lower it is, the more efficiently a heat pump runs. Below 55 °C there "
        "is nothing to worry about."
    ),
    "energie.eignung.jaz": "Expected seasonal performance",
    "energie.eignung.jaz_label": "SPF",
    "energie.eignung.jaz_body": (
        "1 kWh of electricity becomes {jaz} kWh of heat – about {strom} kWh of "
        "electricity a year."
    ),
    "energie.eignung.heizlast": "Heat output needed",
    "energie.eignung.heizlast_label": "design heat load",
    "energie.eignung.heizlast_body": (
        "This is what the heat pump is sized against. Oversized, it cycles on and "
        "off and wears out sooner."
    ),
    "energie.eignung.chart_title": "How your heat demand spreads across the winter",
    "energie.eignung.chart_sub_stab": (
        "Even in January the heat pump covers the load – on the coldest days with "
        "the immersion heater."
    ),
    "energie.eignung.chart_sub_allein": "Even in January the heat pump covers the load on its own.",
    "energie.eignung.serie_wp": "Heat pump",
    "energie.eignung.serie_heizstab": "Immersion heater",
    "energie.eignung.massnahmen": "What would improve efficiency further",
    "energie.monate": ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"],
    # -- Scenarios ------------------------------------------------------------
    "energie.szenarien.eyebrow": "Your options",
    "energie.szenarien.title": "Three routes, one home",
    "energie.szenarien.subtitle": "Pick one and I will work it through for you.",
    "energie.szenarien.picker": "Scenario",
    "energie.szenarien.keine_investition": "no investment",
    "energie.szenarien.button": "Work this one through",
    "energie.szenarien.table": "The routes side by side",
    "energie.szenarien.row.investition": "Investment",
    "energie.szenarien.row.foerderung": "Subsidy",
    "energie.szenarien.row.eigenanteil": "Your share",
    "energie.szenarien.row.energiekosten": "Energy cost per year",
    "energie.szenarien.row.co2": "CO₂ per year",
    "energie.szenarien.row.komfort": "Comfort",
    "energie.szenarien.row.aufwand": "Disruption for you",
    "energie.komfort.1": "low",
    "energie.komfort.2": "noticeable",
    "energie.komfort.3": "good",
    "energie.komfort.4": "high",
    "energie.komfort.5": "very high",
    "energie.aufwand.1": "none",
    "energie.aufwand.2": "little",
    "energie.aufwand.3": "moderate",
    "energie.aufwand.4": "high",
    "energie.aufwand.5": "very high",
    # -- Economics -------------------------------------------------------------
    "energie.wirtschaft.eyebrow": "The economics",
    "energie.wirtschaft.title": "“{szenario}” over 20 years",
    "energie.wirtschaft.subtitle": (
        "Investment, subsidy and running costs looked at together."
    ),
    "energie.wirtschaft.chart_title": "Cumulative total cost",
    "energie.wirtschaft.chart_sub": (
        "Where the lines cross is your break-even against carrying on as you are."
    ),
    "energie.wirtschaft.breakeven": "Break-even",
    "energie.wirtschaft.breakeven_label": "until it evens out",
    "energie.wirtschaft.breakeven_jahre": "{jahre} years",
    "energie.wirtschaft.breakeven_body": (
        "After roughly {jahre} years you have the extra investment back. "
        "From then on you save every year."
    ),
    "energie.wirtschaft.breakeven_nie": (
        "Over 40 years the extra investment does not pay itself back. This route "
        "is worth it for comfort and CO₂ rather than for the money."
    ),
    "energie.wirtschaft.laufend": "Running costs per year",
    "energie.wirtschaft.laufend_label": "per year",
    "energie.wirtschaft.laufend_body": (
        "Instead of {alt} you pay {neu} – energy and servicing together."
    ),
    "energie.wirtschaft.gesamt": "Over 20 years",
    "energie.wirtschaft.gesamt_label": "total advantage",
    "energie.wirtschaft.gesamt_body": (
        "The difference against carrying on as you are, including the investment, "
        "the subsidy and the assumed price rises."
    ),
    # -- Funding ---------------------------------------------------------------
    "energie.foerderung.surface": "Subsidy & plan",
    "energie.foerderung.eyebrow": "Subsidy & getting it done",
    "energie.foerderung.title": "What the state pays for – and in what order",
    "energie.foerderung.subtitle": (
        "The order matters: commission the work too early and you lose the grant."
    ),
    "energie.foerderung.zuschuss": "Expected grant",
    "energie.foerderung.quote": "{satz} of eligible cost",
    "energie.foerderung.zuschuss_body": (
        "Against eligible costs of {kosten}. That brings your own share down to "
        "{eigenanteil}."
    ),
    "energie.foerderung.bausteine": "How the rate adds up",
    "energie.foerderung.deckel": "Capped at {max} (calculated {roh})",
    "energie.foerderung.baustein.grund": "Base grant",
    "energie.foerderung.baustein.klima": "Early-replacement bonus",
    "energie.foerderung.baustein.einkommen": "Income bonus",
    "energie.foerderung.baustein.effizienz": "Efficiency bonus",
    "energie.foerderung.plan": "Your route, in five steps",
    "energie.foerderung.assumptions": [
        "You must apply before any work begins.",
        "Bonuses require evidence (income, replacing the old system).",
    ],
    "energie.schritte": [
        "**1. Energy assessment and quote**|An installer surveys the building, "
        "checks the heat load and the radiators, and quotes.|2–4 weeks",
        "**2. Apply for the grant**|Submit the application with the supply and "
        "installation contract. **Important:** before any work starts, or the "
        "grant is gone.|1–2 weeks",
        "**3. Wait for approval**|Only commission the work once it is "
        "approved.|2–6 weeks",
        "**4. Installation**|Fitting the heat pump, balancing the system and "
        "setting the heating curve.|2–5 days",
        "**5. Evidence and payout**|Submit the installer's declaration and the "
        "grant is paid.|4–8 weeks",
    ],
    # -- Verdicts and findings the calculation produces, as keys -------------
    "energie.urteil.gut": "a good fit",
    "energie.urteil.vorbereitung": "a fit, with some preparation",
    "energie.urteil.erst_spaeter": "worth it only after some preparation",
    "energie.hinweis.hoher_vorlauf": (
        "On the coldest days your existing radiators need a high flow "
        "temperature. That noticeably reduces efficiency."
    ),
    "energie.hinweis.standard_vorlauf": (
        "With standard radiators a heat pump runs well, though not optimally."
    ),
    "energie.hinweis.guter_vorlauf": "Your heat distribution suits a heat pump very well.",
    "energie.hinweis.hoher_bedarf": (
        "Heat demand per square metre is high — the building fabric is a bigger "
        "lever here than the heating technology."
    ),
    "energie.massnahme.heizkoerper": "Replace individual radiators with low-temperature ones",
    "energie.massnahme.abgleich": "Balance the system hydraulically and lower the heating curve",
    "energie.massnahme.daemmung": "Insulate the roof or replace windows first",
    "energie.massnahme.dachboden": "Consider loft insulation as a cheap first step",
    # -- Scenario names and descriptions ---------------------------------------
    "energie.szenario.bestand": "Carry on as you are",
    "energie.szenario.bestand.beschreibung": (
        "The existing boiler stays. No investment, but rising energy costs and "
        "carbon pricing."
    ),
    "energie.szenario.waermepumpe": "Heat pump",
    "energie.szenario.waermepumpe.beschreibung": (
        "Change the heating, leave the building fabric alone. The fastest way off "
        "fossil fuel."
    ),
    "energie.szenario.waermepumpe_huelle": "Heat pump + roof insulation",
    "energie.szenario.waermepumpe_huelle.beschreibung": (
        "Cut the demand first, then size the heat pump smaller. A bigger "
        "investment, but the lowest running costs for good."
    ),
    "energie.szenario.waermepumpe_pv": "Heat pump + solar & battery",
    "energie.szenario.waermepumpe_pv.beschreibung": (
        "Heat and electricity together. Part of the heat pump's power comes off "
        "your own roof, which decouples you from electricity prices."
    ),
    "energie.jahr": "Year {jahr}",
    # -- The assumption list under every figure ---------------------------------
    "energie.annahmen.bedarf": "Heat demand {bedarf} kWh/a",
    "energie.annahmen.preise": (
        "Heat pump electricity {strom} €/kWh, {traeger} {alt} €/kWh{eigene}"
    ),
    "energie.annahmen.eigene": " (your own assumptions)",
    "energie.annahmen.steigerung": "Electricity rising {strom} p.a., fossil {fossil} p.a.",
    "energie.annahmen.jaz": "Seasonal performance {jaz} at {vorlauf} °C flow temperature",
    "energie.annahmen.dauer": "20-year horizon, subsidy on the demo BEG logic",
    # -- What-if ----------------------------------------------------------------
    "energie.wenn.surface": "What if",
    "energie.wenn.title": "Use your own prices",
    "energie.wenn.subtitle": (
        "Nobody knows what energy will cost over the next twenty years — I do not "
        "either. Set what you think is realistic. The figures below follow "
        "immediately."
    ),
    "energie.wenn.annahmen": "Your assumptions",
    "energie.wenn.regler_alt": "{traeger} price in cents per kWh",
    "energie.wenn.regler_strom": "Electricity price for the heat pump, cents per kWh",
    "energie.wenn.heute": "Today with a {heizung}",
    "energie.wenn.danach": "Switching to: {szenario}",
    "energie.wenn.pro_jahr_wartung": "per year, incl. servicing",
    "energie.wenn.unterschied": "Difference",
    "energie.wenn.pro_monat": "per month",
    "energie.wenn.nach_20": "After 20 years",
    "energie.wenn.nach_eigenanteil": "after your own share of {eigenanteil}",
    "energie.wenn.uebernehmen_title": "Shall we carry on with these?",
    "energie.wenn.uebernehmen_body": (
        "So far I am using the demo prices. Take your settings over and they apply "
        "to the whole session — the comparison, the economics and the recommendation."
    ),
    "energie.wenn.uebernehmen_button": "Carry on with these prices",
    "energie.wenn.assumptions": [
        "Heat demand {bedarf} kWh/a",
        "That means {alt} kWh of {traeger} today against {neu} kWh of electricity after",
        "The sliders change only the two prices — demand, seasonal performance and "
        "the investment stay as calculated.",
        "Price rises are deliberately not included here: you are setting the price "
        "that should hold on average over the period.",
    ],
    # ======================================================================
    # My Mobility — e-mobility advice
    # ======================================================================
    "mob.lade.wallbox_zuhause": "Home wallbox",
    "mob.lade.steckdose_zuhause": "Household socket",
    "mob.lade.arbeitsplatz": "Charging at work",
    "mob.lade.nur_oeffentlich": "Public only",
    "mob.lade.nur_oeffentlich.lang": "Public charging only",
    "mob.quelle.zuhause": "At home",
    "mob.quelle.arbeit": "At work",
    "mob.quelle.ac_oeffentlich": "Public AC",
    "mob.quelle.dc_schnell": "DC rapid",
    "mob.kraftstoff.benzin": "petrol",
    "mob.kraftstoff.diesel": "diesel",
    "mob.ja": "yes",
    "mob.nein": "no",
    # -- Profile --------------------------------------------------------------
    "mob.profil.eyebrow": "Your week",
    "mob.profil.correct_me": "Correct me at any point — I recalculate straight away.",
    "mob.profil.taeglich": "Daily",
    "mob.profil.taeglich_wert": "{km} km on {tage} days",
    "mob.profil.langstrecke": "Long trips",
    "mob.profil.langstrecke_wert": "{mal}× a month, ~ {km} km",
    "mob.profil.laden": "Charging",
    "mob.profil.jahr": "Per year",
    "mob.profil.wunsch": "Car you want",
    "mob.profil.budget": "Budget",
    "mob.profil.budget_wert": "up to {budget} a month",
    "mob.profil.bedenken": "Your concerns",
    # -- Everyday practicality --------------------------------------------------
    "mob.alltag.eyebrow": "Does it fit your week",
    "mob.alltag.title": "Your week with an electric car",
    "mob.alltag.subtitle": (
        "What counts is not the brochure figure but the range on a cold January "
        "morning."
    ),
    "mob.alltag.puffer": "Headroom day to day",
    "mob.alltag.puffer_label": "of what you drive daily",
    "mob.alltag.puffer_gut": (
        "Your {km} km a day are a non-issue even in winter. You would charge about "
        "{laden}."
    ),
    "mob.alltag.puffer_ok": (
        "Your daily distance fits, with solid headroom left in winter. You would "
        "charge about {laden}."
    ),
    "mob.alltag.puffer_knapp": (
        "Winter would be tight – you would have to charge almost daily. A bigger "
        "battery or reliable charging matters here."
    ),
    "mob.alltag.laden_woche": "once a week",
    "mob.alltag.laden_tage": "every {tage} days",
    "mob.alltag.laden_zwei": "every other day",
    "mob.alltag.winter": "Winter range",
    "mob.alltag.winter_label": "{fahrzeug}, {batterie} kWh",
    "mob.alltag.winter_body": (
        "In the cold consumption rises to {verbrauch} kWh/100 km. In summer it is "
        "{sommer} km."
    ),
    "mob.alltag.autobahn": "Motorway in winter",
    "mob.alltag.autobahn_label": "{verbrauch} kWh/100 km",
    "mob.alltag.autobahn_body": (
        "The honest figure: cold, at motorway cruising speed. Plan long trips "
        "against this one and they hold up."
    ),
    "mob.alltag.chart_title": "Your typical week",
    "mob.alltag.chart_sub": (
        "The line is your winter range. As long as the bars stay under it, you get "
        "through without charging mid-day."
    ),
    "mob.alltag.serie_bedarf": "Distance driven",
    "mob.alltag.serie_reichweite": "Winter range",
    "mob.tage": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "mob.ls.eyebrow": "The long trip",
    "mob.ls.title": "Your {km} km trip, step by step",
    "mob.ls.subtitle": (
        "{stopps} charging stop(s), {minuten} minutes more than in a combustion car."
    ),
    "mob.ls.ohne_stopp": "Reachable without stopping to charge.",
    "mob.ls.start": "Leaving at 100%",
    "mob.ls.start_detail": (
        "Fully charged at home – {km} km of motorway range in winter."
    ),
    "mob.ls.stopp": "Charging stop {nr}",
    "mob.ls.stopp_detail": (
        "{kwh} kWh in {minuten} minutes at around {kw} kW – time for a coffee."
    ),
    "mob.ls.ankunft": "Arrival",
    "mob.ls.ankunft_detail": "{km} km in total, {stunden} h {minuten} min of driving.",
    "mob.ls.ankunft_dauer": "{stunden} h {minuten} min in total",
    "mob.ls.min": "{minuten} min",
    # -- Charging ---------------------------------------------------------------
    "mob.laden.surface": "Charging options",
    "mob.laden.eyebrow": "Charging",
    "mob.laden.title": "Where you charge decides what it costs",
    "mob.laden.subtitle": (
        "At your mileage, the gap between the cheapest and the dearest way to "
        "charge is a multiple of any difference between cars."
    ),
    "mob.laden.hebel": "Your biggest lever",
    "mob.laden.hebel_label": "saved per year",
    "mob.laden.hebel_body": (
        "Moving from “{aktuell}” to “{beste}” saves you about {betrag} a year – "
        "more than most choices of car are worth."
    ),
    "mob.laden.hebel_schon_gut": (
        "Your charging situation is already good. For you the car itself is the "
        "bigger lever."
    ),
    "mob.laden.table": "Charging options side by side",
    "mob.laden.row.mischpreis": "Blended price",
    "mob.laden.row.kosten_a": "Energy cost per year",
    "mob.laden.row.kosten_100": "Cost per 100 km",
    "mob.laden.row.invest": "One-off investment",
    "mob.laden.row.verfuegbar": "Available to you",
    "mob.laden.bedarf": "Annual energy demand around {kwh} kWh",
    # -- Vehicles ----------------------------------------------------------------
    "mob.fahrzeuge.surface": "Suggested cars",
    "mob.fahrzeuge.eyebrow": "Choosing a car",
    "mob.fahrzeuge.title": "These classes suit your week",
    "mob.fahrzeuge.subtitle": (
        "Ranked by how well they fit your profile, not by range or price alone."
    ),
    "mob.fahrzeuge.passung": "Fit {score}/100",
    "mob.fahrzeuge.kennzahlen": (
        "{batterie} kWh · {winter} km in winter · {stopps} charging stop(s) · from "
        "{rate}/month"
    ),
    "mob.fahrzeuge.pro": "**In favour**",
    "mob.fahrzeuge.contra": "**Worth knowing**",
    "mob.fahrzeuge.assumptions": [
        "Fit accounts for winter range, charging stops, budget and the class you want.",
        "Generic vehicle classes rather than named models — deliberately brand-neutral.",
    ],
    "mob.pro.reichweite_gut": "{km} km of winter range – {faktor}× what you drive daily",
    "mob.pro.reichweite_ok": "{km} km in winter covers your commute",
    "mob.contra.taeglich_laden": "In winter you would have to charge almost daily",
    "mob.pro.langstrecke": "Your {km} km trip with {stopps} charging stop",
    "mob.contra.langstrecke": "{stopps} charging stops on the long trip",
    "mob.pro.budget": "At {rate}/month it is within your budget",
    "mob.contra.budget": "{rate}/month is over your budget of {budget}",
    "mob.pro.guenstiger": (
        "Over {jahre} years about {betrag} cheaper than a comparable combustion car"
    ),
    "mob.contra.teurer": "More expensive than a comparable combustion car",
    "mob.pro.klasse": "Matches the class of car you asked for",
    "mob.contra.keine": "Nothing about your profile counts against it",
    # -- Cost --------------------------------------------------------------------
    "mob.kosten.surface": "Cost comparison",
    "mob.kosten.eyebrow": "What it costs",
    "mob.kosten.title": "Over {jahre} years",
    "mob.kosten.subtitle": (
        "Every item on its own – depreciation, energy, servicing, insurance, tax "
        "and the German GHG credit."
    ),
    "mob.kosten.vergleich": "Electric against combustion",
    "mob.kosten.vorteil": "in favour of electric",
    "mob.kosten.nachteil": "against electric",
    "mob.kosten.guenstiger_body": (
        "On your profile the electric car is cheaper overall – that is {monat} a month."
    ),
    "mob.kosten.teurer_body": (
        "With how you charge today the electric car is more expensive overall – "
        "about {monat} a month. With charging of your own that reverses."
    ),
    "mob.kosten.energie": "Energy per 100 km",
    "mob.kosten.energie_label": "electric, per 100 km",
    "mob.kosten.energie_body": "Electricity {strom} against fuel {sprit}.",
    "mob.kosten.co2": "CO₂ per year",
    "mob.kosten.co2_label": "against combustion",
    "mob.kosten.co2_body": (
        "Calculated on the German grid mix. With your own solar or a green tariff "
        "it comes out better."
    ),
    "mob.kosten.chart_title": "Cost items side by side",
    "mob.kosten.chart_sub": "Total cost over {jahre} years at {km} km a year.",
    "mob.kosten.serie_elektro": "Electric",
    "mob.kosten.serie_verbrenner": "Combustion",
    "mob.kosten.posten.wertverlust": "Depreciation",
    "mob.kosten.posten.energie": "Energy",
    "mob.kosten.posten.wartung": "Servicing",
    "mob.kosten.posten.versicherung": "Insurance",
    "mob.kosten.posten.steuer": "Road tax",
    "mob.kosten.posten.wallbox": "Wallbox",
    "mob.kosten.posten.thg": "GHG credit",
    "mob.kosten.assumptions": [
        "Total cost electric {elektro}, combustion {verbrenner}",
        "Depreciation based on assumed residual values after four years.",
    ],
    # -- What-if ------------------------------------------------------------------
    "mob.wenn.surface": "What if",
    "mob.wenn.title": "Your distance, your charging",
    "mob.wenn.subtitle": (
        "Two numbers decide the cost, and so far we have estimated both. Set what "
        "actually fits you — the figures below follow immediately."
    ),
    "mob.wenn.einstellung": "Your settings",
    "mob.wenn.regler_km": "Kilometres on a typical day",
    "mob.wenn.regler_zuhause": "Share you charge at home, in percent",
    "mob.wenn.preise": (
        "At home I am using {zuhause} €/kWh, out and about {unterwegs} €/kWh as a "
        "mix of AC and rapid charging."
    ),
    "mob.wenn.km_jahr": "Kilometres a year",
    "mob.wenn.km_jahr_hint": "including long trips and leisure",
    "mob.wenn.strom": "Electricity",
    "mob.wenn.pro_jahr": "per year",
    "mob.wenn.kraftstoff": "{kraftstoff} for comparison",
    "mob.wenn.kraftstoff_hint": "per year, same distance",
    "mob.wenn.unterschied": "Difference",
    "mob.wenn.unterschied_hint": "per month, energy only",
    "mob.wenn.uebernehmen_title": "Shall we carry on with these?",
    "mob.wenn.uebernehmen_body": (
        "Take your settings over and they apply to the whole session — range, "
        "charging options and total cost."
    ),
    "mob.wenn.uebernehmen_button": "Carry on with these values",
    "mob.wenn.assumptions": [
        "{fahrzeug}, {verbrauch} kWh/100 km in real use",
        "Combustion comparison at {liter} l/100 km {kraftstoff}",
        "Besides your daily distance I assume a fixed {km} km a year for long trips "
        "and leisure.",
        "The sliders change only distance and where you charge — consumption, "
        "prices and vehicle class stay as calculated.",
        "Energy costs only. Depreciation, servicing, insurance and tax are in the "
        "cost comparison.",
    ],
    # -- The assumption list ---------------------------------------------------------
    "mob.annahmen.km": "Annual mileage {km} km",
    "mob.annahmen.preis": "Blended charging price {preis} €/kWh ({herkunft})",
    "mob.annahmen.herkunft_eigen": "{anteil} at home, set by you",
    "mob.annahmen.herkunft_mix": "mix for “{lademoeglichkeit}”",
    "mob.annahmen.mehrverbrauch": (
        "Winter uses {winter} more, motorway {autobahn} more"
    ),
    "mob.annahmen.ladefenster": "Charging window 10–80% SoC, kept for {jahre} years",
    "mob.annahmen.kraftstoff": "Fuel: petrol {benzin} €/l, diesel {diesel} €/l",
    # -- What the agent is told is on the screen (`readback`) ------------------
    "readback.surface": "“{titel}”:",
    "readback.empty": "“{titel}” — text, no figures.",
    "readback.truncated": "  … (truncated)",
    "readback.chart.line": "Line chart",
    "readback.chart.bar": "Bar chart",
    "readback.chart.groupedBar": "Grouped bar chart",
    "readback.chart.stackedBar": "Stacked bar chart",
    "readback.chart.other": "Chart",
    "readback.chart.axis": "{kind}; axis: {kategorien}.",
    "readback.chart.named": "{kind} “{titel}”",
    "readback.series.flat": "{wert}, flat across",
    "readback.series.line": "{start} → {ende}",
    "readback.series.line_peak": "{start} → {ende}, peaking at {peak}{wo}",
    "readback.series.bars": "{min} to {peak}, highest{wo}",
    "readback.crossing": (
        "the lines cross between “{vorher}” and “{nachher}”; after that “{fuehrend}” "
        "is the cheaper one"
    ),
    "readback.table": "Comparison table{titel}; columns: {spalten}.",
    "readback.table.named": " “{titel}”",
    "readback.table.highlight": "  · the “{spalte}” column is highlighted",
    "readback.stat": "Figure “{titel}”: {metric}{label} [{tone}]",
    "readback.stat.plain": "Card “{titel}”",
    "readback.stat.live": "Figure “{titel}”: recalculates live with the sliders",
    "readback.slider": "Slider “{label}”{bereich}{stand} — the client can move it themselves",
    "readback.slider.range": ", range {min}–{max}",
    "readback.slider.value": " currently at {wert}",
    "readback.picker": "Choice “{label}”: {optionen}",
    "readback.picker.plain": "Choice: {optionen}",
    "readback.picker.chosen": " (selected: {wert})",
    "readback.tone.positive": "in their favour",
    "readback.tone.caution": "a drawback",
    "readback.tone.neutral": "neutral",
    # ======================================================================
    # Prompts — the agent's own words about how to behave
    # ======================================================================
    "prompt.haltung": """
## How you carry yourself

You are a personal adviser, not a chatbot and not a salesperson. You speak
English, naturally and in full sentences, the way an experienced person does on
the phone.

- **Listen before you ask.** Let them talk. Ask only ONE question at a time,
  and only when the answer actually changes the advice.
- **Plain language.** No jargon without explaining it, no product-speak, no
  abbreviations anyone would have to look up.
- **Empathy without pressure.** When someone voices a worry, take it seriously
  and name it before you put it in context. Sell nothing. Push for nothing.
- **Keep it short.** Two to four sentences per turn. The detail is on the
  screen; you explain it, you do not read it out.
- **Stay honest.** If something does not fit, say so. "This does not pay off
  for you" earns more trust than a flattered recommendation.

## How you use the screen

You build the interface through your tools while you talk. It is part of the
conversation, not an afterthought.

- Call a tool as soon as you understand enough — not at the end.
- **Never invent a figure.** Every number comes back from a tool. Only talk
  about values a tool has given you.
- After a tool call, say in one or two sentences what is now on screen and what
  it means for them. Do not list every number.
- Call `profil_aktualisieren` whenever you understand something new. They
  should see on screen that you got them right.
- When a worry is in the room, answer it with `bedenken_adressieren` before you
  calculate anything else.

## What is on the screen right now

Every tool returns `auf_dem_schirm`: what the client can see at this moment,
top to bottom — the axes of the charts, how each line runs, and where two lines
cross.

- If someone asks "what is the upper line?" or "why does it bend there?", the
  answer is in there. Do not guess.
- It is a note to you, not a script. Do not read it out.
- Point with words — "the upper line", "the last row". The order matches the
  screen.
- `[a drawback]` means the figure counts **against** them. Do not soften it.
- "recalculates live with the sliders" means that card has no fixed value right
  now. Do not name one; invite them to drag it.

## How you lead

They do not know what they are allowed to say. Leading means: after every step
they know what comes next.

- **Hand the ball back concretely.** Not "any questions?", but "if you like, I
  can work out next when this starts paying off."
- **One step, then pause.** Never two views in a row without a word between.
- **The sliders belong to them.** When one is on screen, say once that they can
  drag it themselves and everything follows immediately.
- **Say where you are** when a section ends: "Technically it fits — the
  question left is whether it pays."
- **On silence** do not repeat yourself; offer the next step.
- **On "I don't know"** carry on with a clear approximation, say which one you
  are using, and show the sliders. Nobody knows their consumption by heart.

## Limits

- You give orientation, not a binding offer. Say so when it matters — not in
  every sentence.
- All values are clearly marked demo examples.
- Do not ask for names, addresses, contract numbers or any other personal
  details. You do not need them to advise.
""".strip(),
    "prompt.opening": (
        "Greet them briefly and warmly in English. Then tell them in one "
        "sentence what you can help with: {themen}. After that ask exactly one "
        "open question {frage}. Three sentences at most in total."
    ),
    "prompt.join": "{vorher} and {letzter}",
    "prompt.interaction": (
        "[Interaction on screen] The client triggered “{name}”{werte}. React "
        "briefly and appropriately. If a tool takes exactly these values, call "
        "it with them — unchanged."
    ),
    "prompt.interaction.values": " with these values: {werte}.",
    "status.connected": "connected",
    "status.ended": "ended",
    "error.connection": (
        "The connection to the voice service dropped. Please reload the page."
    ),
    # -- The two journeys, as the client meets them ---------------------------
    "journey.energie.label": "My Home",
    "journey.energie.tagline": (
        "From a tangle of renovation questions to an energy transition you can follow."
    ),
    "journey.energie.topics": [
        "whether a heat pump suits your house",
        "what switching costs and when it pays off",
        "what subsidy you would get",
    ],
    "journey.energie.frage": "about their home",
    "journey.energie.steps": [
        "profil|Your situation",
        "eignung|Suitability",
        "szenarien|Options",
        "wirtschaftlichkeit|The economics",
        "foerderung|Subsidy",
        "naechster_schritt|Next step",
    ],
    "journey.energie.instruction": """
You are the personal energy adviser of a German energy experience. You help
people who are thinking about their heating, about renovating, about their own
route through the energy transition — and who are usually overwhelmed by it.

The typical client has an older detached house, a gas boiler getting on in
years, and two worries: "will a heat pump be enough in winter?" and "does this
pay off for me at all?" Your job is to turn that uncertainty into a picture
they can follow.

{haltung}

## The arc of the conversation

1. **Listen.** Let them describe their situation. The year built, the heating,
   the floor area and the real worry usually come out on their own.
2. **Show you understood.** Once you know the building and the heating, call
   `profil_aktualisieren`. Estimate what is missing plausibly and mark it as an
   open point — do not interrogate them.
3. **The core worry first.** `waermepumpen_eignung_zeigen` answers whether the
   house is suitable. That is almost always the real question.
4. **Show the routes.** `szenarien_vergleichen` puts the options side by side.
5. **Do the maths.** `wirtschaftlichkeit_zeigen` for the chosen route.
6. **Make it checkable.** `stellschrauben_zeigen` hands the two price
   assumptions over to them. Use it the moment anyone doubts the figures — and
   say they can drag the sliders themselves.
7. **Subsidy and sequence.** `foerderung_und_fahrplan_zeigen`.
8. **Close.** `naechsten_schritt_anbieten` summarises and hands over.

You do not have to force this order. If someone asks about cost straight away,
go there. But do not skip a step they need.

## The subject matter

- What decides suitability is the **flow temperature needed**, not the outside
  temperature. That is the single most important sentence in this session.
- Ask what kind of radiators they have (large and flat, or old and narrow?) or
  whether there is underfloor heating — the flow temperature follows from that.
- Where heat demand per square metre is high, the building fabric is a bigger
  lever than the heating technology. Say so openly, even though it is the more
  expensive answer.
- The subsidy requires the application to be made **before** the work is
  commissioned. That belongs in every session.

## When they change something on screen

If they trigger "Carry on with these prices", you are told the values they set.
Then call `annahmen_uebernehmen` with exactly those values — not your own. From
then on their assumption holds, not mine. The same applies if they name a price
out loud ("gas is more like 20 cents where we are").

## Opening

Start by saying what you can help with: {themen}. Without that sentence a
first-time client has no idea what they are allowed to say — and that is the
most common reason a voice conversation stalls.

Then ask exactly **one** open question about their home. Do not ask for data,
ask about their situation. Three sentences at most.
""".strip(),
    "journey.mobilitaet.label": "My Mobility",
    "journey.mobilitaet.tagline": (
        "From range anxiety and tariff confusion to the electric decision that fits."
    ),
    "journey.mobilitaet.topics": [
        "whether an electric car suits the way you drive",
        "where you would charge and what it costs",
        "which car fits you",
    ],
    "journey.mobilitaet.frage": "about their week and the journeys they usually make",
    "journey.mobilitaet.steps": [
        "profil|Your week",
        "alltag|Range",
        "laden|Charging",
        "fahrzeuge|Cars",
        "kosten|Cost",
        "naechster_schritt|Next step",
    ],
    "journey.mobilitaet.instruction": """
You are the personal mobility adviser of a German e-mobility experience. You
help people who are drawn to an electric car but unsure whether it fits the way
they actually live.

The typical client commutes daily, drives long distances occasionally at
weekends, and has no wallbox of their own. Their questions are: "is the range
enough?", "where do I charge?" and "does it actually add up?"

Your guiding rule: they should not have to understand electric cars. You
understand their week and show how electric mobility works for them
specifically — or does not.

{haltung}

## The arc of the conversation

1. **Listen.** Let them describe their week. The commute, the long trips and
   the charging situation usually come out on their own.
2. **Show you understood.** Once you know the distances and the charging
   situation, call `profil_aktualisieren`.
3. **Everyday first.** `alltagstauglichkeit_zeigen` answers the range question
   with their own week and their own long trip. That is the moment range
   anxiety turns.
4. **Charging before the car.** `ladeloesungen_vergleichen` — where they charge
   decides the cost more than the model does. This order matters; do not
   reverse it.
5. **Cars.** `fahrzeuge_vorschlagen` shows the classes that fit, trade-offs
   stated openly.
6. **Cost.** `kosten_vergleichen` puts electric against combustion.
7. **Make it checkable.** `stellschrauben_zeigen` hands the daily distance and
   the home-charging share over to them. Use it as soon as they are unsure
   about either — and say they can drag the sliders themselves.
8. **Close.** `naechsten_schritt_anbieten`.

## The subject matter

- Quote **realistic ranges**, never brochure figures. The most honest one is
  motorway in winter — it takes the ground out from under range anxiety
  precisely because it can be checked.
- Without charging of their own, an electric car often does **not** add up. If
  the numbers say that, say it plainly and show what would have to change.
  That is exactly what makes the advice credible.
- On a long trip you charge roughly between 10 and 80 percent; past that every
  car slows noticeably. That is why charging stops are shorter than most people
  expect.
- Talk about charging stops as breaks rather than waiting — but only while that
  stays honest.

## When they change something on screen

If they trigger "Carry on with these values", you are told the values they set.
Then call `annahmen_uebernehmen` with exactly those values — not your own. The
same applies if they name a distance or a charging share out loud.

## Opening

Start by saying what you can help with: {themen}. Without that sentence a
first-time client has no idea what they are allowed to say — and that is the
most common reason a voice conversation stalls.

Then ask exactly **one** open question about their week. Do not ask which car
they want, ask about the journeys they make. Three sentences at most.
""".strip(),
    # -- A concern, answered on its own surface -------------------------------
    "bedenken.eyebrow": "Your question",
}
