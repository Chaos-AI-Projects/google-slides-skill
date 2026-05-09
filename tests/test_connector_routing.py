"""
Tests for connector routing improvements -- Phases A, B, C.

Phase A: Elbow connectors for cross-container connections
Phase B: Smart edge selection based on container adjacency
Phase C: Obstacle-aware routing with spatial index
"""

import math

from google_slides_skill.shapes import reset_ids
from google_slides_skill.connectors import (
    directed_edge_point, rect_edge_point, edge_point,
    smart_elbow_connector, elbow_connector, straight_connector,
)
from google_slides_skill.containers import (
    Container, render_containers, _compute_child_positions,
    auto_position_containers,
)


def setup():
    reset_ids()


# ---------------------------------------------------------------------------
# Phase B: directed_edge_point
# ---------------------------------------------------------------------------

def test_directed_edge_point_right():
    """Midpoint of right edge."""
    x, y = directed_edge_point("rectangle", 1.0, 2.0, 3.0, 1.0, "right")
    assert abs(x - 4.0) < 0.001, f"x={x}, expected 4.0"
    assert abs(y - 2.5) < 0.001, f"y={y}, expected 2.5"


def test_directed_edge_point_left():
    """Midpoint of left edge."""
    x, y = directed_edge_point("rectangle", 1.0, 2.0, 3.0, 1.0, "left")
    assert abs(x - 1.0) < 0.001
    assert abs(y - 2.5) < 0.001


def test_directed_edge_point_top():
    """Midpoint of top edge."""
    x, y = directed_edge_point("rectangle", 1.0, 2.0, 3.0, 1.0, "top")
    assert abs(x - 2.5) < 0.001
    assert abs(y - 2.0) < 0.001


def test_directed_edge_point_bottom():
    """Midpoint of bottom edge."""
    x, y = directed_edge_point("rectangle", 1.0, 2.0, 3.0, 1.0, "bottom")
    assert abs(x - 2.5) < 0.001
    assert abs(y - 3.0) < 0.001


def test_directed_edge_point_ellipse():
    """Ellipse edge points at cardinal directions."""
    x, y = directed_edge_point("ellipse", 1.0, 2.0, 4.0, 2.0, "right")
    assert abs(x - 5.0) < 0.001
    assert abs(y - 3.0) < 0.001


# ---------------------------------------------------------------------------
# Phase A: smart_elbow_connector direction selection
# ---------------------------------------------------------------------------

def test_smart_elbow_horizontal_right():
    """Source left of target -> exit right, enter left, horizontal-first elbow."""
    setup()
    from_shape = {"type": "rectangle", "x": 1.0, "y": 2.0, "width": 1.0, "height": 0.5}
    to_shape = {"type": "rectangle", "x": 5.0, "y": 3.0, "width": 1.0, "height": 0.5}

    oid, reqs = smart_elbow_connector(
        "slide1", from_shape, to_shape,
        from_container_bounds=(0.5, 1.5, 2.5, 2.0),
        to_container_bounds=(4.5, 1.5, 2.5, 2.0),
    )

    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) >= 2, f"Expected >= 2 line segments, got {len(lines)}"


def test_smart_elbow_vertical_down():
    """Source above target -> exit bottom, enter top, vertical-first elbow."""
    setup()
    from_shape = {"type": "rectangle", "x": 3.0, "y": 1.0, "width": 1.0, "height": 0.5}
    to_shape = {"type": "rectangle", "x": 4.0, "y": 4.0, "width": 1.0, "height": 0.5}

    oid, reqs = smart_elbow_connector(
        "slide1", from_shape, to_shape,
        from_container_bounds=(2.0, 0.5, 3.0, 1.5),
        to_container_bounds=(2.0, 3.5, 3.0, 1.5),
    )

    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) >= 2, f"Expected >= 2 line segments, got {len(lines)}"


def test_smart_elbow_same_container():
    """Same container -> use straight connector."""
    setup()
    from_shape = {"type": "rectangle", "x": 1.0, "y": 1.0, "width": 1.0, "height": 0.5}
    to_shape = {"type": "rectangle", "x": 1.0, "y": 2.5, "width": 1.0, "height": 0.5}

    bounds = (0.5, 0.5, 3.0, 3.5)
    oid, reqs = smart_elbow_connector(
        "slide1", from_shape, to_shape,
        from_container_bounds=bounds,
        to_container_bounds=bounds,
    )

    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) >= 1


def test_smart_elbow_preferred_side():
    """Connector spec can override the side selection."""
    setup()
    from_shape = {"type": "rectangle", "x": 1.0, "y": 2.0, "width": 1.0, "height": 0.5}
    to_shape = {"type": "rectangle", "x": 5.0, "y": 2.0, "width": 1.0, "height": 0.5}

    oid, reqs = smart_elbow_connector(
        "slide1", from_shape, to_shape,
        from_container_bounds=(0.5, 1.5, 2.5, 2.0),
        to_container_bounds=(4.5, 1.5, 2.5, 2.0),
        preferred_from_side="bottom",
        preferred_to_side="top",
    )

    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) >= 2


# ---------------------------------------------------------------------------
# Phase C: obstacle-aware routing
# ---------------------------------------------------------------------------

def test_no_obstacle_no_waypoints():
    """When no obstacle in path, smart_elbow uses 2-segment route."""
    setup()
    from_shape = {"type": "rectangle", "x": 1.0, "y": 2.0, "width": 1.0, "height": 0.5}
    to_shape = {"type": "rectangle", "x": 5.0, "y": 2.0, "width": 1.0, "height": 0.5}

    oid, reqs = smart_elbow_connector(
        "slide1", from_shape, to_shape,
        from_container_bounds=(0.5, 1.5, 2.5, 2.0),
        to_container_bounds=(4.5, 1.5, 2.5, 2.0),
        obstacles=[],
    )

    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) >= 1


def test_obstacle_adds_waypoints():
    """When obstacle blocks direct path, route around it."""
    setup()
    from_shape = {"type": "rectangle", "x": 1.0, "y": 2.0, "width": 1.0, "height": 0.5}
    to_shape = {"type": "rectangle", "x": 7.0, "y": 2.0, "width": 1.0, "height": 0.5}

    obstacle = {"x": 3.5, "y": 1.5, "width": 2.0, "height": 1.5}

    oid, reqs = smart_elbow_connector(
        "slide1", from_shape, to_shape,
        from_container_bounds=(0.5, 1.5, 2.0, 1.5),
        to_container_bounds=(6.5, 1.5, 2.0, 1.5),
        obstacles=[obstacle],
    )

    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) >= 3, f"Expected >= 3 segments to route around, got {len(lines)}"


# ---------------------------------------------------------------------------
# Integration: render_containers uses smart routing
# ---------------------------------------------------------------------------

def test_render_containers_uses_elbow():
    """Cross-container connectors should use elbow routing."""
    setup()
    c1 = Container(id="left", title="Left", x=1.0, y=1.0, w=3.0, h=3.0,
                   columns=1,
                   children=[
                       {"id": "a", "label": "A", "type": "rectangle"},
                       {"id": "a2", "label": "A2", "type": "rectangle"},
                   ])
    c2 = Container(id="right", title="Right", x=5.0, y=1.0, w=3.0, h=3.0,
                   columns=1,
                   children=[
                       {"id": "b", "label": "B", "type": "service"},
                       {"id": "b2", "label": "B2", "type": "service"},
                   ])

    connectors = [{
        "from_container": "left", "from_child": "a",
        "to_container": "right", "to_child": "b2",
    }]

    reqs = render_containers("slide1", [c1, c2], connectors_spec=connectors)
    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) >= 2, f"Expected >= 2 lines for elbow, got {len(lines)}"


def test_render_containers_same_container_straight():
    """Within same container, connectors use straight lines."""
    setup()
    c1 = Container(id="group", title="Group", x=1.0, y=1.0, w=4.0, h=3.0,
                   children=[
                       {"id": "a", "label": "A", "type": "rectangle"},
                       {"id": "b", "label": "B", "type": "rectangle"},
                   ])

    connectors = [{
        "from_container": "group", "from_child": "a",
        "to_container": "group", "to_child": "b",
    }]

    reqs = render_containers("slide1", [c1], connectors_spec=connectors)
    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) == 1, f"Expected 1 line for straight, got {len(lines)}"


def test_render_containers_vertical_containers():
    """Vertically stacked containers should route bottom-to-top."""
    setup()
    c1 = Container(id="top", title="Top", x=2.0, y=1.0, w=3.0, h=1.5,
                   children=[{"id": "a", "label": "A", "type": "service"}])
    c2 = Container(id="bottom", title="Bottom", x=2.0, y=3.5, w=3.0, h=1.5,
                   children=[{"id": "b", "label": "B", "type": "database"}])

    connectors = [{
        "from_container": "top", "from_child": "a",
        "to_container": "bottom", "to_child": "b",
    }]

    reqs = render_containers("slide1", [c1, c2], connectors_spec=connectors)
    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) >= 1
