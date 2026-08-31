"""What is on the client's screen, in words the agent can use.

The composers decide what a surface looks like, which is the point of the
architecture — but it left the agent talking about a picture it could not see.
It knew `break_even_jahre` because the tool returned it; it did not know that
the chart draws four lines, that the client's current path is the second one,
or that the two lines cross between year ten and year fifteen. So "was zeigt
die obere Linie?" had no answer, and "sehen Sie den Knick" was a guess.

The fix is not to write a second description by hand next to every composer —
two descriptions of one picture drift, and the day they disagree the agent is
confidently wrong about something the client is looking at. This reads the
*composed tree itself*, after the composer is done with it, and resolves the
same bindings the renderer resolves. One source, so the words and the pixels
cannot disagree.

What comes out is compact German, meant for a tool result rather than a
person: the agent reads it and then says one sentence of its own.
"""

from __future__ import annotations

from typing import Any

from ..texts import Texts
from .surface import Surface

#: Enough for the largest surface in the demo, and a ceiling so a future one
#: cannot quietly push the conversation out of context.
MAX_CHARS = 1800




# ---------------------------------------------------------------------------
# Resolving what the renderer resolves
# ---------------------------------------------------------------------------


def _resolve(value: Any, data: dict[str, Any]) -> Any:
    """Follows a `{"path": "/x/y"}` binding into the surface's data model.

    Deliberately partial: bindings inside `List` templates are relative to the
    element and there is no element here, and client-side function calls only
    have values once a slider has been dragged. Both come back as None and the
    caller leaves them out rather than guessing.
    """
    if not isinstance(value, dict):
        return value
    if "path" not in value:
        return None

    path = value["path"]
    if not isinstance(path, str) or not path.startswith("/"):
        return None

    node: Any = data
    for segment in path.strip("/").split("/"):
        if not segment:
            continue
        if not isinstance(node, dict) or segment not in node:
            return None
        node = node[segment]
    return node


def _text(value: Any, data: dict[str, Any]) -> str | None:
    resolved = _resolve(value, data)
    if resolved is None or isinstance(resolved, (dict, list)):
        return None
    text = str(resolved).strip()
    return text or None


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


# ---------------------------------------------------------------------------
# The components worth describing
# ---------------------------------------------------------------------------


def _chart(t: Texts, component: dict[str, Any], data: dict[str, Any]) -> str | None:
    categories = _resolve(component.get("categories"), data)
    series = _resolve(component.get("series"), data)
    if not isinstance(categories, list) or not isinstance(series, list) or not series:
        return None

    chart_type = str(component.get("chartType") or "bar")
    kind = t.get(f"readback.chart.{chart_type}") or t("readback.chart.other")

    title = _text(component.get("title"), data)
    unit = _text(component.get("unit"), data)
    head = t("readback.chart.named", kind=kind, titel=title) if title else kind
    labels = [str(c) for c in categories]

    lines = [t("readback.chart.axis", kind=head, kategorien=", ".join(labels))]

    is_line = component.get("chartType") == "line"
    plotted: list[tuple[str, list[float]]] = []
    for entry in series:
        if not isinstance(entry, dict):
            continue
        values = [v for v in (_number(v) for v in entry.get("werte", [])) if v is not None]
        if not values:
            continue
        label = str(entry.get("label") or entry.get("id") or "?")
        plotted.append((label, values))
        lines.append(f"  · {label}: {_shape(t, values, labels, unit, as_line=is_line)}")

    if not plotted:
        return None

    if is_line:
        crossing = _crossing(t, plotted, labels)
        if crossing:
            lines.append(f"  · {crossing}")
    return "\n".join(lines)


def _shape(
    t: Texts, values: list[float], labels: list[str], unit: str | None, *, as_line: bool
) -> str:
    """One series in a phrase, said the way that kind of chart is read.

    A line is read as a movement, so its ends carry the meaning. Bars are read
    as a comparison between categories, so the tallest one does — and naming
    only its height ("Höchstwert 5.712 kWh") leaves out the half a client is
    actually pointing at, which is *which month* that is.
    """
    decimals = _decimals(values)

    def fmt(value: float) -> str:
        # The renderer formats a euro axis through its own currency formatter,
        # which puts the sign where the locale puts it — ahead of the figure in
        # English. Appending "€" here would have the agent describing the chart
        # differently from how the client sees it.
        if unit == "€":
            return t.euro(value, decimals=decimals)
        return t.num(value, decimals=decimals, unit=unit)

    if len(values) == 1:
        return fmt(values[0])

    # A flat series is a reference line — the winter range drawn across the
    # week, say. It has no shape to describe and no tallest bar; a range from
    # a value to itself reads as broken.
    if min(values) == max(values):
        return t("readback.series.flat", wert=fmt(values[0]))

    peak = max(range(len(values)), key=lambda i: values[i])
    where = f" ({labels[peak]})" if peak < len(labels) else ""

    if as_line:
        # A curve that only rises peaks at its own endpoint, and saying so
        # twice is noise. Worth a phrase only where it turns.
        if peak in (len(values) - 1, 0):
            return t("readback.series.line", start=fmt(values[0]), ende=fmt(values[-1]))
        return t(
            "readback.series.line_peak",
            start=fmt(values[0]),
            ende=fmt(values[-1]),
            peak=fmt(values[peak]),
            wo=where,
        )
    # Only plotted points, never a total: a sum is a figure the client cannot
    # find anywhere on the chart, and stating one would be the agent asserting
    # something the picture does not say.
    return t(
        "readback.series.bars", min=fmt(min(values)), peak=fmt(values[peak]), wo=where
    )


def _decimals(values: list[float]) -> int:
    """Whole numbers stay whole; anything fractional gets one place.

    Matched to the composers, which round to a tenth wherever they show a
    fraction at all. Reading back more precision than the card shows would put
    a number in the agent's mouth that is not on the screen.
    """
    return 0 if all(v == int(v) for v in values) else 1


def _crossing(
    t: Texts, plotted: list[tuple[str, list[float]]], labels: list[str]
) -> str | None:
    """Where the first two lines swap places — the thing a client points at.

    Reported as the interval between two plotted points, never as an
    interpolated year. The precise break-even comes from `calc.amortisation`
    and is in the same tool result; a second number derived here would
    eventually disagree with it by a year, in front of the client.
    """
    if len(plotted) < 2:
        return None
    (first_label, first), (second_label, second) = plotted[0], plotted[1]
    if len(first) != len(second) or len(first) < 2:
        return None

    for index in range(1, min(len(first), len(labels))):
        before = first[index - 1] - second[index - 1]
        after = first[index] - second[index]
        if before == 0 or (before > 0) == (after > 0):
            continue
        ahead = second_label if after > 0 else first_label
        return t(
            "readback.crossing",
            vorher=labels[index - 1],
            nachher=labels[index],
            fuehrend=ahead,
        )
    return None


def _table(t: Texts, component: dict[str, Any], data: dict[str, Any]) -> str | None:
    columns = _resolve(component.get("columns"), data)
    rows = _resolve(component.get("rows"), data)
    if not isinstance(columns, list) or not isinstance(rows, list):
        return None

    headers = [str(c.get("label", c.get("id", "?"))) for c in columns if isinstance(c, dict)]
    if not headers:
        return None

    title = _text(component.get("title"), data)
    highlight = _text(component.get("highlight"), data)
    marked = next(
        (
            str(c.get("label"))
            for c in columns
            if isinstance(c, dict) and highlight and c.get("id") == highlight
        ),
        None,
    )

    lines = [
        t(
            "readback.table",
            titel=t("readback.table.named", titel=title) if title else "",
            spalten=", ".join(headers),
        )
    ]
    if marked:
        lines.append(t("readback.table.highlight", spalte=marked))
    for row in rows:
        if not isinstance(row, dict):
            continue
        values = [str(v) for v in row.get("werte", [])]
        if values:
            lines.append(f"  · {row.get('label', '?')}: {' | '.join(values)}")
    return "\n".join(lines)


def _stat(t: Texts, component: dict[str, Any], data: dict[str, Any]) -> str | None:
    title = _text(component.get("title"), data)
    if not title:
        return None

    metric = _text(component.get("metric"), data)
    if not metric:
        # The what-if cards compute their figure in the browser from whatever
        # the sliders currently say, so there is no value to read back here —
        # and saying one would be a guess at where the client left the slider.
        # What the agent needs is that the card is live, so it invites the
        # client to drag instead of announcing a number.
        if _is_expression(component.get("metric")):
            return t("readback.stat.live", titel=title)
        return t("readback.stat.plain", titel=title)

    label = _text(component.get("metricLabel"), data)
    tone = str(_text(component.get("tone"), data) or "neutral")
    return t(
        "readback.stat",
        titel=title,
        metric=metric,
        label=f" {label}" if label else "",
        tone=t.get(f"readback.tone.{tone}") or t("readback.tone.neutral"),
    )


def _is_expression(value: Any) -> bool:
    """A client-side function call, evaluated in the browser and not here."""
    return isinstance(value, dict) and "path" not in value


def _slider(t: Texts, component: dict[str, Any], data: dict[str, Any]) -> str | None:
    label = _text(component.get("label"), data)
    value = _number(_resolve(component.get("value"), data))
    if not label:
        return None
    span = ""
    low, high = _number(component.get("min")), _number(component.get("max"))
    if low is not None and high is not None:
        span = t("readback.slider.range", min=t.num(low), max=t.num(high))
    now = t("readback.slider.value", wert=t.num(value)) if value is not None else ""
    return t("readback.slider", label=label, bereich=span, stand=now)


def _picker(t: Texts, component: dict[str, Any], data: dict[str, Any]) -> str | None:
    label = _text(component.get("label"), data)
    options = _resolve(component.get("options"), data)
    if not isinstance(options, list):
        return None
    names = [str(o.get("label")) for o in options if isinstance(o, dict) and o.get("label")]
    if not names:
        return None
    chosen = _text(component.get("value"), data)
    joined = ", ".join(names)
    head = (
        t("readback.picker", label=label, optionen=joined)
        if label
        else t("readback.picker.plain", optionen=joined)
    )
    return head + (t("readback.picker.chosen", wert=chosen) if chosen else "")


_DESCRIBERS = {
    "MetricChart": _chart,
    "ComparisonTable": _table,
    "StatCard": _stat,
    "Slider": _slider,
    "ChoicePicker": _picker,
}


# ---------------------------------------------------------------------------
# The whole surface
# ---------------------------------------------------------------------------


def describe(surface: Surface, t: Texts) -> str:
    """Reads back the surface in the order the client's eye meets it.

    Document order, because that is the order the composer laid out and the
    order the renderer paints. It lets the agent say "die zweite Karte" and be
    right.
    """
    data = surface.data if isinstance(surface.data, dict) else {}
    lines: list[str] = []

    for component in surface.components:
        describer = _DESCRIBERS.get(str(component.get("component")))
        if describer is None:
            continue
        described = describer(t, component, data)
        if described:
            lines.append(described)

    if not lines:
        return t("readback.empty", titel=surface.title)

    body = "\n".join(lines)
    if len(body) > MAX_CHARS:
        body = body[:MAX_CHARS].rsplit("\n", 1)[0] + "\n" + t("readback.truncated")
    return t("readback.surface", titel=surface.title) + "\n" + body
