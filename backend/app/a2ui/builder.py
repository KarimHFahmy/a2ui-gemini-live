"""Composing A2UI surfaces from the official basic catalog.

The renderer's catalog is Google's `@a2ui/react` basic catalog — Card, Column,
Row, Text (Markdown), List, Button, ChoicePicker, Modal, Divider — plus exactly
two additions that have no official equivalent: `MetricChart` and
`ComparisonTable`.

A2UI wants a flat adjacency list where every component carries a unique id and
parents reference children by id. Building that by hand is where composers go
wrong, so :class:`SurfaceBuilder` hands out ids as a side effect of adding
components: children are built first (Python evaluates arguments before calls),
so the tree reads top-down in the source and comes out flat on the wire.

    b = SurfaceBuilder("eignung", "Wärmepumpen-Check")
    b.root(b.column([
        b.heading("Wärmepumpen-Check", "Ihr Haus ist gut geeignet"),
        b.stat_card(title="Vorlauftemperatur", metric="55 °C", body="…"),
    ]))
    return b.finish({"annahmen": [...]})
"""

from __future__ import annotations

from typing import Any, Literal, Sequence

from .surface import Surface

Component = dict[str, Any]
Dynamic = Any  # a literal, a {"path": …} binding, or a {"call": …} function call
Tone = Literal["positive", "neutral", "caution"]

#: Tone is carried by a leading mark rather than by colour: the basic catalog
#: has no tone affordance, and a glyph survives both Markdown and plain text.
TONE_MARK: dict[str, str] = {"positive": "✓", "neutral": "→", "caution": "!"}


def bind(path: str) -> dict[str, str]:
    """A data binding the renderer resolves against the surface data model."""
    return {"path": path}


class SurfaceBuilder:
    """Accumulates one surface's flat component list."""

    def __init__(self, surface_id: str, title: str) -> None:
        self.surface_id = surface_id
        self.title = title
        self._components: list[Component] = []
        self._root_id: str | None = None
        self._next = 0

    # -- plumbing ---------------------------------------------------------

    def _add(self, component: Component) -> str:
        """Registers a component and returns the id parents reference it by."""
        component_id = f"c{self._next}"
        self._next += 1
        self._components.append(
            {"id": component_id, **{k: v for k, v in component.items() if v is not None}}
        )
        return component_id

    def root(self, component_id: str) -> None:
        """Marks which component mounts as the surface root."""
        self._root_id = component_id

    def finish(self, data: dict[str, Any] | None = None) -> Surface:
        """Renames the root to ``root`` — the id A2UI mounts — and returns it."""
        if self._root_id is None:
            raise ValueError(f"surface {self.surface_id!r} has no root component")

        components = [
            {**c, "id": "root"} if c["id"] == self._root_id else c
            for c in self._components
        ]
        return Surface(
            surface_id=self.surface_id,
            title=self.title,
            components=components,
            data=data or {},
        )

    # -- basic catalog: layout -------------------------------------------

    def column(
        self,
        children: Sequence[str],
        *,
        align: str | None = None,
        justify: str | None = None,
        weight: float | None = None,
    ) -> str:
        return self._add(
            {
                "component": "Column",
                "children": list(children),
                "align": align,
                "justify": justify,
                "weight": weight,
            }
        )

    def row(
        self,
        children: Sequence[str],
        *,
        align: str | None = "stretch",
        justify: str | None = None,
        weight: float | None = None,
    ) -> str:
        return self._add(
            {
                "component": "Row",
                "children": list(children),
                "align": align,
                "justify": justify,
                "weight": weight,
            }
        )

    def card(self, child: str, *, weight: float | None = None) -> str:
        return self._add({"component": "Card", "child": child, "weight": weight})

    def text(
        self,
        value: Dynamic,
        *,
        variant: Literal["h1", "h2", "h3", "h4", "h5", "caption", "body"] | None = None,
        weight: float | None = None,
    ) -> str:
        """A Text component.

        The heading and caption variants render as native elements; everything
        else goes through the renderer's Markdown pipeline, so ``**bold**`` and
        ``- bullets`` work in body copy.
        """
        return self._add(
            {"component": "Text", "text": value, "variant": variant, "weight": weight}
        )

    def repeat(
        self,
        template_id: str,
        path: str,
        *,
        direction: Literal["vertical", "horizontal"] = "vertical",
    ) -> str:
        """A List that instantiates ``template_id`` once per item at ``path``.

        Inside the template, bindings are *relative* to the item — ``bind("titel")``
        rather than ``bind("/schritte/0/titel")``. This is how one component
        definition renders a whole timeline or fact list, and why adding a step
        is a data update rather than a layout change.
        """
        return self._add(
            {
                "component": "List",
                "children": {"componentId": template_id, "path": path},
                "direction": direction,
            }
        )

    # -- basic catalog: interaction ---------------------------------------

    def button(
        self,
        label: Dynamic,
        *,
        event: str,
        context: dict[str, Dynamic] | None = None,
        variant: Literal["default", "primary", "borderless"] = "default",
    ) -> str:
        """A Button that dispatches an event back to the agent."""
        return self._add(
            {
                "component": "Button",
                "child": self.text(label),
                "variant": variant,
                "action": {"event": {"name": event, "context": context or {}}},
            }
        )

    def choice(
        self,
        options: Sequence[tuple[str, str]],
        value_path: str,
        *,
        label: Dynamic | None = None,
        display: Literal["checkbox", "chips"] = "chips",
        multiple: bool = False,
    ) -> str:
        """A ChoicePicker bound to a string list in the data model.

        The binding is two-way: picking an option writes it back, so anything
        else bound to the same path updates without a round trip to the agent.
        """
        return self._add(
            {
                "component": "ChoicePicker",
                "label": label,
                "variant": "multipleSelection" if multiple else "mutuallyExclusive",
                "options": [{"label": label_, "value": value} for label_, value in options],
                "value": bind(value_path),
                "displayStyle": display,
            }
        )

    def modal(self, trigger: str, content: str) -> str:
        return self._add({"component": "Modal", "trigger": trigger, "content": content})

    # -- the two additions ------------------------------------------------

    def chart(
        self,
        *,
        categories: Dynamic,
        series: Dynamic,
        chart_type: Literal["bar", "groupedBar", "stackedBar", "line"] = "bar",
        title: Dynamic | None = None,
        subtitle: Dynamic | None = None,
        unit: Dynamic | None = None,
        value_format: Literal["number", "currency", "percent"] = "number",
    ) -> str:
        """Baustein "Diagramm". No official A2UI equivalent, so it is ours."""
        return self._add(
            {
                "component": "MetricChart",
                "title": title,
                "subtitle": subtitle,
                "chartType": chart_type,
                "categories": categories,
                "series": series,
                "unit": unit,
                "valueFormat": value_format,
            }
        )

    def table(
        self,
        *,
        columns: Dynamic,
        rows: Dynamic,
        title: Dynamic | None = None,
        highlight: Dynamic | None = None,
    ) -> str:
        """Baustein "Vergleich". No official A2UI equivalent, so it is ours."""
        return self._add(
            {
                "component": "ComparisonTable",
                "title": title,
                "columns": columns,
                "rows": rows,
                "highlight": highlight,
            }
        )

    # -- composed patterns ------------------------------------------------
    #
    # Recurring shapes built from basic-catalog components. They keep the
    # composers declarative without adding anything to the renderer's catalog.

    def heading(
        self,
        eyebrow: Dynamic,
        title: Dynamic,
        subtitle: Dynamic | None = None,
    ) -> str:
        """Section header: an eyebrow, a heading and an optional lead."""
        children = [
            self.text(eyebrow, variant="caption"),
            self.text(title, variant="h2"),
        ]
        if subtitle is not None:
            children.append(self.text(subtitle, variant="body"))
        return self.column(children)

    def stat_card(
        self,
        *,
        title: Dynamic,
        body: Dynamic,
        metric: Dynamic | None = None,
        metric_label: Dynamic | None = None,
        tone: Tone = "neutral",
        weight: float | None = None,
    ) -> str:
        """Baustein "Karte": one idea, optionally with a headline metric."""
        children = [
            self.text(
                f"{TONE_MARK[tone]} {title}" if isinstance(title, str) else title,
                variant="h4",
            )
        ]
        if metric is not None:
            children.append(self.text(metric, variant="h1"))
            if metric_label:
                children.append(self.text(metric_label, variant="caption"))
        children.append(self.text(body))
        return self.card(self.column(children), weight=weight)

    def bullets(self, items: Sequence[str], *, heading: Dynamic | None = None) -> str:
        """A bulleted list.

        Rendered as one Markdown Text rather than a `repeat` over the data
        model: a flat list of strings has nothing to patch later, and a single
        component beats N for something this small.
        """
        children = []
        if heading is not None:
            children.append(self.text(heading, variant="h5"))
        children.append(self.text("\n".join(f"- {item}" for item in items)))
        return self.column(children)

    def assumptions(self, items: Sequence[str], *, source: str, as_of: str) -> str:
        """"Annahmen und Datenquellen sichtbar machen".

        A Modal keeps the assumptions one tap away from every number without
        letting them compete with the advice — the briefing's progressive
        disclosure applied to the small print.
        """
        # `caption` renders as a native <em>, not through Markdown, so the
        # label is written plainly rather than with underscores.
        trigger = self.text("Annahmen und Datenquellen ansehen", variant="caption")
        content = self.column(
            [
                self.text("Annahmen und Datenquellen", variant="h3"),
                self.text("\n".join(f"- {item}" for item in items)),
                self.text(f"{source} · {as_of}", variant="caption"),
            ]
        )
        return self.modal(trigger, content)
