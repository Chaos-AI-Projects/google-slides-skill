"""
Connector logic for Google Slides diagrams -- Phase 4, Step 2 + Phases A/B/C.

Provides arrow routing between shape edges with anchor point calculation,
straight and single-elbow connectors, smart edge selection based on
container adjacency, and obstacle-aware routing.
"""

import math
from .shapes import (
    to_emu, _next_id, BORDER_DEFAULT, DEFAULT_BORDER_WEIGHT_PT,
    DASH_SOLID, DASH_DASH, ARROW_NONE, ARROW_FILLED, ARROW_OPEN,
    ARROW_DIAMOND,
)


# ---------------------------------------------------------------------------
# Anchor point calculation
# ---------------------------------------------------------------------------

def _rect_center(x: float, y: float, w: float, h: float) -> tuple[float, float]:
    """Return the center of a rectangle."""
    return x + w / 2, y + h / 2


def rect_edge_point(x: float, y: float, w: float, h: float,
                    target_x: float, target_y: float) -> tuple[float, float]:
    """Find where a line from the rectangle center to a target point
    intersects the rectangle border.

    All values in inches. Returns (edge_x, edge_y).
    """
    cx, cy = _rect_center(x, y, w, h)
    dx = target_x - cx
    dy = target_y - cy

    if dx == 0 and dy == 0:
        return cx, y  # degenerate: same point, use top edge

    hw, hh = w / 2, h / 2

    # Check intersection with each edge
    if dx != 0:
        # Right or left edge
        tx = hw / abs(dx)
    else:
        tx = float("inf")

    if dy != 0:
        ty = hh / abs(dy)
    else:
        ty = float("inf")

    t = min(tx, ty)
    return cx + dx * t, cy + dy * t


def ellipse_edge_point(x: float, y: float, w: float, h: float,
                       target_x: float, target_y: float) -> tuple[float, float]:
    """Find where a line from the ellipse center to a target intersects
    the ellipse border."""
    cx, cy = _rect_center(x, y, w, h)
    dx = target_x - cx
    dy = target_y - cy

    if dx == 0 and dy == 0:
        return cx, y  # top of ellipse

    a, b = w / 2, h / 2
    # Parametric: point on ellipse at angle theta
    angle = math.atan2(dy / b if b else 0, dx / a if a else 0)
    return cx + a * math.cos(angle), cy + b * math.sin(angle)


def diamond_edge_point(x: float, y: float, w: float, h: float,
                       target_x: float, target_y: float) -> tuple[float, float]:
    """Find where a line from the diamond center to a target intersects
    the diamond border. Diamond vertices are at midpoints of bounding box edges."""
    cx, cy = _rect_center(x, y, w, h)
    dx = target_x - cx
    dy = target_y - cy

    if dx == 0 and dy == 0:
        return cx, y  # top vertex

    hw, hh = w / 2, h / 2
    # Diamond has 4 edges; the intersection uses the L1 norm
    adx, ady = abs(dx), abs(dy)
    if adx * hh + ady * hw == 0:
        return cx, y
    t = (hw * hh) / (adx * hh + ady * hw)
    return cx + dx * t, cy + dy * t


# Shape type to edge function mapping
EDGE_FUNCTIONS = {
    "rectangle": rect_edge_point,
    "rounded_rectangle": rect_edge_point,
    "ellipse": ellipse_edge_point,
    "diamond": diamond_edge_point,
    "parallelogram": rect_edge_point,  # approximate
}


def edge_point(shape_type: str, x: float, y: float, w: float, h: float,
               target_x: float, target_y: float) -> tuple[float, float]:
    """Get the edge intersection point for a shape toward a target."""
    fn = EDGE_FUNCTIONS.get(shape_type, rect_edge_point)
    return fn(x, y, w, h, target_x, target_y)


def directed_edge_point(shape_type: str, x: float, y: float, w: float, h: float,
                        side: str) -> tuple[float, float]:
    """Get the midpoint of a specific edge side (left, right, top, bottom).

    For rectangles, returns the exact midpoint of the requested edge.
    For ellipses, returns the point on the ellipse at the cardinal direction.
    For diamonds, returns the vertex at the requested direction.
    """
    cx, cy = x + w / 2, y + h / 2

    # Map side to a far-away target in the appropriate direction
    targets = {
        "right": (x + w + 100, cy),
        "left": (x - 100, cy),
        "top": (cx, y - 100),
        "bottom": (cx, y + h + 100),
    }
    target_x, target_y = targets[side]
    return edge_point(shape_type, x, y, w, h, target_x, target_y)


# ---------------------------------------------------------------------------
# Obstacle detection (Phase C)
# ---------------------------------------------------------------------------

def _segments_intersect_box(x1: float, y1: float, x2: float, y2: float,
                            bx: float, by: float, bw: float, bh: float,
                            margin: float = 0.05) -> bool:
    """Check if line segment (x1,y1)-(x2,y2) intersects axis-aligned box
    (bx, by, bw, bh) with optional margin."""
    # Expand box by margin
    rx = bx - margin
    ry = by - margin
    rw = bw + 2 * margin
    rh = bh + 2 * margin

    # Use parametric clipping (Cohen-Sutherland-style)
    dx = x2 - x1
    dy = y2 - y1
    t_min = 0.0
    t_max = 1.0

    for edge_p, edge_q in [
        (-dx, x1 - rx),        # left
        (dx, rx + rw - x1),    # right
        (-dy, y1 - ry),        # top
        (dy, ry + rh - y1),    # bottom
    ]:
        if abs(edge_p) < 1e-9:
            if edge_q < 0:
                return False
        else:
            t = edge_q / edge_p
            if edge_p < 0:
                t_min = max(t_min, t)
            else:
                t_max = min(t_max, t)
            if t_min > t_max:
                return False

    return True


def _find_obstacles_on_path(segments: list[tuple], obstacles: list[dict],
                            from_shape: dict, to_shape: dict) -> list[dict]:
    """Find obstacles that intersect any segment of the path.

    Excludes from_shape and to_shape from the obstacle list.
    """
    blocking = []
    for obs in obstacles:
        # Skip the source and destination shapes
        if (abs(obs["x"] - from_shape["x"]) < 0.01 and
            abs(obs["y"] - from_shape["y"]) < 0.01):
            continue
        if (abs(obs["x"] - to_shape["x"]) < 0.01 and
            abs(obs["y"] - to_shape["y"]) < 0.01):
            continue

        for (sx, sy, ex, ey) in segments:
            if _segments_intersect_box(sx, sy, ex, ey,
                                       obs["x"], obs["y"],
                                       obs["width"], obs["height"]):
                blocking.append(obs)
                break

    return blocking


# ---------------------------------------------------------------------------
# Connector creation
# ---------------------------------------------------------------------------

def straight_connector(page_id: str,
                       from_shape: dict, to_shape: dict, *,
                       color: dict = None, weight_pt: float = DEFAULT_BORDER_WEIGHT_PT,
                       dash: str = DASH_SOLID,
                       start_arrow: str = ARROW_NONE,
                       end_arrow: str = ARROW_FILLED,
                       label: str = None,
                       label_font_size: float = 9,
                       object_id: str = None) -> tuple[str, list[dict]]:
    """Draw a straight connector between two shapes.

    Each shape dict must have: type, x, y, width, height.
    Optionally provide a text label placed at the midpoint.

    Returns (object_id, list_of_requests).
    """
    oid = object_id or _next_id("conn")
    c = color or BORDER_DEFAULT

    # Calculate edge-to-edge points
    from_cx = from_shape["x"] + from_shape["width"] / 2
    from_cy = from_shape["y"] + from_shape["height"] / 2
    to_cx = to_shape["x"] + to_shape["width"] / 2
    to_cy = to_shape["y"] + to_shape["height"] / 2

    p1 = edge_point(from_shape["type"], from_shape["x"], from_shape["y"],
                     from_shape["width"], from_shape["height"], to_cx, to_cy)
    p2 = edge_point(to_shape["type"], to_shape["x"], to_shape["y"],
                     to_shape["width"], to_shape["height"], from_cx, from_cy)

    x1, y1 = p1
    x2, y2 = p2

    reqs = []

    # Create the line
    min_x = min(x1, x2)
    min_y = min(y1, y2)
    w = abs(x2 - x1)
    h = abs(y2 - y1)

    reqs.append({
        "createLine": {
            "objectId": oid,
            "lineCategory": "STRAIGHT",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {
                    "width": {"magnitude": to_emu(w) or 1, "unit": "EMU"},
                    "height": {"magnitude": to_emu(h) or 1, "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1 if x2 >= x1 else -1,
                    "scaleY": 1 if y2 >= y1 else -1,
                    "translateX": to_emu(min_x),
                    "translateY": to_emu(min_y),
                    "unit": "EMU",
                },
            },
        }
    })

    reqs.append({
        "updateLineProperties": {
            "objectId": oid,
            "lineProperties": {
                "lineFill": {
                    "solidFill": {"color": {"rgbColor": c}, "alpha": 1.0}
                },
                "weight": {"magnitude": weight_pt, "unit": "PT"},
                "dashStyle": dash,
                "startArrow": start_arrow,
                "endArrow": end_arrow,
            },
            "fields": "lineFill,weight,dashStyle,startArrow,endArrow",
        }
    })

    # Optional label at midpoint
    all_ids = [oid]
    if label:
        mid_x = (x1 + x2) / 2 - 0.4
        mid_y = (y1 + y2) / 2 - 0.15
        label_id = _next_id("clabel")
        all_ids.append(label_id)
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
                        "translateX": to_emu(mid_x),
                        "translateY": to_emu(mid_y),
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

    return oid, reqs


def elbow_connector(page_id: str,
                    from_shape: dict, to_shape: dict, *,
                    color: dict = None, weight_pt: float = DEFAULT_BORDER_WEIGHT_PT,
                    dash: str = DASH_SOLID,
                    end_arrow: str = ARROW_FILLED,
                    object_id: str = None) -> tuple[str, list[dict]]:
    """Draw a single-elbow (L-shaped) connector using two line segments.

    Goes horizontal first, then vertical. Returns the ID of the first
    segment and the combined request list.
    """
    c = color or BORDER_DEFAULT

    from_cx = from_shape["x"] + from_shape["width"] / 2
    from_cy = from_shape["y"] + from_shape["height"] / 2
    to_cx = to_shape["x"] + to_shape["width"] / 2
    to_cy = to_shape["y"] + to_shape["height"] / 2

    # Elbow point: horizontal from source, then vertical to target
    elbow_x = to_cx
    elbow_y = from_cy

    # Edge points
    p1 = edge_point(from_shape["type"], from_shape["x"], from_shape["y"],
                     from_shape["width"], from_shape["height"], elbow_x, elbow_y)
    p2 = edge_point(to_shape["type"], to_shape["x"], to_shape["y"],
                     to_shape["width"], to_shape["height"], elbow_x, elbow_y)

    reqs = []

    # Horizontal segment: p1 -> elbow
    seg1_id = object_id or _next_id("elbow")
    from .shapes import line as _line
    _, seg1_reqs = _line(page_id, p1[0], p1[1], elbow_x, elbow_y,
                         color=c, weight_pt=weight_pt, dash=dash,
                         object_id=seg1_id)
    reqs.extend(seg1_reqs)

    # Vertical segment: elbow -> p2
    seg2_id = _next_id("elbow")
    _, seg2_reqs = _line(page_id, elbow_x, elbow_y, p2[0], p2[1],
                         color=c, weight_pt=weight_pt, dash=dash,
                         end_arrow=end_arrow, object_id=seg2_id)
    reqs.extend(seg2_reqs)

    return seg1_id, reqs


def _determine_sides(from_container_bounds: tuple, to_container_bounds: tuple,
                     ) -> tuple[str, str]:
    """Determine exit/entry sides based on relative container positions.

    Uses gap-based analysis: if containers are separated vertically
    (no horizontal overlap in their x-ranges), use left/right routing.
    If separated horizontally (no vertical overlap), use top/bottom.
    When containers overlap in both axes, use the axis with less overlap
    (i.e. more gap between them).

    Returns (from_side, to_side).
    """
    fx, fy, fw, fh = from_container_bounds
    tx, ty, tw, th = to_container_bounds

    # Compute gaps between container edges (negative = overlap)
    h_gap = max(tx - (fx + fw), fx - (tx + tw))  # horizontal gap
    v_gap = max(ty - (fy + fh), fy - (ty + th))  # vertical gap

    # If one axis has a clear gap and the other overlaps, use the gap axis
    if h_gap > 0 and v_gap <= 0:
        # Containers side by side horizontally
        fcx = fx + fw / 2
        tcx = tx + tw / 2
        if tcx >= fcx:
            return "right", "left"
        else:
            return "left", "right"
    elif v_gap > 0 and h_gap <= 0:
        # Containers stacked vertically
        fcy = fy + fh / 2
        tcy = ty + th / 2
        if tcy >= fcy:
            return "bottom", "top"
        else:
            return "top", "bottom"
    else:
        # Both axes have gaps or both overlap -- use the larger gap
        fcx, fcy = fx + fw / 2, fy + fh / 2
        tcx, tcy = tx + tw / 2, ty + th / 2
        dx = tcx - fcx
        dy = tcy - fcy

        if h_gap >= v_gap:
            # Horizontal separation is larger
            if dx >= 0:
                return "right", "left"
            else:
                return "left", "right"
        else:
            # Vertical separation is larger
            if dy >= 0:
                return "bottom", "top"
            else:
                return "top", "bottom"


def _route_around_obstacles(p1: tuple, p2: tuple,
                            from_side: str, to_side: str,
                            from_shape: dict, to_shape: dict,
                            obstacles: list[dict],
                            from_container_bounds: tuple | None = None,
                            to_container_bounds: tuple | None = None,
                            ) -> list[tuple]:
    """Generate a multi-segment path that avoids obstacles.

    Uses 3-segment Z-shaped routing: the turn happens in the gap between
    containers rather than at the target's coordinate, preventing long
    segments that fly across the diagram.

    Returns list of (x1, y1, x2, y2) line segments.
    """
    x1, y1 = p1
    x2, y2 = p2

    # Determine elbow routing direction based on sides
    horizontal_first = from_side in ("left", "right")

    # Calculate midpoint for the turn -- place it in the gap between containers
    if horizontal_first:
        # Horizontal-first: 3-segment Z-path (horizontal, vertical, horizontal)
        # The vertical jog goes at the midpoint between source and target x
        if from_container_bounds and to_container_bounds:
            fcx, fcy, fcw, fch = from_container_bounds
            tcx, tcy, tcw, tch = to_container_bounds
            if from_side == "right":
                mid_x = (fcx + fcw + tcx) / 2
            else:
                mid_x = (tcx + tcw + fcx) / 2
        else:
            mid_x = (x1 + x2) / 2
        segments = [
            (x1, y1, mid_x, y1),    # horizontal from source
            (mid_x, y1, mid_x, y2), # vertical jog in the gap
            (mid_x, y2, x2, y2),    # horizontal to target
        ]
    else:
        # Vertical-first: 3-segment Z-path (vertical, horizontal, vertical)
        # The horizontal jog goes at the midpoint between source and target y
        if from_container_bounds and to_container_bounds:
            fcx, fcy, fcw, fch = from_container_bounds
            tcx, tcy, tcw, tch = to_container_bounds
            if from_side == "bottom":
                mid_y = (fcy + fch + tcy) / 2
            else:
                mid_y = (tcy + tch + fcy) / 2
        else:
            mid_y = (y1 + y2) / 2
        segments = [
            (x1, y1, x1, mid_y),    # vertical from source
            (x1, mid_y, x2, mid_y), # horizontal jog in the gap
            (x2, mid_y, x2, y2),    # vertical to target
        ]

    if not obstacles:
        return segments

    # Check if any obstacle blocks the path
    blocking = _find_obstacles_on_path(segments, obstacles, from_shape, to_shape)
    if not blocking:
        return segments

    # Route around: find the combined bounding box of blocking obstacles
    # and add waypoints to go around them
    obs_min_x = min(o["x"] for o in blocking)
    obs_min_y = min(o["y"] for o in blocking)
    obs_max_x = max(o["x"] + o["width"] for o in blocking)
    obs_max_y = max(o["y"] + o["height"] for o in blocking)

    margin = 0.15  # clearance around obstacles

    if horizontal_first:
        # Try routing above or below the obstacle
        dist_above = abs(y1 - (obs_min_y - margin))
        dist_below = abs((obs_max_y + margin) - y1)
        use_above = dist_above <= dist_below

        if use_above:
            detour_y = obs_min_y - margin
        else:
            detour_y = obs_max_y + margin

        # 5-segment route around obstacle
        mid_x1 = obs_min_x - margin
        mid_x2 = obs_max_x + margin
        segments = [
            (x1, y1, mid_x1, y1),
            (mid_x1, y1, mid_x1, detour_y),
            (mid_x1, detour_y, mid_x2, detour_y),
            (mid_x2, detour_y, mid_x2, y2),
            (mid_x2, y2, x2, y2),
        ]
    else:
        # Vertical-first: try routing left or right of obstacle
        dist_left = abs(x1 - (obs_min_x - margin))
        dist_right = abs((obs_max_x + margin) - x1)
        use_left = dist_left <= dist_right

        if use_left:
            detour_x = obs_min_x - margin
        else:
            detour_x = obs_max_x + margin

        mid_y1 = obs_min_y - margin
        mid_y2 = obs_max_y + margin
        segments = [
            (x1, y1, x1, mid_y1),
            (x1, mid_y1, detour_x, mid_y1),
            (detour_x, mid_y1, detour_x, mid_y2),
            (detour_x, mid_y2, x2, mid_y2),
            (x2, mid_y2, x2, y2),
        ]

    return segments


def smart_elbow_connector(page_id: str,
                          from_shape: dict, to_shape: dict, *,
                          from_container_bounds: tuple | None = None,
                          to_container_bounds: tuple | None = None,
                          preferred_from_side: str | None = None,
                          preferred_to_side: str | None = None,
                          obstacles: list[dict] | None = None,
                          color: dict = None,
                          weight_pt: float = DEFAULT_BORDER_WEIGHT_PT,
                          dash: str = DASH_SOLID,
                          end_arrow: str = ARROW_FILLED,
                          label: str = None,
                          label_font_size: float = 9,
                          object_id: str = None) -> tuple[str, list[dict]]:
    """Draw a smart elbow connector that picks routing based on container
    positions (Phase A + B) and avoids obstacles (Phase C).

    If from_container_bounds == to_container_bounds (same container),
    falls back to a straight connector.

    Args:
        from_shape/to_shape: Shape dicts with type, x, y, width, height.
        from_container_bounds: (x, y, w, h) of source container.
        to_container_bounds: (x, y, w, h) of target container.
        preferred_from_side: Override exit side (left/right/top/bottom).
        preferred_to_side: Override entry side.
        obstacles: List of shape dicts to route around.
        color, weight_pt, dash, end_arrow: Line styling.
        label: Optional text label.
        object_id: Optional ID prefix.
    """
    c = color or BORDER_DEFAULT

    # Same container -> straight connector
    if (from_container_bounds and to_container_bounds and
        from_container_bounds == to_container_bounds):
        return straight_connector(
            page_id, from_shape, to_shape,
            color=c, weight_pt=weight_pt, dash=dash,
            end_arrow=end_arrow, label=label,
            label_font_size=label_font_size,
            object_id=object_id,
        )

    # Determine exit/entry sides (Phase B)
    if preferred_from_side and preferred_to_side:
        from_side, to_side = preferred_from_side, preferred_to_side
    elif from_container_bounds and to_container_bounds:
        from_side, to_side = _determine_sides(
            from_container_bounds, to_container_bounds)
    else:
        # Fallback: determine from shape centers
        fcx = from_shape["x"] + from_shape["width"] / 2
        fcy = from_shape["y"] + from_shape["height"] / 2
        tcx = to_shape["x"] + to_shape["width"] / 2
        tcy = to_shape["y"] + to_shape["height"] / 2
        dx, dy = tcx - fcx, tcy - fcy
        if abs(dx) >= abs(dy):
            from_side, to_side = ("right", "left") if dx >= 0 else ("left", "right")
        else:
            from_side, to_side = ("bottom", "top") if dy >= 0 else ("top", "bottom")

    # Get directed edge points (Phase B)
    p1 = directed_edge_point(from_shape["type"], from_shape["x"], from_shape["y"],
                              from_shape["width"], from_shape["height"], from_side)
    p2 = directed_edge_point(to_shape["type"], to_shape["x"], to_shape["y"],
                              to_shape["width"], to_shape["height"], to_side)

    # Route with obstacle avoidance (Phase C)
    segments = _route_around_obstacles(
        p1, p2, from_side, to_side,
        from_shape, to_shape,
        obstacles or [],
        from_container_bounds=from_container_bounds,
        to_container_bounds=to_container_bounds,
    )

    # Filter out zero-length segments
    segments = [(sx, sy, ex, ey) for (sx, sy, ex, ey) in segments
                if abs(ex - sx) > 0.001 or abs(ey - sy) > 0.001]

    # Fallback: if all segments were filtered, use straight connector
    if not segments:
        return straight_connector(
            page_id, from_shape, to_shape,
            color=c, weight_pt=weight_pt, dash=dash,
            end_arrow=end_arrow, label=label,
            label_font_size=label_font_size,
            object_id=object_id,
        )

    # Render line segments
    from .shapes import line as _line
    reqs = []
    first_id = object_id or _next_id("selbow")

    for i, (sx, sy, ex, ey) in enumerate(segments):
        seg_id = first_id if i == 0 else _next_id("selbow")
        is_last = (i == len(segments) - 1)
        _, seg_reqs = _line(
            page_id, sx, sy, ex, ey,
            color=c, weight_pt=weight_pt, dash=dash,
            end_arrow=end_arrow if is_last else ARROW_NONE,
            object_id=seg_id,
        )
        reqs.extend(seg_reqs)

    # Optional label at midpoint of full path
    if label:
        mid_x = (p1[0] + p2[0]) / 2 - 0.4
        mid_y = (p1[1] + p2[1]) / 2 - 0.15
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
                        "translateX": to_emu(mid_x),
                        "translateY": to_emu(mid_y),
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

    return first_id, reqs
