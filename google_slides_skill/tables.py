"""
Table rendering for Google Slides -- Phase 3b deliverable.

Creates native Slides API tables with header row styling, cell text,
and configurable dimensions. Uses createTable + insertText + styling
requests compatible with presentations.batchUpdate.

Each helper returns a list of batchUpdate request dicts.
"""

from .layouts import to_emu, ACCENT, LIGHT_ACCENT, DARK_BG, WHITE

# ---------------------------------------------------------------------------
# Object ID generator (mirrors shapes.py pattern)
# ---------------------------------------------------------------------------

_table_counter = 0


def _next_table_id(prefix: str = "table") -> str:
    global _table_counter
    _table_counter += 1
    return f"{prefix}_{_table_counter}"


def reset_table_ids():
    global _table_counter
    _table_counter = 0


# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------

HEADER_BG = ACCENT
HEADER_TEXT_COLOR = WHITE
CELL_TEXT_COLOR = DARK_BG
ALT_ROW_BG = LIGHT_ACCENT
BORDER_COLOR = {"red": 0.75, "green": 0.75, "blue": 0.75}

DEFAULT_FONT_FAMILY = "Arial"
HEADER_FONT_SIZE_PT = 12
CELL_FONT_SIZE_PT = 11


# ---------------------------------------------------------------------------
# Table builder
# ---------------------------------------------------------------------------

def create_table(
    page_id: str,
    x: float,
    y: float,
    w: float,
    h: float,
    data: list[list[str]],
    *,
    header: bool = True,
    header_bg: dict = None,
    header_text_color: dict = None,
    alt_row_bg: dict = None,
    cell_text_color: dict = None,
    font_size: float = CELL_FONT_SIZE_PT,
    header_font_size: float = HEADER_FONT_SIZE_PT,
    object_id: str = None,
) -> tuple[str, list[dict]]:
    """Create a table on a slide.

    Args:
        page_id: slide object ID
        x, y, w, h: position and size in inches
        data: 2D list of cell strings, first row is header if header=True
        header: if True, style the first row as a header
        header_bg: header row background color (RGB dict)
        header_text_color: header text color (RGB dict)
        alt_row_bg: alternating row background (RGB dict), None to disable
        cell_text_color: body cell text color (RGB dict)
        font_size: body cell font size in points
        header_font_size: header row font size in points
        object_id: explicit object ID, or auto-generated

    Returns:
        (object_id, list_of_requests)
    """
    if not data or not data[0]:
        return object_id or _next_table_id(), []

    oid = object_id or _next_table_id()
    rows = len(data)
    cols = len(data[0])

    h_bg = header_bg or HEADER_BG
    h_tc = header_text_color or HEADER_TEXT_COLOR
    c_tc = cell_text_color or CELL_TEXT_COLOR
    a_bg = alt_row_bg if alt_row_bg is not None else ALT_ROW_BG

    reqs = []

    # 1. Create the table
    reqs.append({
        "createTable": {
            "objectId": oid,
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {
                    "width": {"magnitude": to_emu(w), "unit": "EMU"},
                    "height": {"magnitude": to_emu(h), "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1,
                    "scaleY": 1,
                    "translateX": to_emu(x),
                    "translateY": to_emu(y),
                    "unit": "EMU",
                },
            },
            "rows": rows,
            "columns": cols,
        }
    })

    # 2. Insert text into each cell
    for r, row in enumerate(data):
        for c, cell_text in enumerate(row):
            if cell_text:
                reqs.append({
                    "insertText": {
                        "objectId": oid,
                        "cellLocation": {
                            "rowIndex": r,
                            "columnIndex": c,
                        },
                        "text": str(cell_text),
                        "insertionIndex": 0,
                    }
                })

    # 3. Style header row
    if header and rows > 0:
        # Header background
        reqs.append({
            "updateTableCellProperties": {
                "objectId": oid,
                "tableRange": {
                    "location": {"rowIndex": 0, "columnIndex": 0},
                    "rowSpan": 1,
                    "columnSpan": cols,
                },
                "tableCellProperties": {
                    "tableCellBackgroundFill": {
                        "solidFill": {
                            "color": {"rgbColor": h_bg},
                        }
                    }
                },
                "fields": "tableCellBackgroundFill",
            }
        })
        # Header text style
        for c in range(cols):
            reqs.append({
                "updateTextStyle": {
                    "objectId": oid,
                    "cellLocation": {"rowIndex": 0, "columnIndex": c},
                    "textRange": {"type": "ALL"},
                    "style": {
                        "fontFamily": DEFAULT_FONT_FAMILY,
                        "fontSize": {"magnitude": header_font_size, "unit": "PT"},
                        "bold": True,
                        "foregroundColor": {
                            "opaqueColor": {"rgbColor": h_tc}
                        },
                    },
                    "fields": "fontFamily,fontSize,bold,foregroundColor",
                }
            })

    # 4. Style body rows
    start_row = 1 if header else 0
    for r in range(start_row, rows):
        # Alternating row backgrounds
        if a_bg and r % 2 == (1 if header else 0):
            reqs.append({
                "updateTableCellProperties": {
                    "objectId": oid,
                    "tableRange": {
                        "location": {"rowIndex": r, "columnIndex": 0},
                        "rowSpan": 1,
                        "columnSpan": cols,
                    },
                    "tableCellProperties": {
                        "tableCellBackgroundFill": {
                            "solidFill": {
                                "color": {"rgbColor": a_bg},
                            }
                        }
                    },
                    "fields": "tableCellBackgroundFill",
                }
            })

        # Body text style
        for c in range(cols):
            reqs.append({
                "updateTextStyle": {
                    "objectId": oid,
                    "cellLocation": {"rowIndex": r, "columnIndex": c},
                    "textRange": {"type": "ALL"},
                    "style": {
                        "fontFamily": DEFAULT_FONT_FAMILY,
                        "fontSize": {"magnitude": font_size, "unit": "PT"},
                        "bold": False,
                        "foregroundColor": {
                            "opaqueColor": {"rgbColor": c_tc}
                        },
                    },
                    "fields": "fontFamily,fontSize,bold,foregroundColor",
                }
            })

    return oid, reqs
