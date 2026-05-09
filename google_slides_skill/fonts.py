"""
Font specification for the Google Slides creation skill.

Phase 1 deliverable: defines font families, weights, and sizes for each text role.
All sizes are in points (pt). The Google Slides API uses these in TextStyle objects.
"""

# Font families
FONT_TITLE = "Arial"
FONT_BODY = "Arial"
FONT_MONO = "Roboto Mono"

# Text role specifications: (font_family, bold, italic, size_pt)
FONT_SPEC = {
    "slide_title": {
        "fontFamily": FONT_TITLE,
        "bold": True,
        "italic": False,
        "fontSize": 36,
    },
    "subtitle": {
        "fontFamily": FONT_BODY,
        "bold": False,
        "italic": False,
        "fontSize": 24,
    },
    "body": {
        "fontFamily": FONT_BODY,
        "bold": False,
        "italic": False,
        "fontSize": 18,
    },
    "caption": {
        "fontFamily": FONT_BODY,
        "bold": False,
        "italic": True,
        "fontSize": 14,
    },
    "code": {
        "fontFamily": FONT_MONO,
        "bold": False,
        "italic": False,
        "fontSize": 14,
    },
}


def to_slides_text_style(role: str) -> dict:
    """Convert a font spec role to a Google Slides API TextStyle object."""
    spec = FONT_SPEC[role]
    return {
        "fontFamily": spec["fontFamily"],
        "bold": spec["bold"],
        "italic": spec["italic"],
        "fontSize": {"magnitude": spec["fontSize"], "unit": "PT"},
    }


# Summary table for documentation
FONT_TABLE = """
Font Specification Table
========================
Role          | Font Family  | Weight | Size (pt)
--------------+--------------+--------+----------
Slide Title   | Arial        | Bold   | 36
Subtitle      | Arial        | Normal | 24
Body Text     | Arial        | Normal | 18
Caption       | Arial        | Italic | 14
Code          | Roboto Mono  | Normal | 14
"""
