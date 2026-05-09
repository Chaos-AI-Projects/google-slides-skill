"""
Container shapes for Google Slides -- 2-layer layout model.

Architecture diagrams use a strict 2-layer hierarchy:
  - Layer 1: Groups (containers) -- placed in a row or column
  - Layer 2: Components (children) -- placed within their group

Two layout modes:
  - "horizontal": groups left-to-right, components top-to-bottom within each
  - "vertical": groups top-to-bottom, components left-to-right within each

Connectors are restricted to adjacent elements only:
  - Cross-group: between components in adjacent groups
  - Intra-group: between adjacent components within the same group

This constraint eliminates the need for complex obstacle avoidance routing.

Usage:
    from google_slides_skill.containers import Container, render_containers

    c = Container(
        id="backend",
        title="Backend Services",
        children=[
            {"id": "api", "label": "API Server", "type": "rectangle"},
            {"id": "worker", "label": "Worker", "type": "rectangle"},
        ],
    )
    requests = render_containers(page_id, [c], connectors=[...],
                                 layout_mode="horizontal")
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .shapes import (
    rectangle, rounded_rectangle, ellipse, text_label, _next_id, reset_ids,
    to_emu, _solid_fill, _outline, _text_style, _insert_shape_text,
    FILL_LIGHT_GRAY, FILL_LIGHT_BLUE, FILL_BLUE, FILL_WHITE,
    BORDER_DEFAULT, BORDER_BLUE, DASH_DASH, DASH_SOLID,
    DEFAULT_BORDER_WEIGHT_PT, DEFAULT_FONT_SIZE_PT,
    FILL_GREEN, FILL_ORANGE, FILL_RED, FILL_DARK,
)
from .connectors import (
    straight_connector, smart_elbow_connector, directed_edge_point,
    ARROW_NONE, ARROW_FILLED,
)


# ---------------------------------------------------------------------------
# Color palette for containers
# ---------------------------------------------------------------------------

CONTAINER_FILLS = [
    {"red": 0.94, "green": 0.94, "blue": 0.96},  # light purple-gray
    {"red": 0.93, "green": 0.96, "blue": 0.93},  # light green-gray
    {"red": 0.96, "green": 0.94, "blue": 0.90},  # light warm-gray
    {"red": 0.90, "green": 0.94, "blue": 0.97},  # light blue-gray
    {"red": 0.96, "green": 0.93, "blue": 0.95},  # light pink-gray
]

CONTAINER_BORDERS = [
    {"red": 0.55, "green": 0.55, "blue": 0.65},
    {"red": 0.45, "green": 0.60, "blue": 0.45},
    {"red": 0.65, "green": 0.55, "blue": 0.40},
    {"red": 0.40, "green": 0.55, "blue": 0.65},
    {"red": 0.65, "green": 0.45, "blue": 0.60},
]

# Title bar styling
TITLE_BAR_HEIGHT = 0.35  # inches
TITLE_FONT_SIZE = 11
TITLE_FONT_BOLD = True
TITLE_COLOR = {"red": 0.20, "green": 0.20, "blue": 0.25}

# Child layout constants
CONTAINER_PADDING = 0.15  # padding inside container edges
CHILD_SPACING = 0.20  # gap between children
DEFAULT_CHILD_W = 1.3
DEFAULT_CHILD_H = 0.6

# Child shape fills by type
CHILD_STYLES = {
    "rectangle": {"fill": FILL_LIGHT_BLUE, "border": BORDER_BLUE},
    "rounded_rectangle": {"fill": FILL_LIGHT_BLUE, "border": BORDER_BLUE},
    "ellipse": {"fill": FILL_WHITE, "border": BORDER_DEFAULT},
    "database": {"fill": {"red": 0.85, "green": 0.91, "blue": 0.98}, "border": BORDER_BLUE},
    "service": {"fill": FILL_LIGHT_BLUE, "border": BORDER_BLUE},
    "queue": {"fill": {"red": 0.95, "green": 0.88, "blue": 0.78}, "border": {"red": 0.70, "green": 0.50, "blue": 0.20}},
    "cache": {"fill": {"red": 0.88, "green": 0.95, "blue": 0.88}, "border": {"red": 0.30, "green": 0.60, "blue": 0.30}},
}


# ---------------------------------------------------------------------------
# Container data class
# ---------------------------------------------------------------------------

@dataclass
class Container:
    """A container box that owns child shapes.

    Attributes:
        id: Unique identifier for this container.
        title: Title text displayed in the title bar.
        children: List of child shape dicts with keys:
            id, label, type (rectangle|rounded_rectangle|ellipse|database|service|queue|cache).
        x, y, w, h: Position and size in inches (auto-computed if None).
        fill: Background fill color (auto-assigned from palette if None).
        border_color: Border color (auto-assigned if None).
        border_dash: Border dash style (default DASH_DASH for containers).
        layout: Child arrangement: "grid" or "flow" (horizontal wrap).
        columns: Number of columns for grid layout (auto-computed if None).
    """
    id: str
    title: str
    children: list[dict] = field(default_factory=list)
    x: float | None = None
    y: float | None = None
    w: float | None = None
    h: float | None = None
    fill: dict | None = None
    border_color: dict | None = None
    border_dash: str = DASH_DASH
    layout: str = "grid"
    columns: int | None = None


# ---------------------------------------------------------------------------
# 2-Layer layout engine
# ---------------------------------------------------------------------------

def _compute_child_positions_vertical(container: Container,
                                       child_w: float = DEFAULT_CHILD_W,
                                       child_h: float = DEFAULT_CHILD_H,
                                       ) -> list[dict]:
    """Place children in a vertical stack (top-to-bottom) within the container.

    Used when layout_mode="horizontal" (groups are horizontal, children vertical).
    """
    n = len(container.children)
    if n == 0:
        return []

    inner_x = container.x + CONTAINER_PADDING
    inner_y = container.y + TITLE_BAR_HEIGHT + CONTAINER_PADDING
    inner_w = container.w - 2 * CONTAINER_PADDING
    inner_h = container.h - TITLE_BAR_HEIGHT - 2 * CONTAINER_PADDING

    cw = min(child_w, inner_w)
    avail_h_per_child = (inner_h - CHILD_SPACING * (n - 1)) / n
    ch = min(child_h, avail_h_per_child)

    # Center horizontally within container
    cx = inner_x + (inner_w - cw) / 2

    result = []
    for i, child in enumerate(container.children):
        augmented = dict(child)
        augmented["_x"] = cx
        augmented["_y"] = inner_y + i * (ch + CHILD_SPACING)
        augmented["_w"] = cw
        augmented["_h"] = ch
        augmented["_index"] = i
        result.append(augmented)
    return result


def _compute_child_positions_horizontal(container: Container,
                                         child_w: float = DEFAULT_CHILD_W,
                                         child_h: float = DEFAULT_CHILD_H,
                                         ) -> list[dict]:
    """Place children in a horizontal row (left-to-right) within the container.

    Used when layout_mode="vertical" (groups are vertical, children horizontal).
    """
    n = len(container.children)
    if n == 0:
        return []

    inner_x = container.x + CONTAINER_PADDING
    inner_y = container.y + TITLE_BAR_HEIGHT + CONTAINER_PADDING
    inner_w = container.w - 2 * CONTAINER_PADDING
    inner_h = container.h - TITLE_BAR_HEIGHT - 2 * CONTAINER_PADDING

    avail_w_per_child = (inner_w - CHILD_SPACING * (n - 1)) / n
    cw = min(child_w, avail_w_per_child)
    ch = min(child_h, inner_h)

    # Center vertically within container
    cy = inner_y + (inner_h - ch) / 2

    result = []
    for i, child in enumerate(container.children):
        augmented = dict(child)
        augmented["_x"] = inner_x + i * (cw + CHILD_SPACING)
        augmented["_y"] = cy
        augmented["_w"] = cw
        augmented["_h"] = ch
        augmented["_index"] = i
        result.append(augmented)
    return result


def _compute_child_positions(container: Container,
                             child_w: float = DEFAULT_CHILD_W,
                             child_h: float = DEFAULT_CHILD_H,
                             layout_mode: str = "horizontal",
                             ) -> list[dict]:
    """Compute absolute (x, y, w, h) for each child within the container.

    In the 2-layer model:
      layout_mode="horizontal" -> children stack vertically
      layout_mode="vertical"   -> children stack horizontally

    Falls back to grid layout for compatibility.
    """
    if layout_mode == "horizontal":
        return _compute_child_positions_vertical(container, child_w, child_h)
    elif layout_mode == "vertical":
        return _compute_child_positions_horizontal(container, child_w, child_h)

    # Legacy grid fallback
    n = len(container.children)
    if n == 0:
        return []

    cols = container.columns or _auto_columns(n)
    rows = math.ceil(n / cols)

    inner_x = container.x + CONTAINER_PADDING
    inner_y = container.y + TITLE_BAR_HEIGHT + CONTAINER_PADDING
    inner_w = container.w - 2 * CONTAINER_PADDING
    inner_h = container.h - TITLE_BAR_HEIGHT - 2 * CONTAINER_PADDING

    avail_w_per_child = (inner_w - CHILD_SPACING * (cols - 1)) / cols
    avail_h_per_child = (inner_h - CHILD_SPACING * (rows - 1)) / rows
    cw = min(child_w, avail_w_per_child)
    ch = min(child_h, avail_h_per_child)

    result = []
    for i, child in enumerate(container.children):
        col = i % cols
        row = i // cols
        augmented = dict(child)
        augmented["_x"] = inner_x + col * (cw + CHILD_SPACING)
        augmented["_y"] = inner_y + row * (ch + CHILD_SPACING)
        augmented["_w"] = cw
        augmented["_h"] = ch
        augmented["_index"] = i
        result.append(augmented)
    return result


def _auto_columns(n_children: int) -> int:
    """Pick number of columns for grid layout based on child count."""
    if n_children <= 2:
        return n_children
    if n_children <= 4:
        return 2
    if n_children <= 9:
        return 3
    return 4


def auto_size_container(container: Container,
                        child_w: float = DEFAULT_CHILD_W,
                        child_h: float = DEFAULT_CHILD_H,
                        layout_mode: str = "horizontal") -> None:
    """Compute container w/h from its children if not set."""
    n = len(container.children)
    if n == 0:
        if container.w is None:
            container.w = 2.0
        if container.h is None:
            container.h = 1.0
        return

    if layout_mode == "horizontal":
        # Children stack vertically -> container is tall and narrow
        needed_w = child_w + 2 * CONTAINER_PADDING
        needed_h = (TITLE_BAR_HEIGHT + n * child_h +
                    (n - 1) * CHILD_SPACING + 2 * CONTAINER_PADDING)
    elif layout_mode == "vertical":
        # Children stack horizontally -> container is wide and short
        needed_w = (n * child_w + (n - 1) * CHILD_SPACING +
                    2 * CONTAINER_PADDING)
        needed_h = TITLE_BAR_HEIGHT + child_h + 2 * CONTAINER_PADDING
    else:
        # Grid fallback
        cols = container.columns or _auto_columns(n)
        rows = math.ceil(n / cols)
        needed_w = cols * child_w + (cols - 1) * CHILD_SPACING + 2 * CONTAINER_PADDING
        needed_h = (TITLE_BAR_HEIGHT + rows * child_h +
                    (rows - 1) * CHILD_SPACING + 2 * CONTAINER_PADDING)

    if container.w is None:
        container.w = needed_w
    if container.h is None:
        container.h = needed_h


def auto_position_containers(containers: list[Container],
                             area_x: float = 1.0, area_y: float = 1.0,
                             area_w: float = 8.0, area_h: float = 4.3,
                             layout_mode: str = "horizontal",
                             ) -> None:
    """Position containers according to the layout mode.

    layout_mode="horizontal": groups placed left-to-right
    layout_mode="vertical": groups placed top-to-bottom
    """
    for c in containers:
        auto_size_container(c, layout_mode=layout_mode)

    to_place = [c for c in containers if c.x is None or c.y is None]
    if not to_place:
        return

    gap = 0.25

    if layout_mode == "horizontal":
        # Place groups left-to-right, centered vertically
        total_w = sum(c.w for c in to_place) + gap * (len(to_place) - 1)
        start_x = area_x + max(0, (area_w - total_w) / 2)
        cursor_x = start_x
        for c in to_place:
            if c.x is None:
                c.x = cursor_x
            if c.y is None:
                c.y = area_y + max(0, (area_h - c.h) / 2)
            cursor_x += c.w + gap

    elif layout_mode == "vertical":
        # Place groups top-to-bottom, centered horizontally
        total_h = sum(c.h for c in to_place) + gap * (len(to_place) - 1)
        start_y = area_y + max(0, (area_h - total_h) / 2)
        cursor_y = start_y
        for c in to_place:
            if c.x is None:
                c.x = area_x + max(0, (area_w - c.w) / 2)
            if c.y is None:
                c.y = cursor_y
            cursor_y += c.h + gap

    else:
        # Legacy: horizontal flow with row wrapping
        cursor_x = area_x
        cursor_y = area_y
        row_height = 0.0
        for c in to_place:
            if cursor_x + c.w > area_x + area_w and cursor_x > area_x:
                cursor_x = area_x
                cursor_y += row_height + gap
                row_height = 0.0
            if c.x is None:
                c.x = cursor_x
            if c.y is None:
                c.y = cursor_y
            cursor_x += c.w + gap
            row_height = max(row_height, c.h)


# ---------------------------------------------------------------------------
# Adjacency validation
# ---------------------------------------------------------------------------

def _build_adjacency(containers: list[Container], layout_mode: str,
                     ) -> set[tuple[str, str]]:
    """Build the set of adjacent (container_id, container_id) pairs.

    In horizontal mode, containers at index i and i+1 are adjacent.
    In vertical mode, same logic.
    """
    adj = set()
    for i in range(len(containers) - 1):
        a, b = containers[i].id, containers[i + 1].id
        adj.add((a, b))
        adj.add((b, a))
    return adj


def _child_adjacent_in_group(container: Container, child_a_id: str,
                              child_b_id: str) -> bool:
    """Check if two children are adjacent within a container."""
    ids = [c["id"] for c in container.children]
    try:
        ia = ids.index(child_a_id)
        ib = ids.index(child_b_id)
        return abs(ia - ib) == 1
    except ValueError:
        return False


def validate_connector(conn: dict, containers: list[Container],
                       layout_mode: str,
                       adjacent_groups: set[tuple[str, str]]) -> bool:
    """Validate that a connector respects adjacency constraints.

    Returns True if the connector is valid (connects adjacent elements).
    Standalone nodes bypass adjacency checks.
    """
    # Standalone nodes are always allowed
    if conn.get("from_node") or conn.get("to_node"):
        return True

    from_cid = conn.get("from_container")
    to_cid = conn.get("to_container")
    from_child = conn.get("from_child")
    to_child = conn.get("to_child")

    if not from_cid or not to_cid:
        return True  # incomplete spec, let it through

    # Same container: children must be adjacent
    if from_cid == to_cid:
        container = next((c for c in containers if c.id == from_cid), None)
        if container and from_child and to_child:
            return _child_adjacent_in_group(container, from_child, to_child)
        return True

    # Different containers: must be adjacent groups
    return (from_cid, to_cid) in adjacent_groups


# ---------------------------------------------------------------------------
# Simple connector routing for 2-layer layout
# ---------------------------------------------------------------------------

def _route_adjacent_connector(page_id: str,
                               from_shape: dict, to_shape: dict,
                               from_cid: str | None, to_cid: str | None,
                               layout_mode: str,
                               color: dict = None, weight_pt: float = 1.5,
                               dash: str = DASH_SOLID,
                               end_arrow: str = ARROW_FILLED,
                               label: str = None,
                               label_font_size: float = 9,
                               ) -> list[dict]:
    """Route a connector between adjacent elements using simple paths.

    For same-group connectors: straight line.
    For cross-group connectors: single-bend elbow in the gap direction.
    """
    c = color or BORDER_DEFAULT

    if from_cid == to_cid or from_cid is None or to_cid is None:
        # Same group or standalone: use straight connector
        _, reqs = straight_connector(
            page_id, from_shape, to_shape,
            color=c, weight_pt=weight_pt, dash=dash,
            end_arrow=end_arrow, label=label,
            label_font_size=label_font_size,
        )
        return reqs

    # Cross-group: determine direction based on relative positions
    fcx = from_shape["x"] + from_shape["width"] / 2
    fcy = from_shape["y"] + from_shape["height"] / 2
    tcx = to_shape["x"] + to_shape["width"] / 2
    tcy = to_shape["y"] + to_shape["height"] / 2

    dx = tcx - fcx
    dy = tcy - fcy

    if layout_mode == "horizontal":
        # Groups are side by side: connectors go left/right
        from_side = "right" if dx >= 0 else "left"
        to_side = "left" if dx >= 0 else "right"
    elif layout_mode == "vertical":
        # Groups are stacked: connectors go top/bottom
        from_side = "bottom" if dy >= 0 else "top"
        to_side = "top" if dy >= 0 else "bottom"
    else:
        # Fallback: use the larger delta
        if abs(dx) >= abs(dy):
            from_side = "right" if dx >= 0 else "left"
            to_side = "left" if dx >= 0 else "right"
        else:
            from_side = "bottom" if dy >= 0 else "top"
            to_side = "top" if dy >= 0 else "bottom"

    # Get edge points
    p1 = directed_edge_point(from_shape["type"], from_shape["x"], from_shape["y"],
                              from_shape["width"], from_shape["height"], from_side)
    p2 = directed_edge_point(to_shape["type"], to_shape["x"], to_shape["y"],
                              to_shape["width"], to_shape["height"], to_side)

    x1, y1 = p1
    x2, y2 = p2

    # Simple single-bend elbow: if shapes are roughly aligned, go straight;
    # otherwise use a Z-path with the jog at the midpoint
    from .shapes import line as _line
    reqs = []

    # Check if roughly aligned (within half a shape width/height)
    threshold = 0.3  # inches

    if layout_mode == "horizontal":
        # Horizontal groups: primary axis is X, secondary is Y
        if abs(y1 - y2) < threshold:
            # Roughly aligned: straight line
            seg_id = _next_id("adj_conn")
            _, seg_reqs = _line(page_id, x1, y1, x2, y2,
                                color=c, weight_pt=weight_pt, dash=dash,
                                end_arrow=end_arrow, object_id=seg_id)
            reqs.extend(seg_reqs)
        else:
            # Z-path: horizontal, vertical, horizontal
            mid_x = (x1 + x2) / 2
            seg1_id = _next_id("adj_conn")
            _, s1 = _line(page_id, x1, y1, mid_x, y1,
                          color=c, weight_pt=weight_pt, dash=dash, object_id=seg1_id)
            reqs.extend(s1)

            seg2_id = _next_id("adj_conn")
            _, s2 = _line(page_id, mid_x, y1, mid_x, y2,
                          color=c, weight_pt=weight_pt, dash=dash, object_id=seg2_id)
            reqs.extend(s2)

            seg3_id = _next_id("adj_conn")
            _, s3 = _line(page_id, mid_x, y2, x2, y2,
                          color=c, weight_pt=weight_pt, dash=dash,
                          end_arrow=end_arrow, object_id=seg3_id)
            reqs.extend(s3)
    else:
        # Vertical groups: primary axis is Y, secondary is X
        if abs(x1 - x2) < threshold:
            seg_id = _next_id("adj_conn")
            _, seg_reqs = _line(page_id, x1, y1, x2, y2,
                                color=c, weight_pt=weight_pt, dash=dash,
                                end_arrow=end_arrow, object_id=seg_id)
            reqs.extend(seg_reqs)
        else:
            # Z-path: vertical, horizontal, vertical
            mid_y = (y1 + y2) / 2
            seg1_id = _next_id("adj_conn")
            _, s1 = _line(page_id, x1, y1, x1, mid_y,
                          color=c, weight_pt=weight_pt, dash=dash, object_id=seg1_id)
            reqs.extend(s1)

            seg2_id = _next_id("adj_conn")
            _, s2 = _line(page_id, x1, mid_y, x2, mid_y,
                          color=c, weight_pt=weight_pt, dash=dash, object_id=seg2_id)
            reqs.extend(s2)

            seg3_id = _next_id("adj_conn")
            _, s3 = _line(page_id, x2, mid_y, x2, y2,
                          color=c, weight_pt=weight_pt, dash=dash,
                          end_arrow=end_arrow, object_id=seg3_id)
            reqs.extend(s3)

    # Optional label at midpoint
    if label:
        mid_lx = (x1 + x2) / 2 - 0.4
        mid_ly = (y1 + y2) / 2 - 0.15
        label_id = _next_id("clabel")
        reqs.append({
            "createShape": {
                "objectId": label_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": page_id,
                    "size": {
                        "width": {"magnitude": to_emu(0.8), "unit": "EMU"},
                        "height": {"magnitude": to_emu(0.3), "unit": "EMU"},
                    },
                    "transform": {
                        "scaleX": 1, "scaleY": 1,
                        "translateX": to_emu(mid_lx),
                        "translateY": to_emu(mid_ly),
                        "unit": "EMU",
                    },
                },
            }
        })
        reqs.append({
            "insertText": {
                "objectId": label_id,
                "text": label,
                "insertionIndex": 0,
            }
        })
        reqs.append({
            "updateTextStyle": {
                "objectId": label_id,
                "textRange": {"type": "ALL"},
                "style": {
                    "fontFamily": "Arial",
                    "fontSize": {"magnitude": label_font_size, "unit": "PT"},
                    "foregroundColor": {"opaqueColor": {"rgbColor": c}},
                },
                "fields": "fontFamily,fontSize,foregroundColor",
            }
        })
        reqs.append({
            "updateParagraphStyle": {
                "objectId": label_id,
                "textRange": {"type": "ALL"},
                "style": {"alignment": "CENTER"},
                "fields": "alignment",
            }
        })

    return reqs


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render_container_box(page_id: str, container: Container,
                          color_index: int = 0) -> tuple[str, list[dict]]:
    """Render the container background rectangle with title bar."""
    fill = container.fill or CONTAINER_FILLS[color_index % len(CONTAINER_FILLS)]
    border = container.border_color or CONTAINER_BORDERS[color_index % len(CONTAINER_BORDERS)]

    oid = _next_id(f"container_{container.id}")
    reqs = []

    reqs.append({
        "createShape": {
            "objectId": oid,
            "shapeType": "RECTANGLE",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {
                    "width": {"magnitude": to_emu(container.w), "unit": "EMU"},
                    "height": {"magnitude": to_emu(container.h), "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1, "scaleY": 1,
                    "translateX": to_emu(container.x),
                    "translateY": to_emu(container.y),
                    "unit": "EMU",
                },
            },
        }
    })

    reqs.append({
        "updateShapeProperties": {
            "objectId": oid,
            "shapeProperties": {
                "shapeBackgroundFill": _solid_fill(fill, alpha=0.6),
                "outline": _outline(border, weight_pt=1.5, dash=container.border_dash),
            },
            "fields": "shapeBackgroundFill,outline",
        }
    })

    title_id = _next_id(f"ctitle_{container.id}")
    reqs.append({
        "createShape": {
            "objectId": title_id,
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {
                    "width": {"magnitude": to_emu(container.w - 0.2), "unit": "EMU"},
                    "height": {"magnitude": to_emu(TITLE_BAR_HEIGHT), "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1, "scaleY": 1,
                    "translateX": to_emu(container.x + 0.1),
                    "translateY": to_emu(container.y + 0.02),
                    "unit": "EMU",
                },
            },
        }
    })

    reqs.extend(_insert_shape_text(
        title_id, container.title,
        text_color=TITLE_COLOR,
        font_size=TITLE_FONT_SIZE,
        bold=TITLE_FONT_BOLD,
        alignment="START",
    ))

    return oid, reqs


def _render_child(page_id: str, child: dict) -> tuple[str, list[dict]]:
    """Render a single child shape. Returns (object_id, requests)."""
    ctype = child.get("type", "rectangle")
    style = CHILD_STYLES.get(ctype, CHILD_STYLES["rectangle"])
    label = child.get("label", child["id"])

    x, y, w, h = child["_x"], child["_y"], child["_w"], child["_h"]

    shape_fn_map = {
        "rectangle": rectangle,
        "rounded_rectangle": rounded_rectangle,
        "ellipse": ellipse,
        "database": rectangle,
        "service": rounded_rectangle,
        "queue": rectangle,
        "cache": rounded_rectangle,
    }
    shape_fn = shape_fn_map.get(ctype, rectangle)

    oid, reqs = shape_fn(
        page_id, x, y, w, h,
        text=label,
        fill=style["fill"],
        border_color=style["border"],
        font_size=9,
        bold=False,
        text_color={"red": 0.15, "green": 0.15, "blue": 0.15},
    )

    return oid, reqs


def render_containers(page_id: str,
                      containers: list[Container],
                      connectors_spec: list[dict] | None = None,
                      standalone_nodes: list[dict] | None = None,
                      area_x: float = 1.0, area_y: float = 1.0,
                      area_w: float = 8.0, area_h: float = 4.3,
                      layout_mode: str = "horizontal",
                      ) -> list[dict]:
    """Render containers with children and optional connectors onto a slide.

    Uses the 2-layer layout model:
      layout_mode="horizontal": groups left-to-right, children top-to-bottom
      layout_mode="vertical": groups top-to-bottom, children left-to-right
      layout_mode="grid": legacy grid layout (no adjacency enforcement)

    Connectors are validated for adjacency (cross-group connectors must
    connect adjacent groups; intra-group connectors must connect adjacent
    children). Invalid connectors are silently skipped.

    Z-order: containers (back) -> children -> standalone nodes -> connectors (front).
    """
    # Auto-position containers
    auto_position_containers(containers, area_x, area_y, area_w, area_h,
                             layout_mode=layout_mode)

    requests = []
    shape_map: dict[str, dict] = {}

    # Phase 1: Render container backgrounds
    for i, c in enumerate(containers):
        _, container_reqs = _render_container_box(page_id, c, color_index=i)
        requests.extend(container_reqs)

    # Phase 2: Render children
    for c in containers:
        positioned_children = _compute_child_positions(
            c, layout_mode=layout_mode)
        for child in positioned_children:
            oid, child_reqs = _render_child(page_id, child)
            requests.extend(child_reqs)

            ctype = child.get("type", "rectangle")
            type_name_map = {
                "rectangle": "rectangle",
                "rounded_rectangle": "rounded_rectangle",
                "ellipse": "ellipse",
                "database": "rectangle",
                "service": "rounded_rectangle",
                "queue": "rectangle",
                "cache": "rounded_rectangle",
            }
            shape_map[f"{c.id}/{child['id']}"] = {
                "type": type_name_map.get(ctype, "rectangle"),
                "x": child["_x"],
                "y": child["_y"],
                "width": child["_w"],
                "height": child["_h"],
            }

    # Phase 3: Render standalone nodes
    if standalone_nodes:
        for node in standalone_nodes:
            ctype = node.get("type", "rectangle")
            style = CHILD_STYLES.get(ctype, CHILD_STYLES["rectangle"])
            shape_fn_map = {
                "rectangle": rectangle,
                "rounded_rectangle": rounded_rectangle,
                "ellipse": ellipse,
            }
            shape_fn = shape_fn_map.get(ctype, rectangle)
            oid, reqs = shape_fn(
                page_id, node["x"], node["y"], node["w"], node["h"],
                text=node.get("label", node["id"]),
                fill=node.get("fill", style["fill"]),
                border_color=node.get("border", style["border"]),
                font_size=node.get("font_size", 10),
                bold=node.get("bold", False),
                text_color={"red": 0.15, "green": 0.15, "blue": 0.15},
            )
            requests.extend(reqs)

            type_name_map = {
                "rectangle": "rectangle",
                "rounded_rectangle": "rounded_rectangle",
                "ellipse": "ellipse",
            }
            shape_map[node["id"]] = {
                "type": type_name_map.get(ctype, "rectangle"),
                "x": node["x"],
                "y": node["y"],
                "width": node["w"],
                "height": node["h"],
            }

    # Phase 4: Render connectors with adjacency validation
    if connectors_spec:
        use_2layer = layout_mode in ("horizontal", "vertical")
        adjacent_groups = (_build_adjacency(containers, layout_mode)
                          if use_2layer else set())

        for conn in connectors_spec:
            # Resolve shape keys
            from_key = conn.get("from_node")
            from_container_id = None
            if not from_key and "from_container" in conn and "from_child" in conn:
                from_key = f"{conn['from_container']}/{conn['from_child']}"
                from_container_id = conn["from_container"]

            to_key = conn.get("to_node")
            to_container_id = None
            if not to_key and "to_container" in conn and "to_child" in conn:
                to_key = f"{conn['to_container']}/{conn['to_child']}"
                to_container_id = conn["to_container"]

            if from_key not in shape_map or to_key not in shape_map:
                continue

            # Validate adjacency in 2-layer mode
            if use_2layer and not validate_connector(
                    conn, containers, layout_mode, adjacent_groups):
                continue  # skip non-adjacent connectors

            if use_2layer:
                # Use simplified adjacent routing
                conn_reqs = _route_adjacent_connector(
                    page_id,
                    shape_map[from_key],
                    shape_map[to_key],
                    from_cid=from_container_id,
                    to_cid=to_container_id,
                    layout_mode=layout_mode,
                    label=conn.get("label"),
                    dash=conn.get("dash", DASH_SOLID),
                    color=conn.get("color"),
                )
            else:
                # Legacy: use smart_elbow_connector with obstacle avoidance
                container_bounds = {c.id: (c.x, c.y, c.w, c.h)
                                    for c in containers}
                from_bounds = container_bounds.get(from_container_id)
                to_bounds = container_bounds.get(to_container_id)

                obstacles = []
                for c in containers:
                    if c.id != from_container_id and c.id != to_container_id:
                        obstacles.append({
                            "x": c.x, "y": c.y,
                            "width": c.w, "height": c.h,
                        })

                _, conn_reqs = smart_elbow_connector(
                    page_id,
                    shape_map[from_key],
                    shape_map[to_key],
                    from_container_bounds=from_bounds,
                    to_container_bounds=to_bounds,
                    obstacles=obstacles,
                    label=conn.get("label"),
                    dash=conn.get("dash", DASH_SOLID),
                    color=conn.get("color"),
                )
                conn_reqs = conn_reqs  # already a list from tuple

            requests.extend(conn_reqs)

    return requests
