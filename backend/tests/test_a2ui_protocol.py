"""The A2UI wire format the renderer accepts.

These assert the exact envelope shapes from the A2UI v0.9 specification. A
regression here shows up in the browser as a silently blank surface, which is
the worst possible failure mode during a live demo.
"""

from __future__ import annotations

import pytest

from app.a2ui import protocol


def test_create_surface_carries_catalog_and_version():
    message = protocol.create_surface("profil")

    assert message["version"] == "v0.9.1"
    assert message["createSurface"] == {
        "surfaceId": "profil",
        "catalogId": protocol.ADVISORY_CATALOG_ID,
    }


def test_create_surface_omits_send_data_model_when_false():
    # The v0.9 schema is strict; an explicit `false` is noise on the wire.
    assert "sendDataModel" not in protocol.create_surface("x")["createSurface"]
    assert protocol.create_surface("x", send_data_model=True)["createSurface"][
        "sendDataModel"
    ]


def test_update_components_rejects_empty_list():
    with pytest.raises(ValueError):
        protocol.update_components("profil", [])


def test_update_data_model_defaults_to_root():
    message = protocol.update_data_model("profil", {"a": 1})
    assert message["updateDataModel"]["path"] == "/"


class TestValidateTree:
    def test_accepts_a_well_formed_tree(self):
        protocol.validate_tree(
            [
                {"id": "root", "component": "Column", "children": ["a", "b"]},
                {"id": "a", "component": "Card", "child": "b"},
                {"id": "b", "component": "Text", "text": "hi"},
            ]
        )

    def test_requires_a_root(self):
        with pytest.raises(ValueError, match="no component with id 'root'"):
            protocol.validate_tree([{"id": "a", "component": "Text", "text": "hi"}])

    def test_rejects_duplicate_ids(self):
        with pytest.raises(ValueError, match="duplicate"):
            protocol.validate_tree(
                [
                    {"id": "root", "component": "Column", "children": ["a"]},
                    {"id": "a", "component": "Text", "text": "1"},
                    {"id": "a", "component": "Text", "text": "2"},
                ]
            )

    def test_rejects_dangling_child_reference(self):
        with pytest.raises(ValueError, match="unknown child 'ghost'"):
            protocol.validate_tree(
                [{"id": "root", "component": "Column", "children": ["ghost"]}]
            )

    def test_data_bindings_are_not_child_references(self):
        # `{"path": ...}` in a list-shaped prop is data, not a component id.
        protocol.validate_tree(
            [
                {"id": "root", "component": "Column", "children": ["chart"]},
                {
                    "id": "chart",
                    "component": "MetricChart",
                    "series": {"path": "/serien"},
                    "categories": {"path": "/kategorien"},
                },
            ]
        )
