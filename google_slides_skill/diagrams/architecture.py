"""
Architecture diagram generator -- 2-layer layout model.

Renders architecture diagrams with container groups and connectors using
the strict 2-layer hierarchy:
  - "horizontal": groups left-to-right, components top-to-bottom
  - "vertical": groups top-to-bottom, components left-to-right

Connectors are restricted to adjacent elements only.

Usage:
    groups = [
        {
            "id": "backend",
            "title": "Backend Services",
            "children": [
                {"id": "api", "label": "API Server", "type": "service"},
                {"id": "worker", "label": "Worker", "type": "service"},
            ],
        },
        {
            "id": "data",
            "title": "Data Layer",
            "children": [
                {"id": "db", "label": "PostgreSQL", "type": "database"},
                {"id": "cache", "label": "Redis", "type": "cache"},
            ],
        },
    ]
    connectors = [
        {"from_container": "backend", "from_child": "api",
         "to_container": "data", "to_child": "db", "label": "SQL"},
    ]
    requests = render_architecture(page_id, groups, connectors,
                                   layout_mode="horizontal")
"""

from __future__ import annotations

from ..containers import Container, render_containers


# ---------------------------------------------------------------------------
# Default area (matches LAYOUT_DIAGRAM)
# ---------------------------------------------------------------------------

AREA_X = 1.0
AREA_Y = 1.0
AREA_W = 8.0
AREA_H = 4.3


def render_architecture(page_id: str,
                        groups: list[dict],
                        connectors: list[dict] | None = None,
                        standalone_nodes: list[dict] | None = None,
                        area_x: float = AREA_X,
                        area_y: float = AREA_Y,
                        area_w: float = AREA_W,
                        area_h: float = AREA_H,
                        layout_mode: str = "horizontal",
                        ) -> list[dict]:
    """Render an architecture diagram with container groups.

    Args:
        page_id: Slide object ID.
        groups: List of group dicts, each with:
            id, title, children (list of child dicts).
            Optional: x, y, w, h, fill, border_color, layout, columns.
        connectors: Connector specs (see render_containers).
        standalone_nodes: Nodes outside any container.
        area_x/y/w/h: Bounding area for auto-layout.
        layout_mode: "horizontal" (groups L-R, children T-B) or
                     "vertical" (groups T-B, children L-R).

    Returns:
        List of batchUpdate request dicts.
    """
    containers = []
    for g in groups:
        c = Container(
            id=g["id"],
            title=g["title"],
            children=g.get("children", []),
            x=g.get("x"),
            y=g.get("y"),
            w=g.get("w"),
            h=g.get("h"),
            fill=g.get("fill"),
            border_color=g.get("border_color"),
            border_dash=g.get("border_dash", "DASH"),
            layout=g.get("layout", "grid"),
            columns=g.get("columns"),
        )
        containers.append(c)

    return render_containers(
        page_id, containers,
        connectors_spec=connectors,
        standalone_nodes=standalone_nodes,
        area_x=area_x, area_y=area_y,
        area_w=area_w, area_h=area_h,
        layout_mode=layout_mode,
    )
