"""
Text area capacity table -- strict enforcement model.

Provides exhaustive, pre-computed capacity limits for every (role, area,
font_size) combination used in slide layouts.  Text that exceeds the limit
is truncated with an ellipsis -- no dynamic font reduction, no exceptions.

Each entry in CAPACITY_TABLE maps:
    (role, area_name, font_size_pt) -> max_words

Two font sizes are defined per text box: a *normal* size (the role's
default) and a *reduced* size chosen for readability when content is dense.

Bullet entries use the same structure with an extra bullet_level dimension.

The capacity values are derived from the box dimensions, font metrics, and
empirical testing with the Google Slides API.  The formula used:
    chars_per_line = floor(box_width_in / (font_size_pt * 0.012))
    lines = floor(box_height_in / (font_size_pt * 0.02))
    max_chars = chars_per_line * lines
    max_words = floor(max_chars / 5.5)  (avg English word + space)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Box dimensions: every text area used by any layout, in inches (w, h)
# ---------------------------------------------------------------------------

TEXT_AREAS = {
    # Layout body areas
    "full_body": (8.0, 3.4),
    "half_body": (3.8, 3.4),
    "full_wide": (8.0, 4.5),
    "narrow_tall": (4.5, 4.0),
    "code_block": (7.6, 3.4),      # code_block layout (with padding)
    "quote_area": (7.0, 2.5),
    # Title/subtitle areas
    "title_bar": (8.0, 1.0),       # standard title bar (fits 2 lines at 28pt)
    "title_wide": (8.0, 1.2),      # title_slide title
    "subtitle_title": (6.0, 0.8),  # title_slide subtitle
    "subtitle_header": (3.8, 0.6), # comparison column header
    "section_heading": (8.0, 1.5), # section_divider heading
    # Diagram label areas
    "container_title": (2.0, 0.35),
    "child_label": (1.3, 0.6),
    "connector_label": (0.8, 0.3),
}


def _compute_capacity(w: float, h: float, font_size_pt: float,
                      indent_in: float = 0.0,
                      font_family: str = "Arial") -> int:
    """Compute max words that fit in a box at a given font size.

    Calibrated against Google Slides rendering:
      - Proportional fonts (Arial): char width ~ font_size * 0.0083 inches
      - Monospace fonts (Roboto Mono): char width ~ font_size * 0.0100 inches
      - Line height ~ font_size * 0.017 inches
      - Average word length ~ 5.5 chars (including trailing space)

    Returns a conservative estimate (slightly under actual capacity).
    """
    effective_w = w - indent_in
    if effective_w <= 0 or h <= 0:
        return 0
    char_width = font_size_pt * (0.0100 if "mono" in font_family.lower() else 0.0083)
    line_height = font_size_pt * 0.017
    chars_per_line = int(effective_w / char_width)
    lines = int(h / line_height)
    max_chars = chars_per_line * lines
    return max(1, int(max_chars / 5.5))


def _text_fits(text: str, w: float, h: float, font_size_pt: float,
               indent_in: float = 0.0,
               font_family: str = "Arial") -> bool:
    """Check if text actually fits in a box by simulating word-wrap.

    Unlike _compute_capacity (which uses average word length), this checks
    the actual character count of each word against the line width.  This
    catches long technical words (e.g. "Orchestration") that the average-
    based model misses.
    """
    effective_w = w - indent_in
    if effective_w <= 0 or h <= 0:
        return False
    char_width = font_size_pt * (0.0100 if "mono" in font_family.lower() else 0.0083)
    line_height = font_size_pt * 0.017
    chars_per_line = max(1, int(effective_w / char_width))
    max_lines = max(1, int(h / line_height))

    lines_needed = 1
    current_line_len = 0
    for word in text.split():
        wlen = len(word)
        if current_line_len == 0:
            current_line_len = wlen
        elif current_line_len + 1 + wlen <= chars_per_line:
            current_line_len += 1 + wlen
        else:
            lines_needed += 1
            current_line_len = wlen
    return lines_needed <= max_lines


# ---------------------------------------------------------------------------
# Pre-computed capacity table: (role, area, font_size_pt) -> max_words
#
# Two sizes per combination: normal (role default) and reduced.
# Font size defaults: slide_title=36, subtitle=24, body=18, caption=14, code=14
# ---------------------------------------------------------------------------

# Role default font sizes (must match fonts.py)
_ROLE_SIZES = {
    "slide_title": 36,
    "subtitle": 24,
    "body": 18,
    "caption": 14,
    "code": 14,
}

# Reduced font sizes per role (one step down, still readable)
_REDUCED_SIZES = {
    "slide_title": 28,
    "subtitle": 20,
    "body": 14,
    "caption": 11,
    "code": 11,
}


def _build_capacity_table() -> dict[tuple, int]:
    """Build the exhaustive capacity table from areas and font sizes."""
    # (role, area) combinations that appear in layouts
    combos = [
        # title_body, title_bullets, two_column, text_image, image_text,
        # full_image, code_block, comparison, table_text, text_table layouts
        ("slide_title", "title_bar"),
        ("slide_title", "title_wide"),
        ("slide_title", "section_heading"),
        ("subtitle", "subtitle_title"),
        ("subtitle", "subtitle_header"),
        ("subtitle", "quote_area"),
        ("body", "full_body"),
        ("body", "full_wide"),
        ("body", "half_body"),
        ("body", "narrow_tall"),
        ("caption", "full_body"),
        ("caption", "quote_area"),
        ("code", "code_block"),
        # Diagram elements
        ("body", "container_title"),
        ("body", "child_label"),
        ("caption", "connector_label"),
    ]

    # Font family per role (for char width calculation)
    role_fonts = {
        "code": "Roboto Mono",
    }

    table = {}
    for role, area in combos:
        w, h = TEXT_AREAS[area]
        normal = _ROLE_SIZES[role]
        reduced = _REDUCED_SIZES[role]
        font = role_fonts.get(role, "Arial")
        table[(role, area, normal)] = _compute_capacity(w, h, normal, font_family=font)
        if reduced != normal:
            table[(role, area, reduced)] = _compute_capacity(w, h, reduced, font_family=font)
    return table


CAPACITY_TABLE = _build_capacity_table()


def _build_bullet_capacity_table() -> dict[tuple, int]:
    """Build bullet capacity table with indent adjustments."""
    bullet_combos = [
        ("body", "full_body"),
        ("body", "full_wide"),
        ("body", "half_body"),
        ("body", "narrow_tall"),
        ("caption", "full_body"),
    ]
    indent_per_level = {0: 0.3, 1: 0.6}  # inches

    table = {}
    for role, area in bullet_combos:
        w, h = TEXT_AREAS[area]
        for level in (0, 1):
            normal = _ROLE_SIZES[role]
            reduced = _REDUCED_SIZES[role]
            indent = indent_per_level[level]
            table[(role, area, level, normal)] = _compute_capacity(
                w, h, normal, indent_in=indent)
            if reduced != normal:
                table[(role, area, level, reduced)] = _compute_capacity(
                    w, h, reduced, indent_in=indent)
    return table


BULLET_CAPACITY_TABLE = _build_bullet_capacity_table()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_capacity(role: str, area: str, font_size_pt: float | None = None) -> int:
    """Get max word count for plain text in a given area at a specific font size.

    If font_size_pt is None, uses the role's default size.
    Returns the max words, or -1 if the combination is not in the table.
    """
    if font_size_pt is None:
        font_size_pt = _ROLE_SIZES.get(role, 18)
    return CAPACITY_TABLE.get((role, area, font_size_pt), -1)


def get_bullet_capacity(role: str, area: str, level: int,
                        font_size_pt: float | None = None) -> int:
    """Get max word count for bulleted text at a nesting level and font size.

    Returns the max words, or -1 if the combination is not in the table.
    """
    if font_size_pt is None:
        font_size_pt = _ROLE_SIZES.get(role, 18)
    return BULLET_CAPACITY_TABLE.get((role, area, level, font_size_pt), -1)


def fit_text(text: str, role: str, area: str,
             font_size_pt: float | None = None) -> tuple[str, float]:
    """Fit text into the given area, truncating if necessary.

    Returns (fitted_text, font_size_pt).

    Strategy:
    1. Try at the specified (or default) font size.
    2. If text exceeds capacity, try the reduced font size.
    3. If still too long, truncate with ellipsis at the reduced size.

    Never returns a font size below the reduced size for the role.

    Uses character-aware word-wrap simulation so long technical words
    (e.g. "Orchestration") are handled correctly.
    """
    if font_size_pt is None:
        font_size_pt = _ROLE_SIZES.get(role, 18)

    dims = TEXT_AREAS.get(area)
    if dims is None:
        return text, font_size_pt

    w, h = dims
    role_fonts = {"code": "Roboto Mono"}
    font = role_fonts.get(role, "Arial")

    # Try at requested size (character-aware check)
    if _text_fits(text, w, h, font_size_pt, font_family=font):
        return text, font_size_pt

    # Try at reduced size
    reduced = _REDUCED_SIZES.get(role, font_size_pt)
    if reduced != font_size_pt:
        if _text_fits(text, w, h, reduced, font_family=font):
            return text, reduced
        # Truncate at reduced size
        return _truncate_to_fit(text, w, h, reduced, font_family=font), reduced

    # Truncate at the requested size
    return _truncate_to_fit(text, w, h, font_size_pt, font_family=font), font_size_pt


def _truncate(text: str, max_words: int) -> str:
    """Truncate text to max_words, adding ellipsis."""
    words = text.split()
    if len(words) <= max_words:
        return text
    # Keep max_words - 1 words + ellipsis to stay within limit
    return " ".join(words[:max_words - 1]) + "..."


def _truncate_to_fit(text: str, w: float, h: float, font_size_pt: float,
                     font_family: str = "Arial") -> str:
    """Truncate text word-by-word until it fits in the box."""
    words = text.split()
    for n in range(len(words) - 1, 0, -1):
        candidate = " ".join(words[:n]) + "..."
        if _text_fits(candidate, w, h, font_size_pt, font_family=font_family):
            return candidate
    # Even one word doesn't fit -- return it anyway (best effort)
    return words[0] + "..." if words else text


def fit_font_size(text: str, role: str, area: str) -> float:
    """Return the font size (pt) needed to fit text in the given area.

    Compatibility wrapper around fit_text(). Returns only the font size.
    Unlike the old implementation, this uses a two-tier lookup (normal/reduced)
    rather than continuous scaling with an 8pt floor.
    """
    _, size = fit_text(text, role, area)
    return size


# Legacy compatibility
def estimate_capacity_at_size(role: str, area: str, font_size_pt: float) -> int:
    """Estimate capacity at an arbitrary font size.

    Checks the pre-computed table first; falls back to computation.
    """
    cap = get_capacity(role, area, font_size_pt)
    if cap >= 0:
        return cap
    # Compute on the fly for non-standard sizes
    dims = TEXT_AREAS.get(area)
    if dims is None:
        return -1
    return _compute_capacity(dims[0], dims[1], font_size_pt)


# ---------------------------------------------------------------------------
# Diagram capacity constraints
# ---------------------------------------------------------------------------

DIAGRAM_AREA = (8.0, 4.3)

DIAGRAM_CAPACITY = {
    "flowchart": {
        "max_nodes": 12,
        "max_edges": 20,
        "min_node_w": 1.2,
        "min_node_h": 0.6,
    },
    "sequence": {
        "max_participants": 5,
        "max_messages": 10,
    },
    "bar_chart": {
        "max_bars": 8,
    },
    "comparison_chart": {
        "max_groups": 6,
    },
}


def get_diagram_capacity(diagram_type: str) -> dict:
    """Get capacity constraints for a diagram type."""
    return DIAGRAM_CAPACITY.get(diagram_type, {})


# ---------------------------------------------------------------------------
# Table capacity constraints
# ---------------------------------------------------------------------------

TABLE_AREAS = {
    "table_full": (8.0, 3.5),
    "table_half": (3.8, 3.5),
}

TABLE_CAPACITY = {
    "table_full": {
        "max_rows": 10,
        "max_cols": 6,
        "min_row_h": 0.30,
        "min_col_w": 1.0,
        "cell_max_words": 8,
        "header_max_words": 4,
    },
    "table_half": {
        "max_rows": 10,
        "max_cols": 3,
        "min_row_h": 0.30,
        "min_col_w": 1.0,
        "cell_max_words": 5,
        "header_max_words": 3,
    },
}


def get_table_capacity(area: str) -> dict:
    """Get capacity constraints for a table area."""
    return TABLE_CAPACITY.get(area, {})
