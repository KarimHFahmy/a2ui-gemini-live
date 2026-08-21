"""A2UI v0.9 agent-to-renderer message construction.

The backend is the A2UI *agent*: it speaks UI by emitting a stream of
declarative JSON envelopes that the browser renders with the official
``@a2ui/react`` v0.9 renderer.

Wire format (see specification/v0_9_1 of the A2UI project):

    {"version": "v0.9.1", "createSurface":    {"surfaceId": ..., "catalogId": ...}}
    {"version": "v0.9.1", "updateComponents": {"surfaceId": ..., "components": [...]}}
    {"version": "v0.9.1", "updateDataModel":  {"surfaceId": ..., "path": ..., "value": ...}}
    {"version": "v0.9.1", "deleteSurface":    {"surfaceId": ...}}

v0.9 keeps structure (``components``) and content (``dataModel``) apart, which
is exactly what a live voice session needs: the layout is emitted once and
every follow-up refinement is a cheap data patch.
"""

from __future__ import annotations

from typing import Any, Iterable, Literal

PROTOCOL_VERSION: Literal["v0.9.1"] = "v0.9.1"

#: The A2UI basic catalog shipped with ``@a2ui/react/v0_9``.
BASIC_CATALOG_ID = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"

#: Our own, approved catalog of advisory building blocks ("freigegebener
#: Komponenten-Katalog"). The agent may only ever request these components.
ADVISORY_CATALOG_ID = "urn:a2ui:catalog:adaptive-advisory:1.0"

A2uiMessage = dict[str, Any]


def create_surface(
    surface_id: str,
    *,
    catalog_id: str = ADVISORY_CATALOG_ID,
    send_data_model: bool = False,
) -> A2uiMessage:
    """Creates a new rendering surface.

    ``catalogId`` is the surface default; individual components may override it
    per component, which is how we mix the basic catalog with our own.
    """
    payload: dict[str, Any] = {"surfaceId": surface_id, "catalogId": catalog_id}
    if send_data_model:
        payload["sendDataModel"] = True
    return {"version": PROTOCOL_VERSION, "createSurface": payload}


def update_components(surface_id: str, components: list[dict[str, Any]]) -> A2uiMessage:
    """Adds or replaces components on a surface.

    The renderer expects a flat adjacency list; exactly one component must have
    ``id == "root"``.
    """
    if not components:
        raise ValueError("updateComponents requires at least one component")
    return {
        "version": PROTOCOL_VERSION,
        "updateComponents": {"surfaceId": surface_id, "components": components},
    }


def update_data_model(surface_id: str, value: Any, path: str = "/") -> A2uiMessage:
    """Replaces the value at ``path`` in the surface data model."""
    return {
        "version": PROTOCOL_VERSION,
        "updateDataModel": {"surfaceId": surface_id, "path": path, "value": value},
    }


def delete_surface(surface_id: str) -> A2uiMessage:
    """Removes a surface and everything on it."""
    return {"version": PROTOCOL_VERSION, "deleteSurface": {"surfaceId": surface_id}}


def validate_tree(components: Iterable[dict[str, Any]]) -> None:
    """Guardrail: catches malformed trees before they reach the browser.

    A surface that references a missing child renders a permanent
    "[Loading ...]" placeholder, which looks like a hang during a live demo.
    Failing loudly here turns that into a server-side error we can log.
    """
    comps = list(components)
    ids = [c.get("id") for c in comps]

    duplicates = {i for i in ids if i is not None and ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"duplicate component ids: {sorted(duplicates)}")
    if "root" not in ids:
        raise ValueError("component tree has no component with id 'root'")

    known = set(ids)
    for comp in comps:
        for ref in _child_references(comp):
            if ref not in known:
                raise ValueError(
                    f"component {comp.get('id')!r} references unknown child {ref!r}"
                )


#: Properties that hold a single child id or a list of child ids. Kept explicit
#: rather than inferred so a typo in a component builder fails fast. Data
#: bindings are dicts and never match, which is why only plain strings and
#: string lists are treated as references.
_SINGLE_CHILD_PROPS = ("child", "trigger", "content")
_CHILD_LIST_PROPS = ("children",)


def _child_references(component: dict[str, Any]) -> list[str]:
    refs: list[str] = []

    for prop in _SINGLE_CHILD_PROPS:
        value = component.get(prop)
        if isinstance(value, str):
            refs.append(value)

    for prop in _CHILD_LIST_PROPS:
        value = component.get(prop)
        if isinstance(value, list):
            refs.extend(v for v in value if isinstance(v, str))
        elif isinstance(value, dict) and "componentId" in value:
            # ChildList template form: {"componentId": ..., "path": ...}
            refs.append(value["componentId"])

    for tab in component.get("tabs") or []:
        if isinstance(tab, dict) and isinstance(tab.get("child"), str):
            refs.append(tab["child"])

    return refs
