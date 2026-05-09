"""
Simple chart generator -- Phase 4, Step 5.

Bar charts and comparison bars using native Slides shapes. For complex
charts, recommend embedding a Google Sheets chart instead.

Usage:
    # Simple bar chart
    data = [
        {"label": "Q1", "value": 100},
        {"label": "Q2", "value": 150},
        {"label": "Q3", "value": 120},
        {"label": "Q4", "value": 180},
    ]
    requests = render_bar_chart(page_id, data, title="Revenue by Quarter")

    # Comparison bars (two series)
    data = [
        {"label": "Q1", "value_a": 100, "value_b": 80},
        {"label": "Q2", "value_a": 150, "value_b": 120},
    ]
    requests = render_comparison_chart(page_id, data,
        legend_a="2025", legend_b="2024")
"""

from __future__ import annotations

from ..shapes import (
    rectangle, text_label, line, _next_id,
    FILL_BLUE, FILL_LIGHT_BLUE, FILL_ORANGE, FILL_LIGHT_GRAY,
    BORDER_DEFAULT, to_emu,
)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

AREA_X = 1.0
AREA_Y = 1.0
AREA_W = 8.0
AREA_H = 4.3

# Chart margins within the area
CHART_LEFT = 0.6   # space for Y axis labels
CHART_BOTTOM = 0.5  # space for X axis labels
CHART_TOP = 0.4    # space for title
CHART_RIGHT = 0.3


# ---------------------------------------------------------------------------
# Bar chart
# ---------------------------------------------------------------------------

def render_bar_chart(page_id: str, data: list[dict], *,
                     title: str = None,
                     bar_color: dict = None,
                     area_x: float = AREA_X, area_y: float = AREA_Y,
                     area_w: float = AREA_W, area_h: float = AREA_H,
                     ) -> list[dict]:
    """Render a simple bar chart.

    Args:
        page_id: Slide object ID.
        data: List of dicts with keys: label, value.
        title: Optional chart title.
        bar_color: Fill color for bars (default: FILL_BLUE).

    Returns:
        List of batchUpdate request dicts.
    """
    if not data:
        return []

    bc = bar_color or FILL_BLUE
    requests = []

    # Compute chart area
    cx = area_x + CHART_LEFT
    cy = area_y + CHART_TOP
    cw = area_w - CHART_LEFT - CHART_RIGHT
    ch = area_h - CHART_TOP - CHART_BOTTOM

    # Title
    if title:
        _, reqs = text_label(
            page_id, area_x, area_y, area_w, CHART_TOP,
            title, font_size=12, bold=True, alignment="CENTER",
        )
        requests.extend(reqs)

    max_val = max(d["value"] for d in data) or 1
    n = len(data)

    # Bar dimensions
    bar_gap = 0.1
    total_gap = bar_gap * (n + 1)
    bar_w = min((cw - total_gap) / n, 1.0)
    # Recalculate total width and center
    total_bars_w = n * bar_w + (n + 1) * bar_gap
    bars_start_x = cx + (cw - total_bars_w) / 2

    # Draw Y axis line
    _, reqs = line(page_id, cx, cy, cx, cy + ch,
                   color=BORDER_DEFAULT, weight_pt=1.0)
    requests.extend(reqs)

    # Draw X axis line
    _, reqs = line(page_id, cx, cy + ch, cx + cw, cy + ch,
                   color=BORDER_DEFAULT, weight_pt=1.0)
    requests.extend(reqs)

    # Y-axis labels (0 and max)
    _, reqs = text_label(
        page_id, area_x, cy + ch - 0.15, CHART_LEFT - 0.05, 0.2,
        "0", font_size=8, alignment="END",
    )
    requests.extend(reqs)
    _, reqs = text_label(
        page_id, area_x, cy - 0.05, CHART_LEFT - 0.05, 0.2,
        str(int(max_val)), font_size=8, alignment="END",
    )
    requests.extend(reqs)

    # Bars and labels
    for i, d in enumerate(data):
        val = d["value"]
        label = d["label"]
        bar_h = (val / max_val) * ch if max_val > 0 else 0
        bx = bars_start_x + bar_gap + i * (bar_w + bar_gap)
        by = cy + ch - bar_h

        # Bar
        _, reqs = rectangle(
            page_id, bx, by, bar_w, bar_h,
            fill=bc, border_color=BORDER_DEFAULT, border_weight=0.5,
        )
        requests.extend(reqs)

        # Value label above bar
        _, reqs = text_label(
            page_id, bx, by - 0.2, bar_w, 0.2,
            str(int(val)), font_size=8, bold=True,
        )
        requests.extend(reqs)

        # X-axis label below bar
        _, reqs = text_label(
            page_id, bx - 0.1, cy + ch + 0.05, bar_w + 0.2, 0.3,
            label, font_size=8,
        )
        requests.extend(reqs)

    return requests


# ---------------------------------------------------------------------------
# Comparison bars (two series side-by-side)
# ---------------------------------------------------------------------------

def render_comparison_chart(page_id: str, data: list[dict], *,
                            title: str = None,
                            legend_a: str = "A",
                            legend_b: str = "B",
                            color_a: dict = None,
                            color_b: dict = None,
                            area_x: float = AREA_X, area_y: float = AREA_Y,
                            area_w: float = AREA_W, area_h: float = AREA_H,
                            ) -> list[dict]:
    """Render a comparison bar chart with two series.

    Args:
        page_id: Slide object ID.
        data: List of dicts with keys: label, value_a, value_b.
        legend_a/b: Series names for the legend.
        color_a/b: Fill colors for each series.

    Returns:
        List of batchUpdate request dicts.
    """
    if not data:
        return []

    ca = color_a or FILL_BLUE
    cb = color_b or FILL_ORANGE
    requests = []

    # Chart area (extra top space for legend)
    legend_h = 0.3
    cx = area_x + CHART_LEFT
    cy = area_y + CHART_TOP + legend_h
    cw = area_w - CHART_LEFT - CHART_RIGHT
    ch = area_h - CHART_TOP - CHART_BOTTOM - legend_h

    # Title
    if title:
        _, reqs = text_label(
            page_id, area_x, area_y, area_w, CHART_TOP,
            title, font_size=12, bold=True, alignment="CENTER",
        )
        requests.extend(reqs)

    # Legend
    leg_x = cx + cw - 2.5
    leg_y = area_y + CHART_TOP
    # Series A swatch
    _, reqs = rectangle(page_id, leg_x, leg_y + 0.05, 0.2, 0.15, fill=ca)
    requests.extend(reqs)
    _, reqs = text_label(page_id, leg_x + 0.25, leg_y, 0.8, 0.25,
                         legend_a, font_size=8, alignment="START")
    requests.extend(reqs)
    # Series B swatch
    _, reqs = rectangle(page_id, leg_x + 1.2, leg_y + 0.05, 0.2, 0.15, fill=cb)
    requests.extend(reqs)
    _, reqs = text_label(page_id, leg_x + 1.45, leg_y, 0.8, 0.25,
                         legend_b, font_size=8, alignment="START")
    requests.extend(reqs)

    all_vals = [d["value_a"] for d in data] + [d["value_b"] for d in data]
    max_val = max(all_vals) if all_vals else 1
    n = len(data)

    # Pair dimensions
    pair_gap = 0.15
    bar_inner_gap = 0.05
    pair_w_total = cw / n
    bar_w = (pair_w_total - pair_gap - bar_inner_gap) / 2
    bar_w = min(bar_w, 0.6)

    # Axes
    _, reqs = line(page_id, cx, cy, cx, cy + ch,
                   color=BORDER_DEFAULT, weight_pt=1.0)
    requests.extend(reqs)
    _, reqs = line(page_id, cx, cy + ch, cx + cw, cy + ch,
                   color=BORDER_DEFAULT, weight_pt=1.0)
    requests.extend(reqs)

    for i, d in enumerate(data):
        pair_x = cx + i * pair_w_total + pair_gap / 2

        for j, (val, color) in enumerate([
            (d["value_a"], ca), (d["value_b"], cb)
        ]):
            bar_h = (val / max_val) * ch if max_val > 0 else 0
            bx = pair_x + j * (bar_w + bar_inner_gap)
            by = cy + ch - bar_h

            _, reqs = rectangle(
                page_id, bx, by, bar_w, bar_h,
                fill=color, border_color=BORDER_DEFAULT, border_weight=0.5,
            )
            requests.extend(reqs)

        # X-axis label
        _, reqs = text_label(
            page_id, pair_x - 0.1, cy + ch + 0.05,
            pair_w_total, 0.3,
            d["label"], font_size=8,
        )
        requests.extend(reqs)

    return requests
