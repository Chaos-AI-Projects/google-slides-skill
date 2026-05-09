"""
Slide layout definitions -- Phase 3 deliverable.

Defines 12 reusable slide layouts with element positions, text roles, and
styling. All positions are in inches; the Google Slides API expects EMU
(1 inch = 914400 EMU), so use the helper to_emu() when building requests.

Slide canvas: 10 x 5.625 inches (standard 16:9).

Each layout is a dict with:
  - name: human-readable layout name
  - description: what it's for
  - background: optional background color (RGB dict)
  - elements: list of element dicts, each with:
      - id: element identifier (used as suffix in object IDs)
      - kind: "text" | "image" | "shape"
      - role: text role from fonts.py (for text elements)
      - x, y, width, height: position in inches
      - optional: bullets (bool), bullet_level (int), background (RGB),
        alignment (str), placeholder (str for image/shape description)
"""

# Conversion helpers
INCH = 914400  # EMU per inch


def to_emu(inches: float) -> int:
    """Convert inches to EMU (English Metric Units)."""
    return int(inches * INCH)


# Slide dimensions
SLIDE_W = 10.0
SLIDE_H = 5.625

# Common positions
_MARGIN = 1.0  # left/right margin for content
_CONTENT_W = SLIDE_W - 2 * _MARGIN  # 8.0 inches

# Title bar: top of slide (1.0" allows 2 lines at 28pt reduced size)
_TITLE_X = _MARGIN
_TITLE_Y = 0.4
_TITLE_W = _CONTENT_W
_TITLE_H = 1.0

# Body area below title bar
_BODY_Y = 1.6
_BODY_H = 3.4

# Wide body (minimal title space)
_WIDE_Y = 0.8
_WIDE_H = 4.5

# Half column dimensions (for two-column layouts)
_COL_GAP = 0.4
_COL_W = (_CONTENT_W - _COL_GAP) / 2  # 3.8 inches each

# Text + Image split
_TEXT_IMG_TEXT_W = 4.5
_TEXT_IMG_IMG_W = _CONTENT_W - _TEXT_IMG_TEXT_W - _COL_GAP  # 3.1

# Colors
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
DARK_BG = {"red": 0.15, "green": 0.15, "blue": 0.20}
CODE_BG = {"red": 0.95, "green": 0.95, "blue": 0.95}
ACCENT = {"red": 0.20, "green": 0.40, "blue": 0.80}
LIGHT_ACCENT = {"red": 0.90, "green": 0.93, "blue": 0.98}

# ---------------------------------------------------------------------------
# Layout definitions
# ---------------------------------------------------------------------------

LAYOUT_TITLE_SLIDE = {
    "name": "title_slide",
    "description": "Centered title and subtitle for presentation openers",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _MARGIN,
            "y": 1.5,
            "width": _CONTENT_W,
            "height": 1.2,
            "alignment": "CENTER",
        },
        {
            "id": "subtitle",
            "kind": "text",
            "role": "subtitle",
            "x": _MARGIN + 1.0,
            "y": 2.9,
            "width": _CONTENT_W - 2.0,
            "height": 0.8,
            "alignment": "CENTER",
        },
    ],
}

LAYOUT_SECTION_DIVIDER = {
    "name": "section_divider",
    "description": "Large centered text for section breaks",
    "background": DARK_BG,
    "elements": [
        {
            "id": "heading",
            "kind": "text",
            "role": "slide_title",
            "x": _MARGIN,
            "y": 1.8,
            "width": _CONTENT_W,
            "height": 1.5,
            "alignment": "CENTER",
            "foreground": WHITE,
        },
    ],
}

LAYOUT_TITLE_BODY = {
    "name": "title_body",
    "description": "Title bar with full-width body text",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "body",
            "kind": "text",
            "role": "body",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _CONTENT_W,
            "height": _BODY_H,
            "area": "full_body",
        },
    ],
}

LAYOUT_TITLE_BULLETS = {
    "name": "title_bullets",
    "description": "Title bar with bulleted list",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "bullets",
            "kind": "text",
            "role": "body",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _CONTENT_W,
            "height": _BODY_H,
            "bullets": True,
            "area": "full_body",
        },
    ],
}

LAYOUT_TWO_COLUMN = {
    "name": "two_column",
    "description": "Title with two side-by-side text areas",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "left",
            "kind": "text",
            "role": "body",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _COL_W,
            "height": _BODY_H,
            "area": "half_body",
        },
        {
            "id": "right",
            "kind": "text",
            "role": "body",
            "x": _MARGIN + _COL_W + _COL_GAP,
            "y": _BODY_Y,
            "width": _COL_W,
            "height": _BODY_H,
            "area": "half_body",
        },
    ],
}

LAYOUT_TEXT_IMAGE = {
    "name": "text_image",
    "description": "Title with text on left, image placeholder on right",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "text",
            "kind": "text",
            "role": "body",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _TEXT_IMG_TEXT_W,
            "height": _BODY_H,
            "area": "narrow_tall",
        },
        {
            "id": "image",
            "kind": "image",
            "x": _MARGIN + _TEXT_IMG_TEXT_W + _COL_GAP,
            "y": _BODY_Y,
            "width": _TEXT_IMG_IMG_W,
            "height": _BODY_H,
            "placeholder": "image_right",
        },
    ],
}

LAYOUT_IMAGE_TEXT = {
    "name": "image_text",
    "description": "Title with image on left, text on right",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "image",
            "kind": "image",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _TEXT_IMG_IMG_W,
            "height": _BODY_H,
            "placeholder": "image_left",
        },
        {
            "id": "text",
            "kind": "text",
            "role": "body",
            "x": _MARGIN + _TEXT_IMG_IMG_W + _COL_GAP,
            "y": _BODY_Y,
            "width": _TEXT_IMG_TEXT_W,
            "height": _BODY_H,
            "area": "narrow_tall",
        },
    ],
}

LAYOUT_FULL_IMAGE = {
    "name": "full_image",
    "description": "Title with full-bleed image area",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": 0.2,
            "width": _TITLE_W,
            "height": 0.6,
        },
        {
            "id": "image",
            "kind": "image",
            "x": _MARGIN,
            "y": 1.0,
            "width": _CONTENT_W,
            "height": 4.3,
            "placeholder": "image_full",
        },
    ],
}

LAYOUT_CODE_BLOCK = {
    "name": "code_block",
    "description": "Title with monospace code area on gray background",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "code_bg",
            "kind": "shape",
            "shape_type": "RECTANGLE",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _CONTENT_W,
            "height": _BODY_H,
            "background": CODE_BG,
            "corner_radius": 0.1,
        },
        {
            "id": "code",
            "kind": "text",
            "role": "code",
            "x": _MARGIN + 0.2,
            "y": _BODY_Y + 0.15,
            "width": _CONTENT_W - 0.4,
            "height": _BODY_H - 0.3,
            "area": "code_block",
        },
    ],
}

LAYOUT_COMPARISON = {
    "name": "comparison",
    "description": "Title with two columns, each having a header and body",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "left_header",
            "kind": "text",
            "role": "subtitle",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _COL_W,
            "height": 0.6,
            "alignment": "CENTER",
            "background": LIGHT_ACCENT,
        },
        {
            "id": "left_body",
            "kind": "text",
            "role": "body",
            "x": _MARGIN,
            "y": _BODY_Y + 0.7,
            "width": _COL_W,
            "height": _BODY_H - 0.7,
            "area": "half_body",
        },
        {
            "id": "right_header",
            "kind": "text",
            "role": "subtitle",
            "x": _MARGIN + _COL_W + _COL_GAP,
            "y": _BODY_Y,
            "width": _COL_W,
            "height": 0.6,
            "alignment": "CENTER",
            "background": LIGHT_ACCENT,
        },
        {
            "id": "right_body",
            "kind": "text",
            "role": "body",
            "x": _MARGIN + _COL_W + _COL_GAP,
            "y": _BODY_Y + 0.7,
            "width": _COL_W,
            "height": _BODY_H - 0.7,
            "area": "half_body",
        },
    ],
}

LAYOUT_QUOTE = {
    "name": "quote",
    "description": "Large centered quote with attribution line",
    "background": None,
    "elements": [
        {
            "id": "quote",
            "kind": "text",
            "role": "subtitle",
            "x": 1.5,
            "y": 1.2,
            "width": 7.0,
            "height": 2.5,
            "alignment": "CENTER",
            "area": "quote_area",
        },
        {
            "id": "attribution",
            "kind": "text",
            "role": "caption",
            "x": 1.5,
            "y": 4.0,
            "width": 7.0,
            "height": 0.5,
            "alignment": "CENTER",
        },
    ],
}

LAYOUT_DIAGRAM = {
    "name": "diagram",
    "description": "Title with large area for embedded diagrams or shapes",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": 0.2,
            "width": _TITLE_W,
            "height": 0.6,
        },
        {
            "id": "diagram",
            "kind": "shape",
            "shape_type": "RECTANGLE",
            "x": _MARGIN,
            "y": 1.0,
            "width": _CONTENT_W,
            "height": 4.3,
            "placeholder": "diagram_area",
        },
    ],
}

# ---------------------------------------------------------------------------
# Phase 3b: Table layouts
# ---------------------------------------------------------------------------

LAYOUT_TABLE_FULL = {
    "name": "table_full",
    "description": "Title with full-width table",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "table",
            "kind": "table",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _CONTENT_W,
            "height": _BODY_H,
            "area": "table_full",
        },
    ],
}

LAYOUT_TABLE_TEXT = {
    "name": "table_text",
    "description": "Title with table on left, text on right",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "table",
            "kind": "table",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _COL_W,
            "height": _BODY_H,
            "area": "table_half",
        },
        {
            "id": "text",
            "kind": "text",
            "role": "body",
            "x": _MARGIN + _COL_W + _COL_GAP,
            "y": _BODY_Y,
            "width": _COL_W,
            "height": _BODY_H,
            "area": "half_body",
        },
    ],
}

LAYOUT_TEXT_TABLE = {
    "name": "text_table",
    "description": "Title with text on left, table on right",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "text",
            "kind": "text",
            "role": "body",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _COL_W,
            "height": _BODY_H,
            "area": "half_body",
        },
        {
            "id": "table",
            "kind": "table",
            "x": _MARGIN + _COL_W + _COL_GAP,
            "y": _BODY_Y,
            "width": _COL_W,
            "height": _BODY_H,
            "area": "table_half",
        },
    ],
}

LAYOUT_TWO_TABLE = {
    "name": "two_table",
    "description": "Title with two side-by-side tables",
    "background": None,
    "elements": [
        {
            "id": "title",
            "kind": "text",
            "role": "slide_title",
            "x": _TITLE_X,
            "y": _TITLE_Y,
            "width": _TITLE_W,
            "height": _TITLE_H,
        },
        {
            "id": "table_left",
            "kind": "table",
            "x": _MARGIN,
            "y": _BODY_Y,
            "width": _COL_W,
            "height": _BODY_H,
            "area": "table_half",
        },
        {
            "id": "table_right",
            "kind": "table",
            "x": _MARGIN + _COL_W + _COL_GAP,
            "y": _BODY_Y,
            "width": _COL_W,
            "height": _BODY_H,
            "area": "table_half",
        },
    ],
}

# ---------------------------------------------------------------------------
# Registry: all layouts indexed by name
# ---------------------------------------------------------------------------

LAYOUTS = {
    layout["name"]: layout
    for layout in [
        LAYOUT_TITLE_SLIDE,
        LAYOUT_SECTION_DIVIDER,
        LAYOUT_TITLE_BODY,
        LAYOUT_TITLE_BULLETS,
        LAYOUT_TWO_COLUMN,
        LAYOUT_TEXT_IMAGE,
        LAYOUT_IMAGE_TEXT,
        LAYOUT_FULL_IMAGE,
        LAYOUT_CODE_BLOCK,
        LAYOUT_COMPARISON,
        LAYOUT_QUOTE,
        LAYOUT_DIAGRAM,
        LAYOUT_TABLE_FULL,
        LAYOUT_TABLE_TEXT,
        LAYOUT_TEXT_TABLE,
        LAYOUT_TWO_TABLE,
    ]
}


def get_layout(name: str) -> dict:
    """Look up a layout by name. Raises KeyError if not found."""
    return LAYOUTS[name]


def list_layouts() -> list[str]:
    """Return all available layout names."""
    return list(LAYOUTS.keys())
