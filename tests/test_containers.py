"""
Unit tests for containers.py -- Phase 5.

Tests container layout logic, auto-sizing, auto-positioning, child placement,
z-order, and request generation without hitting the Google Slides API.
"""

import math

from google_slides_skill.shapes import reset_ids
from google_slides_skill.containers import (
    Container, auto_size_container, auto_position_containers,
    _compute_child_positions, _auto_columns, render_containers,
    CONTAINER_PADDING, TITLE_BAR_HEIGHT, CHILD_SPACING,
    DEFAULT_CHILD_W, DEFAULT_CHILD_H,
)


def setup():
    """Reset shape ID counter before each logical test group."""
    reset_ids()


# ---------------------------------------------------------------------------
# _auto_columns
# ---------------------------------------------------------------------------

def test_auto_columns():
    assert _auto_columns(1) == 1
    assert _auto_columns(2) == 2
    assert _auto_columns(3) == 2
    assert _auto_columns(4) == 2
    assert _auto_columns(5) == 3
    assert _auto_columns(9) == 3
    assert _auto_columns(10) == 4


# ---------------------------------------------------------------------------
# auto_size_container
# ---------------------------------------------------------------------------

def test_auto_size_empty():
    c = Container(id="empty", title="Empty")
    auto_size_container(c)
    assert c.w == 2.0
    assert c.h == 1.0


def test_auto_size_single_child():
    c = Container(id="one", title="One", children=[
        {"id": "a", "label": "A", "type": "rectangle"},
    ])
    auto_size_container(c)
    expected_w = 1 * DEFAULT_CHILD_W + 0 * CHILD_SPACING + 2 * CONTAINER_PADDING
    expected_h = TITLE_BAR_HEIGHT + 1 * DEFAULT_CHILD_H + 0 * CHILD_SPACING + 2 * CONTAINER_PADDING
    assert abs(c.w - expected_w) < 0.001, f"w={c.w}, expected={expected_w}"
    assert abs(c.h - expected_h) < 0.001, f"h={c.h}, expected={expected_h}"


def test_auto_size_four_children():
    """4 children -> 2x2 grid in grid layout mode."""
    c = Container(id="four", title="Four", children=[
        {"id": f"c{i}", "label": f"C{i}", "type": "rectangle"} for i in range(4)
    ])
    auto_size_container(c, layout_mode="grid")
    expected_w = 2 * DEFAULT_CHILD_W + 1 * CHILD_SPACING + 2 * CONTAINER_PADDING
    expected_h = TITLE_BAR_HEIGHT + 2 * DEFAULT_CHILD_H + 1 * CHILD_SPACING + 2 * CONTAINER_PADDING
    assert abs(c.w - expected_w) < 0.001, f"w={c.w}, expected={expected_w}"
    assert abs(c.h - expected_h) < 0.001, f"h={c.h}, expected={expected_h}"


def test_auto_size_explicit_overrides():
    """Explicit w/h should not be overwritten."""
    c = Container(id="explicit", title="Explicit", w=5.0, h=3.0, children=[
        {"id": "a", "label": "A", "type": "rectangle"},
    ])
    auto_size_container(c)
    assert c.w == 5.0
    assert c.h == 3.0


# ---------------------------------------------------------------------------
# auto_position_containers
# ---------------------------------------------------------------------------

def test_auto_position_basic():
    c1 = Container(id="a", title="A", w=3.0, h=2.0)
    c2 = Container(id="b", title="B", w=3.0, h=2.0)
    auto_position_containers([c1, c2], area_x=1.0, area_y=1.0, area_w=8.0, area_h=4.0,
                             layout_mode="grid")
    assert c1.x == 1.0
    assert c1.y == 1.0
    assert c2.x == 1.0 + 3.0 + 0.25  # gap
    assert c2.y == 1.0


def test_auto_position_wraps():
    """Containers that exceed area width wrap to next row."""
    c1 = Container(id="a", title="A", w=5.0, h=2.0)
    c2 = Container(id="b", title="B", w=5.0, h=2.0)
    auto_position_containers([c1, c2], area_x=0.5, area_y=0.5, area_w=8.0, area_h=6.0,
                             layout_mode="grid")
    assert c1.x == 0.5
    assert c1.y == 0.5
    assert c2.x == 0.5
    assert abs(c2.y - (0.5 + 2.0 + 0.25)) < 0.001


def test_auto_position_preserves_explicit():
    """Containers with explicit x/y should keep them."""
    c1 = Container(id="a", title="A", x=2.0, y=2.0, w=3.0, h=2.0)
    c2 = Container(id="b", title="B", w=3.0, h=2.0)
    auto_position_containers([c1, c2], area_x=1.0, area_y=1.0, area_w=8.0, area_h=4.0)
    assert c1.x == 2.0
    assert c1.y == 2.0
    assert c2.x is not None
    assert c2.y is not None


# ---------------------------------------------------------------------------
# _compute_child_positions
# ---------------------------------------------------------------------------

def test_child_positions_single():
    c = Container(id="one", title="One", x=1.0, y=1.0, w=3.0, h=2.0,
                  children=[{"id": "a", "label": "A", "type": "rectangle"}])
    placed = _compute_child_positions(c)
    assert len(placed) == 1
    child = placed[0]
    assert child["_x"] >= c.x + CONTAINER_PADDING
    assert child["_y"] >= c.y + TITLE_BAR_HEIGHT + CONTAINER_PADDING
    assert child["_x"] + child["_w"] <= c.x + c.w - CONTAINER_PADDING + 0.01


def test_child_positions_grid():
    c = Container(id="four", title="Four", x=1.0, y=1.0, w=4.0, h=3.0,
                  children=[
                      {"id": f"c{i}", "label": f"C{i}", "type": "rectangle"}
                      for i in range(4)
                  ])
    placed = _compute_child_positions(c, layout_mode="grid")
    assert len(placed) == 4

    for child in placed:
        assert child["_x"] >= c.x
        assert child["_y"] >= c.y + TITLE_BAR_HEIGHT
        assert child["_x"] + child["_w"] <= c.x + c.w + 0.01
        assert child["_y"] + child["_h"] <= c.y + c.h + 0.01

    # Grid layout: 2x2 arrangement
    assert placed[0]["_y"] == placed[1]["_y"]
    assert placed[2]["_y"] == placed[3]["_y"]
    assert placed[0]["_y"] < placed[2]["_y"]
    assert placed[0]["_x"] < placed[1]["_x"]


# ---------------------------------------------------------------------------
# render_containers -- request generation
# ---------------------------------------------------------------------------

def test_render_produces_requests():
    setup()
    c = Container(id="svc", title="Services", x=1.0, y=1.0, w=4.0, h=2.5,
                  children=[
                      {"id": "api", "label": "API", "type": "service"},
                      {"id": "web", "label": "Web", "type": "service"},
                  ])
    reqs = render_containers("slide1", [c])
    assert len(reqs) > 0

    create_shapes = [r for r in reqs if "createShape" in r]
    assert len(create_shapes) >= 3
    first_shape = create_shapes[0]["createShape"]
    assert first_shape["shapeType"] == "RECTANGLE"
    assert "container_svc" in first_shape["objectId"]


def test_render_z_order():
    """Container backgrounds must come before child shapes in the request list."""
    setup()
    c = Container(id="grp", title="Group", x=1.0, y=1.0, w=4.0, h=2.5,
                  children=[{"id": "a", "label": "A", "type": "rectangle"}])
    reqs = render_containers("slide1", [c])

    create_shapes = [r for r in reqs if "createShape" in r]
    assert "container_grp" in create_shapes[0]["createShape"]["objectId"]
    assert "ctitle_grp" in create_shapes[1]["createShape"]["objectId"]
    assert create_shapes[2]["createShape"]["shapeType"] in ("RECTANGLE", "ROUND_RECTANGLE")


def test_render_with_connectors():
    setup()
    c1 = Container(id="frontend", title="Frontend", x=1.0, y=1.0, w=3.0, h=2.0,
                   children=[{"id": "ui", "label": "UI", "type": "rectangle"}])
    c2 = Container(id="backend", title="Backend", x=5.0, y=1.0, w=3.0, h=2.0,
                   children=[{"id": "api", "label": "API", "type": "service"}])

    connectors = [{
        "from_container": "frontend", "from_child": "ui",
        "to_container": "backend", "to_child": "api",
        "label": "HTTP",
    }]

    reqs = render_containers("slide1", [c1, c2], connectors_spec=connectors)
    create_lines = [r for r in reqs if "createLine" in r]
    assert len(create_lines) >= 1, f"Expected at least 1 line, got {len(create_lines)}"


def test_render_with_standalone_nodes():
    setup()
    c1 = Container(id="svc", title="Services", x=1.0, y=1.0, w=3.0, h=2.0,
                   children=[{"id": "api", "label": "API", "type": "service"}])

    standalone = [
        {"id": "client", "label": "Client", "type": "rounded_rectangle",
         "x": 5.0, "y": 1.5, "w": 1.5, "h": 0.7},
    ]

    connectors = [{
        "from_node": "client",
        "to_container": "svc", "to_child": "api",
    }]

    reqs = render_containers("slide1", [c1], connectors_spec=connectors,
                             standalone_nodes=standalone)
    create_shapes = [r for r in reqs if "createShape" in r]
    assert len(create_shapes) >= 4, f"Expected >= 4 shapes, got {len(create_shapes)}"


def test_render_multiple_containers():
    """Multiple containers auto-positioned."""
    setup()
    containers = [
        Container(id="a", title="Group A", children=[
            {"id": "a1", "label": "A1", "type": "service"},
        ]),
        Container(id="b", title="Group B", children=[
            {"id": "b1", "label": "B1", "type": "database"},
            {"id": "b2", "label": "B2", "type": "cache"},
        ]),
        Container(id="c", title="Group C", children=[
            {"id": "c1", "label": "C1", "type": "queue"},
        ]),
    ]

    reqs = render_containers("slide1", containers)
    assert len(reqs) > 0

    for c in containers:
        assert c.x is not None
        assert c.y is not None
        assert c.w is not None
        assert c.h is not None


# ---------------------------------------------------------------------------
# Architecture diagram module
# ---------------------------------------------------------------------------

def test_render_architecture():
    setup()
    from google_slides_skill.diagrams.architecture import render_architecture

    groups = [
        {
            "id": "frontend",
            "title": "Frontend",
            "children": [
                {"id": "spa", "label": "SPA", "type": "rectangle"},
                {"id": "cdn", "label": "CDN", "type": "service"},
            ],
        },
        {
            "id": "backend",
            "title": "Backend",
            "children": [
                {"id": "api", "label": "API", "type": "service"},
                {"id": "worker", "label": "Worker", "type": "service"},
            ],
        },
    ]
    connectors = [
        {"from_container": "frontend", "from_child": "spa",
         "to_container": "backend", "to_child": "api"},
    ]

    reqs = render_architecture("slide1", groups, connectors)
    assert len(reqs) > 0

    create_shapes = [r for r in reqs if "createShape" in r]
    create_lines = [r for r in reqs if "createLine" in r]
    assert len(create_shapes) >= 6
    assert len(create_lines) >= 1
