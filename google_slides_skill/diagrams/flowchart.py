"""
Flowchart diagram generator -- Phase 4, Step 3.

Input: list of nodes and edges. Auto-layout via topological sort + grid
placement. Renders shapes and connectors onto a Google Slides page.

Usage:
    nodes = [
        {"id": "start", "label": "Start", "type": "start_end"},
        {"id": "process1", "label": "Do work", "type": "process"},
        {"id": "decide", "label": "OK?", "type": "decision"},
        {"id": "end", "label": "End", "type": "start_end"},
    ]
    edges = [
        {"from": "start", "to": "process1"},
        {"from": "process1", "to": "decide"},
        {"from": "decide", "to": "end", "label": "Yes"},
    ]
    requests = render_flowchart(page_id, nodes, edges)
"""

from __future__ import annotations

from collections import defaultdict, deque

from ..shapes import (
    rectangle, rounded_rectangle, diamond, ellipse, parallelogram,
    reset_ids, FILL_BLUE, FILL_LIGHT_BLUE, FILL_LIGHT_GRAY,
    FILL_GREEN, FILL_ORANGE, BORDER_BLUE, BORDER_DEFAULT, FILL_WHITE,
    DEFAULT_BORDER_WEIGHT_PT,
)
from ..connectors import straight_connector

# ---------------------------------------------------------------------------
# Layout constants (inches, fitting within the 8.0 x 4.3 diagram area)
# ---------------------------------------------------------------------------

# Target area (from LAYOUT_DIAGRAM: x=1.0, y=1.0, w=8.0, h=4.3)
AREA_X = 1.0
AREA_Y = 1.0
AREA_W = 8.0
AREA_H = 4.3

# Node sizes
NODE_W = 1.4
NODE_H = 0.7
DECISION_W = 1.6
DECISION_H = 1.0

# Spacing
H_SPACING = 1.5  # horizontal gap between node centers
V_SPACING = 1.2  # vertical gap between row centers

# Node type -> shape function + default fill
NODE_STYLES = {
    "process": {
        "shape_fn": rectangle,
        "fill": FILL_LIGHT_BLUE,
        "border": BORDER_BLUE,
        "w": NODE_W,
        "h": NODE_H,
    },
    "decision": {
        "shape_fn": diamond,
        "fill": FILL_LIGHT_GRAY,
        "border": BORDER_DEFAULT,
        "w": DECISION_W,
        "h": DECISION_H,
    },
    "start_end": {
        "shape_fn": rounded_rectangle,
        "fill": FILL_GREEN,
        "border": {"red": 0.15, "green": 0.50, "blue": 0.25},
        "w": NODE_W,
        "h": NODE_H,
    },
    "io": {
        "shape_fn": parallelogram,
        "fill": FILL_ORANGE,
        "border": {"red": 0.70, "green": 0.40, "blue": 0.10},
        "w": NODE_W,
        "h": NODE_H,
    },
}


# ---------------------------------------------------------------------------
# Topological layout
# ---------------------------------------------------------------------------

def _topo_levels(nodes: list[dict], edges: list[dict]) -> dict[str, int]:
    """Assign each node to a level (row) using topological ordering.

    Nodes with no incoming edges get level 0. Each subsequent node gets
    max(predecessor levels) + 1.
    """
    node_ids = {n["id"] for n in nodes}
    children = defaultdict(list)
    in_degree = defaultdict(int)
    for n in nodes:
        in_degree[n["id"]] = 0
    for e in edges:
        if e["from"] in node_ids and e["to"] in node_ids:
            children[e["from"]].append(e["to"])
            in_degree[e["to"]] += 1

    levels = {}
    queue = deque()
    for nid in node_ids:
        if in_degree[nid] == 0:
            queue.append(nid)
            levels[nid] = 0

    while queue:
        nid = queue.popleft()
        for child in children[nid]:
            new_level = levels[nid] + 1
            if child not in levels or levels[child] < new_level:
                levels[child] = new_level
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # Handle any unvisited nodes (cycles) -- place at max level + 1
    max_level = max(levels.values()) if levels else 0
    for n in nodes:
        if n["id"] not in levels:
            levels[n["id"]] = max_level + 1

    return levels


def _grid_positions(nodes: list[dict], edges: list[dict],
                    area_x: float, area_y: float,
                    area_w: float, area_h: float) -> dict[str, tuple[float, float, float, float]]:
    """Compute (x, y, w, h) for each node, centered within rows.

    Returns dict: node_id -> (x, y, w, h) in inches.
    """
    levels = _topo_levels(nodes, edges)
    node_map = {n["id"]: n for n in nodes}

    # Group nodes by level
    rows: dict[int, list[str]] = defaultdict(list)
    for nid, level in sorted(levels.items(), key=lambda kv: kv[1]):
        rows[level].append(nid)

    num_rows = len(rows)
    if num_rows == 0:
        return {}

    # Calculate spacing to fit within area
    v_space = min(V_SPACING, area_h / max(num_rows, 1))

    positions = {}
    for level in sorted(rows.keys()):
        row_nodes = rows[level]
        num_cols = len(row_nodes)

        # Get widths for this row
        widths = []
        for nid in row_nodes:
            ntype = node_map[nid].get("type", "process")
            style = NODE_STYLES.get(ntype, NODE_STYLES["process"])
            widths.append(style["w"])

        total_w = sum(widths) + H_SPACING * max(num_cols - 1, 0)
        start_x = area_x + (area_w - total_w) / 2

        # Vertical centering
        y = area_y + level * v_space

        x_cursor = start_x
        for i, nid in enumerate(row_nodes):
            ntype = node_map[nid].get("type", "process")
            style = NODE_STYLES.get(ntype, NODE_STYLES["process"])
            nw, nh = style["w"], style["h"]
            positions[nid] = (x_cursor, y, nw, nh)
            x_cursor += nw + H_SPACING

    return positions


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_flowchart(page_id: str, nodes: list[dict], edges: list[dict], *,
                     area_x: float = AREA_X, area_y: float = AREA_Y,
                     area_w: float = AREA_W, area_h: float = AREA_H,
                     ) -> list[dict]:
    """Render a flowchart onto a slide page.

    Args:
        page_id: The slide object ID.
        nodes: List of dicts with keys: id, label, type (process|decision|start_end|io).
        edges: List of dicts with keys: from, to, and optional label.
        area_x/y/w/h: Bounding area in inches.

    Returns:
        List of batchUpdate request dicts.
    """
    positions = _grid_positions(nodes, edges, area_x, area_y, area_w, area_h)
    node_map = {n["id"]: n for n in nodes}
    requests = []

    # Render nodes
    shape_info = {}  # node_id -> {type, x, y, width, height} for connector routing
    for nid, (x, y, w, h) in positions.items():
        node = node_map[nid]
        ntype = node.get("type", "process")
        style = NODE_STYLES.get(ntype, NODE_STYLES["process"])

        shape_fn = style["shape_fn"]
        _, reqs = shape_fn(
            page_id, x, y, w, h,
            text=node["label"],
            fill=style["fill"],
            border_color=style["border"],
            font_size=10,
            text_color={"red": 0.1, "green": 0.1, "blue": 0.1},
        )
        requests.extend(reqs)

        # Map shape type name for connector routing
        type_name = {
            "process": "rectangle",
            "decision": "diamond",
            "start_end": "rounded_rectangle",
            "io": "parallelogram",
        }.get(ntype, "rectangle")

        shape_info[nid] = {
            "type": type_name,
            "x": x, "y": y, "width": w, "height": h,
        }

    # Render edges
    for e in edges:
        from_id = e["from"]
        to_id = e["to"]
        if from_id not in shape_info or to_id not in shape_info:
            continue

        _, reqs = straight_connector(
            page_id,
            shape_info[from_id],
            shape_info[to_id],
            label=e.get("label"),
        )
        requests.extend(reqs)

    return requests
