"""
Shape primitives for Google Slides -- Phase 4, Step 1.

Helper functions that emit batchUpdate request objects for basic shapes:
rectangles, rounded rectangles, ellipses, lines/arrows, and text labels.

Each helper takes position (x, y, width, height) in inches and returns a
list of batchUpdate request dicts ready for presentations.batchUpdate.
"""

from .layouts import to_emu, ACCENT, DARK_BG, WHITE

# ---------------------------------------------------------------------------
# Object ID generator
# ---------------------------------------------------------------------------

_id_counter = 0


def _next_id(prefix: str = "shape") -> str:
    """Generate a unique object ID with the given prefix."""
    global _id_counter
    _id_counter += 1
    return f"{prefix}_{_id_counter}"


def reset_ids():
    """Reset the ID counter (call before building a new presentation)."""
    global _id_counter
    _id_counter = 0


# ---------------------------------------------------------------------------
# Color / style constants
# ---------------------------------------------------------------------------

# Shape palette -- consistent with layouts.py
FILL_BLUE = ACCENT                                           # primary accent
FILL_DARK = DARK_BG                                          # dark background
FILL_WHITE = WHITE                                           # white
FILL_LIGHT_GRAY = {"red": 0.93, "green": 0.93, "blue": 0.93}
FILL_LIGHT_BLUE = {"red": 0.85, "green": 0.91, "blue": 0.98}
FILL_GREEN = {"red": 0.20, "green": 0.66, "blue": 0.33}
FILL_ORANGE = {"red": 0.95, "green": 0.60, "blue": 0.15}
FILL_RED = {"red": 0.85, "green": 0.20, "blue": 0.20}

BORDER_DEFAULT = {"red": 0.30, "green": 0.30, "blue": 0.35}
BORDER_BLUE = ACCENT

# Default styling
DEFAULT_BORDER_WEIGHT_PT = 1.5
DEFAULT_FONT_FAMILY = "Arial"
DEFAULT_FONT_SIZE_PT = 12
DEFAULT_TEXT_COLOR = DARK_BG

# Arrow head types understood by the Slides API
ARROW_NONE = "NONE"
ARROW_OPEN = "OPEN_ARROW"
ARROW_FILLED = "FILL_ARROW"
ARROW_DIAMOND = "FILL_DIAMOND"

# Dash styles
DASH_SOLID = "SOLID"
DASH_DOT = "DOT"
DASH_DASH = "DASH"
DASH_DASH_DOT = "DASH_DOT"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _size(w_inches: float, h_inches: float) -> dict:
    return {
        "width": {"magnitude": to_emu(w_inches), "unit": "EMU"},
        "height": {"magnitude": to_emu(h_inches), "unit": "EMU"},
    }


def _transform(x_inches: float, y_inches: float) -> dict:
    return {
        "scaleX": 1,
        "scaleY": 1,
        "translateX": to_emu(x_inches),
        "translateY": to_emu(y_inches),
        "unit": "EMU",
    }


def _solid_fill(color: dict, alpha: float = 1.0) -> dict:
    return {"solidFill": {"color": {"rgbColor": color}, "alpha": alpha}}


def _outline(color: dict = None, weight_pt: float = DEFAULT_BORDER_WEIGHT_PT,
             dash: str = DASH_SOLID) -> dict:
    c = color or BORDER_DEFAULT
    return {
        "outlineFill": _solid_fill(c),
        "weight": {"magnitude": weight_pt, "unit": "PT"},
        "dashStyle": dash,
    }


def _text_style(font_family: str = DEFAULT_FONT_FAMILY,
                font_size_pt: float = DEFAULT_FONT_SIZE_PT,
                bold: bool = False, italic: bool = False,
                color: dict = None) -> dict:
    style = {
        "fontFamily": font_family,
        "fontSize": {"magnitude": font_size_pt, "unit": "PT"},
        "bold": bold,
        "italic": italic,
    }
    if color:
        style["foregroundColor"] = {"opaqueColor": {"rgbColor": color}}
    return style


# ---------------------------------------------------------------------------
# Shape primitives
# ---------------------------------------------------------------------------

def rectangle(page_id: str, x: float, y: float, w: float, h: float, *,
              text: str = None, fill: dict = None, border_color: dict = None,
              border_weight: float = DEFAULT_BORDER_WEIGHT_PT,
              border_dash: str = DASH_SOLID,
              text_color: dict = None, font_size: float = DEFAULT_FONT_SIZE_PT,
              bold: bool = False, alignment: str = "CENTER",
              object_id: str = None) -> tuple[str, list[dict]]:
    """Create a rectangle shape, optionally with text inside.

    Returns (object_id, list_of_requests).
    """
    oid = object_id or _next_id("rect")
    reqs = []

    reqs.append({
        "createShape": {
            "objectId": oid,
            "shapeType": "RECTANGLE",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": _size(w, h),
                "transform": _transform(x, y),
            },
        }
    })

    # Shape properties: fill + outline
    props = {}
    fields = []
    if fill:
        props["shapeBackgroundFill"] = _solid_fill(fill)
        fields.append("shapeBackgroundFill")
    if border_color or border_dash != DASH_SOLID:
        props["outline"] = _outline(border_color, border_weight, border_dash)
        fields.append("outline")

    if fields:
        reqs.append({
            "updateShapeProperties": {
                "objectId": oid,
                "shapeProperties": props,
                "fields": ",".join(fields),
            }
        })

    # Optional text
    if text is not None:
        reqs.extend(_insert_shape_text(
            oid, text, text_color=text_color, font_size=font_size,
            bold=bold, alignment=alignment,
        ))

    return oid, reqs


def rounded_rectangle(page_id: str, x: float, y: float, w: float, h: float,
                      **kwargs) -> tuple[str, list[dict]]:
    """Create a rounded rectangle. Same arguments as rectangle()."""
    oid = kwargs.pop("object_id", None) or _next_id("rrect")
    kwargs["object_id"] = oid
    _, reqs = rectangle(page_id, x, y, w, h, **kwargs)
    # Patch the shape type in the createShape request
    reqs[0]["createShape"]["shapeType"] = "ROUND_RECTANGLE"
    return oid, reqs


def ellipse(page_id: str, x: float, y: float, w: float, h: float, *,
            text: str = None, fill: dict = None, border_color: dict = None,
            border_weight: float = DEFAULT_BORDER_WEIGHT_PT,
            text_color: dict = None, font_size: float = DEFAULT_FONT_SIZE_PT,
            bold: bool = False, alignment: str = "CENTER",
            object_id: str = None) -> tuple[str, list[dict]]:
    """Create an ellipse (or circle if w == h)."""
    oid = object_id or _next_id("ellipse")
    reqs = []

    reqs.append({
        "createShape": {
            "objectId": oid,
            "shapeType": "ELLIPSE",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": _size(w, h),
                "transform": _transform(x, y),
            },
        }
    })

    props = {}
    fields = []
    if fill:
        props["shapeBackgroundFill"] = _solid_fill(fill)
        fields.append("shapeBackgroundFill")
    if border_color:
        props["outline"] = _outline(border_color, border_weight)
        fields.append("outline")

    if fields:
        reqs.append({
            "updateShapeProperties": {
                "objectId": oid,
                "shapeProperties": props,
                "fields": ",".join(fields),
            }
        })

    if text is not None:
        reqs.extend(_insert_shape_text(
            oid, text, text_color=text_color, font_size=font_size,
            bold=bold, alignment=alignment,
        ))

    return oid, reqs


def diamond(page_id: str, x: float, y: float, w: float, h: float, *,
            text: str = None, fill: dict = None, border_color: dict = None,
            border_weight: float = DEFAULT_BORDER_WEIGHT_PT,
            text_color: dict = None, font_size: float = 10,
            bold: bool = False, alignment: str = "CENTER",
            object_id: str = None) -> tuple[str, list[dict]]:
    """Create a diamond shape (for flowchart decisions)."""
    oid = object_id or _next_id("diamond")
    reqs = []

    reqs.append({
        "createShape": {
            "objectId": oid,
            "shapeType": "DIAMOND",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": _size(w, h),
                "transform": _transform(x, y),
            },
        }
    })

    props = {}
    fields = []
    if fill:
        props["shapeBackgroundFill"] = _solid_fill(fill)
        fields.append("shapeBackgroundFill")
    if border_color:
        props["outline"] = _outline(border_color, border_weight)
        fields.append("outline")

    if fields:
        reqs.append({
            "updateShapeProperties": {
                "objectId": oid,
                "shapeProperties": props,
                "fields": ",".join(fields),
            }
        })

    if text is not None:
        reqs.extend(_insert_shape_text(
            oid, text, text_color=text_color, font_size=font_size,
            bold=bold, alignment=alignment,
        ))

    return oid, reqs


def parallelogram(page_id: str, x: float, y: float, w: float, h: float, *,
                  text: str = None, fill: dict = None, border_color: dict = None,
                  border_weight: float = DEFAULT_BORDER_WEIGHT_PT,
                  text_color: dict = None, font_size: float = DEFAULT_FONT_SIZE_PT,
                  bold: bool = False, alignment: str = "CENTER",
                  object_id: str = None) -> tuple[str, list[dict]]:
    """Create a parallelogram (for flowchart I/O nodes)."""
    oid = object_id or _next_id("para")
    reqs = []

    reqs.append({
        "createShape": {
            "objectId": oid,
            "shapeType": "PARALLELOGRAM",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": _size(w, h),
                "transform": _transform(x, y),
            },
        }
    })

    props = {}
    fields = []
    if fill:
        props["shapeBackgroundFill"] = _solid_fill(fill)
        fields.append("shapeBackgroundFill")
    if border_color:
        props["outline"] = _outline(border_color, border_weight)
        fields.append("outline")

    if fields:
        reqs.append({
            "updateShapeProperties": {
                "objectId": oid,
                "shapeProperties": props,
                "fields": ",".join(fields),
            }
        })

    if text is not None:
        reqs.extend(_insert_shape_text(
            oid, text, text_color=text_color, font_size=font_size,
            bold=bold, alignment=alignment,
        ))

    return oid, reqs


def line(page_id: str, x1: float, y1: float, x2: float, y2: float, *,
         color: dict = None, weight_pt: float = DEFAULT_BORDER_WEIGHT_PT,
         dash: str = DASH_SOLID,
         start_arrow: str = ARROW_NONE, end_arrow: str = ARROW_NONE,
         object_id: str = None) -> tuple[str, list[dict]]:
    """Create a straight line between two points.

    Coordinates are in inches. Returns (object_id, list_of_requests).
    """
    oid = object_id or _next_id("line")
    c = color or BORDER_DEFAULT

    # Lines are created as connectors with absolute start/end positions.
    # The Slides API uses a createLine request.
    reqs = []

    reqs.append({
        "createLine": {
            "objectId": oid,
            "lineCategory": "STRAIGHT",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": _size(abs(x2 - x1), abs(y2 - y1)),
                "transform": {
                    "scaleX": 1 if x2 >= x1 else -1,
                    "scaleY": 1 if y2 >= y1 else -1,
                    "translateX": to_emu(x1),
                    "translateY": to_emu(y1),
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

    return oid, reqs


def arrow(page_id: str, x1: float, y1: float, x2: float, y2: float, *,
          color: dict = None, weight_pt: float = DEFAULT_BORDER_WEIGHT_PT,
          dash: str = DASH_SOLID, head: str = ARROW_FILLED,
          object_id: str = None) -> tuple[str, list[dict]]:
    """Create a line with an arrowhead at the end point."""
    return line(page_id, x1, y1, x2, y2,
                color=color, weight_pt=weight_pt, dash=dash,
                end_arrow=head, object_id=object_id)


def text_label(page_id: str, x: float, y: float, w: float, h: float,
               text: str, *, font_size: float = DEFAULT_FONT_SIZE_PT,
               bold: bool = False, italic: bool = False,
               color: dict = None, alignment: str = "CENTER",
               object_id: str = None) -> tuple[str, list[dict]]:
    """Create a standalone text label (TEXT_BOX with no background)."""
    oid = object_id or _next_id("label")
    reqs = []

    reqs.append({
        "createShape": {
            "objectId": oid,
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": _size(w, h),
                "transform": _transform(x, y),
            },
        }
    })

    reqs.extend(_insert_shape_text(
        oid, text, text_color=color, font_size=font_size,
        bold=bold, italic=italic, alignment=alignment,
    ))

    return oid, reqs


# ---------------------------------------------------------------------------
# Text insertion helper (shared by shape primitives)
# ---------------------------------------------------------------------------

def _insert_shape_text(object_id: str, text: str, *,
                       text_color: dict = None,
                       font_size: float = DEFAULT_FONT_SIZE_PT,
                       bold: bool = False, italic: bool = False,
                       alignment: str = "CENTER") -> list[dict]:
    """Insert text into an existing shape and style it."""
    tc = text_color or DEFAULT_TEXT_COLOR
    reqs = [
        {
            "insertText": {
                "objectId": object_id,
                "text": text,
                "insertionIndex": 0,
            }
        },
        {
            "updateTextStyle": {
                "objectId": object_id,
                "textRange": {"type": "ALL"},
                "style": _text_style(color=tc, font_size_pt=font_size,
                                     bold=bold, italic=italic),
                "fields": "fontFamily,fontSize,bold,italic,foregroundColor",
            }
        },
        {
            "updateParagraphStyle": {
                "objectId": object_id,
                "textRange": {"type": "ALL"},
                "style": {"alignment": alignment},
                "fields": "alignment",
            }
        },
    ]
    return reqs
