"""Typed builders for the components the agent is allowed to emit.

Everything the agent can render goes through this module. The renderer's
Adaptive Advisory catalog is a superset of two things:

* the **basic catalog** shipped with ``@a2ui/react/v0_9`` (Row, Column, Text,
  Button, Divider …), and
* the **advisory building blocks** defined by this demo — the approved set from
  the briefing (Karten, Vergleich, Szenario, Diagramm, Timeline, Empfehlung,
  Call-to-action).

Both resolve from the surface's catalog. A2UI v0.9 has no per-component
``catalogId`` override, so components carry no catalog id of their own.

Keeping the builders here means an invalid component shape is a Python error at
compose time rather than a blank card in front of a client.
"""

from __future__ import annotations

from typing import Any, Literal, Sequence

Component = dict[str, Any]
Dynamic = Any  # a literal, {"path": ...} binding, or {"call": ..., "args": ...}


def _clean(component: Component) -> Component:
    """Drops ``None`` values so the renderer's strict schemas stay happy."""
    return {k: v for k, v in component.items() if v is not None}


# ---------------------------------------------------------------------------
# Basic catalog (layout + text)
# ---------------------------------------------------------------------------


def column(
    component_id: str,
    children: Sequence[str],
    *,
    align: str | None = None,
    justify: str | None = None,
    weight: float | None = None,
) -> Component:
    return _clean(
        {
            "id": component_id,
            "component": "Column",
            "children": list(children),
            "align": align,
            "justify": justify,
            "weight": weight,
        }
    )


def row(
    component_id: str,
    children: Sequence[str],
    *,
    align: str | None = None,
    justify: str | None = None,
    weight: float | None = None,
) -> Component:
    return _clean(
        {
            "id": component_id,
            "component": "Row",
            "children": list(children),
            "align": align,
            "justify": justify,
            "weight": weight,
        }
    )


def text(
    component_id: str,
    value: Dynamic,
    *,
    variant: Literal["caption", "body"] | None = None,
    weight: float | None = None,
) -> Component:
    """A Text component. The renderer treats the value as Markdown."""
    return _clean(
        {
            "id": component_id,
            "component": "Text",
            "text": value,
            "variant": variant,
            "weight": weight,
        }
    )


def divider(component_id: str, *, axis: str = "horizontal") -> Component:
    return {
        "id": component_id,
        "component": "Divider",
        "axis": axis,
    }


def button(
    component_id: str,
    child_id: str,
    *,
    event_name: str,
    context: dict[str, Dynamic] | None = None,
    variant: Literal["default", "primary", "borderless"] = "default",
) -> Component:
    """A Button whose action is dispatched back to the agent as an event."""
    return {
        "id": component_id,
        "component": "Button",
        "child": child_id,
        "variant": variant,
        "action": {"event": {"name": event_name, "context": context or {}}},
    }


# ---------------------------------------------------------------------------
# Adaptive Advisory catalog (the approved advisory building blocks)
# ---------------------------------------------------------------------------


def bind(path: str) -> dict[str, str]:
    """A data binding. The renderer resolves it against the surface data model.

    Using a real binding rather than a literal is what lets the agent patch a
    surface with a single ``updateDataModel`` message later on.
    """
    return {"path": path}


def advisory_header(
    component_id: str,
    *,
    title: Dynamic,
    subtitle: Dynamic | None = None,
    eyebrow: Dynamic | None = None,
    icon: str | None = None,
) -> Component:
    """Baustein: section header that frames what the client is looking at."""
    return _clean(
        {
            "id": component_id,
            "component": "AdvisoryHeader",
            "title": title,
            "subtitle": subtitle,
            "eyebrow": eyebrow,
            "icon": icon,
        }
    )


def profile_summary(
    component_id: str,
    *,
    title: Dynamic,
    facts: Dynamic,
    open_points: Dynamic | None = None,
    note: Dynamic | None = None,
) -> Component:
    """Baustein: "sichtbare Zusammenfassung des Verstandenen".

    Bound to the data model so it can be patched with ``updateDataModel`` on
    every turn without re-sending the layout.
    """
    return _clean(
        {
            "id": component_id,
            "component": "ProfileSummary",
            "title": title,
            "facts": facts,
            "openPoints": open_points,
            "note": note,
        }
    )


def insight_card(
    component_id: str,
    *,
    title: Dynamic,
    body: Dynamic,
    tone: Literal["positive", "neutral", "caution"] = "neutral",
    icon: str | None = None,
    metric: Dynamic | None = None,
    metric_label: Dynamic | None = None,
    weight: float | None = None,
) -> Component:
    """Baustein "Karte": one idea, optionally with a headline metric."""
    return _clean(
        {
            "id": component_id,
            "component": "InsightCard",
            "title": title,
            "body": body,
            "tone": tone,
            "icon": icon,
            "metric": metric,
            "metricLabel": metric_label,
            "weight": weight,
        }
    )


def comparison_table(
    component_id: str,
    *,
    title: Dynamic | None = None,
    columns: Dynamic,
    rows: Dynamic,
    highlight: Dynamic | None = None,
) -> Component:
    """Baustein "Vergleich": options as columns, criteria as rows."""
    return _clean(
        {
            "id": component_id,
            "component": "ComparisonTable",
            "title": title,
            "columns": columns,
            "rows": rows,
            "highlight": highlight,
        }
    )


def scenario_selector(
    component_id: str,
    *,
    title: Dynamic | None = None,
    scenarios: Dynamic,
    selected_path: str,
    event_name: str = "szenario_gewaehlt",
) -> Component:
    """Baustein "Szenario": selectable cards.

    ``selected`` is a two-way binding: picking a card writes the id back into
    the data model, so anything else bound to that path — the comparison table
    highlight, for instance — follows along without another round trip to the
    agent. The action still fires so the agent can react in speech.
    """
    return _clean(
        {
            "id": component_id,
            "component": "ScenarioSelector",
            "title": title,
            "scenarios": scenarios,
            "selected": bind(selected_path),
            "action": {
                "event": {
                    "name": event_name,
                    "context": {"szenarioId": bind(selected_path)},
                }
            },
        }
    )


def metric_chart(
    component_id: str,
    *,
    title: Dynamic | None = None,
    subtitle: Dynamic | None = None,
    chart_type: Literal["bar", "groupedBar", "stackedBar", "line", "donut"] = "bar",
    series: Dynamic,
    categories: Dynamic,
    unit: Dynamic | None = None,
    value_format: Literal["number", "currency", "percent"] = "number",
) -> Component:
    """Baustein "Diagramm": the numeric backbone of the advice."""
    return _clean(
        {
            "id": component_id,
            "component": "MetricChart",
            "title": title,
            "subtitle": subtitle,
            "chartType": chart_type,
            "series": series,
            "categories": categories,
            "unit": unit,
            "valueFormat": value_format,
        }
    )


def timeline(
    component_id: str,
    *,
    title: Dynamic | None = None,
    steps: Dynamic,
) -> Component:
    """Baustein "Timeline": what happens when, in which order."""
    return _clean(
        {
            "id": component_id,
            "component": "Timeline",
            "title": title,
            "steps": steps,
        }
    )


def recommendation(
    component_id: str,
    *,
    title: Dynamic,
    summary: Dynamic,
    fit_score: Dynamic | None = None,
    fit_label: Dynamic | None = None,
    pros: Dynamic | None = None,
    cons: Dynamic | None = None,
    rank: Dynamic | None = None,
    weight: float | None = None,
) -> Component:
    """Baustein "Empfehlung": a ranked option with its trade-offs shown openly."""
    return _clean(
        {
            "id": component_id,
            "component": "Recommendation",
            "title": title,
            "summary": summary,
            "fitScore": fit_score,
            "fitLabel": fit_label,
            "pros": pros,
            "cons": cons,
            "rank": rank,
            "weight": weight,
        }
    )


def next_step_cta(
    component_id: str,
    *,
    title: Dynamic,
    body: Dynamic | None = None,
    primary_label: Dynamic,
    primary_event: str,
    primary_context: dict[str, Dynamic] | None = None,
    secondary_label: Dynamic | None = None,
    secondary_event: str | None = None,
    secondary_context: dict[str, Dynamic] | None = None,
) -> Component:
    """Baustein "Call-to-action": the handover into a human or digital process."""
    component: Component = {
        "id": component_id,
        "component": "NextStepCTA",
        "title": title,
        "primaryLabel": primary_label,
        "primaryAction": {
            "event": {"name": primary_event, "context": primary_context or {}}
        },
    }
    if body is not None:
        component["body"] = body
    if secondary_label is not None and secondary_event is not None:
        component["secondaryLabel"] = secondary_label
        component["secondaryAction"] = {
            "event": {"name": secondary_event, "context": secondary_context or {}}
        }
    return component


def assumption_note(
    component_id: str,
    *,
    title: Dynamic | None = None,
    assumptions: Dynamic,
    source: Dynamic | None = None,
    as_of: Dynamic | None = None,
) -> Component:
    """Baustein: "Annahmen und Datenquellen sichtbar machen".

    Required on every surface that shows a number the client might act on.
    """
    return _clean(
        {
            "id": component_id,
            "component": "AssumptionNote",
            "title": title,
            "assumptions": assumptions,
            "source": source,
            "asOf": as_of,
        }
    )
