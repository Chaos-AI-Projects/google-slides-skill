"""
Tests for connector routing improvements -- v2.

Tests that connectors route around container boxes (not just child shapes),
and that the routing avoids crossing through intermediate containers.
"""

from google_slides_skill.shapes import reset_ids, line as _line, to_emu
from google_slides_skill.connectors import (
    _segments_intersect_box, _route_around_obstacles,
    _determine_sides, smart_elbow_connector, directed_edge_point,
)
from google_slides_skill.containers import Container, render_containers


def setup():
    reset_ids()


# ---------------------------------------------------------------------------
# Container boxes should be treated as obstacles
# ---------------------------------------------------------------------------

def test_three_containers_no_crossover():
    """Connector from left to right container should NOT cross through
    the middle container.

    Layout: [A] [B] [C] side by side.
    Connector from A/child to C/child must route around B, not through it.

    Uses layout_mode="grid" so the 2-layer adjacency validator does not
    silently drop the non-adjacent connector.
    """
    setup()
    c_a = Container(id="a", title="A", x=1.0, y=1.5, w=2.0, h=2.0,
                    children=[{"id": "x", "label": "X", "type": "service"}])
    c_b = Container(id="b", title="B", x=3.5, y=1.5, w=2.0, h=2.0,
                    children=[{"id": "y", "label": "Y", "type": "service"}])
    c_c = Container(id="c", title="C", x=6.0, y=1.5, w=2.0, h=2.0,
                    children=[{"id": "z", "label": "Z", "type": "service"}])

    connectors = [{
        "from_container": "a", "from_child": "x",
        "to_container": "c", "to_child": "z",
    }]

    reqs = render_containers("slide1", [c_a, c_b, c_c],
                             connectors_spec=connectors,
                             layout_mode="grid")

    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) >= 1, "Expected at least 1 connector segment to be produced"

    segments = []
    for lr in lines:
        props = lr["createLine"]["elementProperties"]
        tx = props["transform"]["translateX"] / to_emu(1.0)
        ty = props["transform"]["translateY"] / to_emu(1.0)
        sx = props["transform"].get("scaleX", 1)
        sy = props["transform"].get("scaleY", 1)
        w = props["size"]["width"]["magnitude"] / to_emu(1.0)
        h = props["size"]["height"]["magnitude"] / to_emu(1.0)

        if sx >= 0 and sy >= 0:
            x1, y1 = tx, ty
            x2, y2 = tx + w, ty + h
        elif sx < 0 and sy >= 0:
            x1, y1 = tx + w, ty
            x2, y2 = tx, ty + h
        elif sx >= 0 and sy < 0:
            x1, y1 = tx, ty + h
            x2, y2 = tx + w, ty
        else:
            x1, y1 = tx + w, ty + h
            x2, y2 = tx, ty

        segments.append((x1, y1, x2, y2))

    for (sx, sy, ex, ey) in segments:
        crosses_b = _segments_intersect_box(
            sx, sy, ex, ey,
            c_b.x, c_b.y, c_b.w, c_b.h,
            margin=0.0,
        )
        assert not crosses_b, (
            f"Segment ({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) crosses container B "
            f"at ({c_b.x},{c_b.y},{c_b.w},{c_b.h})"
        )


def test_route_around_obstacles_includes_container_bounds():
    """When routing between two shapes, container obstacles should be avoided."""
    setup()
    from_shape = {"type": "rectangle", "x": 1.5, "y": 2.0, "width": 1.0, "height": 0.5}
    to_shape = {"type": "rectangle", "x": 7.0, "y": 2.0, "width": 1.0, "height": 0.5}

    container_obstacle = {"x": 3.5, "y": 1.5, "width": 2.0, "height": 2.0}

    segments = _route_around_obstacles(
        (2.5, 2.25), (7.0, 2.25),
        "right", "left",
        from_shape, to_shape,
        [container_obstacle],
    )

    for (sx, sy, ex, ey) in segments:
        crosses = _segments_intersect_box(
            sx, sy, ex, ey,
            container_obstacle["x"], container_obstacle["y"],
            container_obstacle["width"], container_obstacle["height"],
            margin=0.0,
        )
        assert not crosses, (
            f"Segment ({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) crosses obstacle"
        )


def test_vertically_stacked_three_containers():
    """Connector from top to bottom container avoids the middle one.

    Uses layout_mode="grid" so the 2-layer adjacency validator does not
    silently drop the non-adjacent connector.
    """
    setup()
    c_top = Container(id="top", title="Top", x=3.0, y=1.0, w=3.0, h=1.2,
                      children=[{"id": "a", "label": "A", "type": "service"}])
    c_mid = Container(id="mid", title="Mid", x=3.0, y=2.7, w=3.0, h=1.2,
                      children=[{"id": "b", "label": "B", "type": "service"}])
    c_bot = Container(id="bot", title="Bot", x=3.0, y=4.4, w=3.0, h=1.2,
                      children=[{"id": "c", "label": "C", "type": "service"}])

    connectors = [{
        "from_container": "top", "from_child": "a",
        "to_container": "bot", "to_child": "c",
    }]

    reqs = render_containers("slide1", [c_top, c_mid, c_bot],
                             connectors_spec=connectors,
                             layout_mode="grid")

    lines = [r for r in reqs if "createLine" in r]
    assert len(lines) >= 3, f"Expected >= 3 segments to avoid middle, got {len(lines)}"
