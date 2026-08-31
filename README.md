# google-slides-skill

Programmatic Google Slides presentation builder using the native Slides API.

Generates `batchUpdate` request objects for the [Google Slides API](https://developers.google.com/slides/api/reference/rest) -- create slides, place text, build tables, render diagrams, and connect components with smart connectors.

## Modules

| Module | Purpose |
|--------|---------|
| `fonts` | Font specification system (slide_title, subtitle, body, caption, code) |
| `layouts` | 16 reusable slide layouts with precise positioning (16:9, 10.0 x 5.625 inches) |
| `capacity` | Text capacity estimation, font size fitting, overflow handling |
| `tables` | Native Slides API tables with header styling, alternating row colors, 4 layout variants |
| `shapes` | Primitive shape builders (rectangle, rounded_rectangle, ellipse, diamond, etc.) |
| `connectors` | Straight and smart elbow connectors with obstacle-aware routing |
| `containers` | Large container boxes with title bars, dashed borders, auto-grid layout for nested components |
| `formulas` | LaTeX formula rendering to PNG via matplotlib (optional dependency) |
| `diagrams.flowchart` | Flowchart generator with topological sort auto-layout |
| `diagrams.chart` | Bar, line, and pie chart generators |
| `diagrams.architecture` | Architecture diagram generator with 2-layer container groups |
| `diagrams.sequence` | Sequence diagram generator with participant boxes and lifelines |

## Quick Start

```python
from google_slides_skill import FONT_SPEC, to_slides_text_style, get_layout
from google_slides_skill.shapes import rectangle, text_label
from google_slides_skill.containers import Container, render_containers
from google_slides_skill.diagrams.flowchart import render_flowchart

# Get a layout definition
layout = get_layout("title_body")

# Build container-based architecture diagram
containers = [
    Container(id="frontend", title="Frontend", children=[
        {"id": "spa", "label": "SPA", "type": "rectangle"},
        {"id": "cdn", "label": "CDN", "type": "service"},
    ]),
    Container(id="backend", title="Backend", children=[
        {"id": "api", "label": "API Server", "type": "service"},
        {"id": "db", "label": "PostgreSQL", "type": "database"},
    ]),
]
connectors = [
    {"from_container": "frontend", "from_child": "spa",
     "to_container": "backend", "to_child": "api", "label": "HTTPS"},
]

# Generate Slides API requests
requests = render_containers("slide_page_id", containers, connectors_spec=connectors)
```

## Layouts

16 built-in layouts for standard 16:9 slides (10.0 x 5.625 inches):

- `title_slide` -- centered title and subtitle
- `section_divider` -- section break with large title
- `title_body` -- title with full-width body text
- `title_bullets` -- title with bulleted list
- `two_column` -- two equal text columns
- `text_image` / `image_text` -- text with image placeholder
- `full_image` -- full-slide image
- `code_block` -- monospaced code display
- `comparison` -- side-by-side comparison with headers
- `quote` -- centered quotation
- `diagram` -- open area for diagrams and shapes
- `table_full` -- full-width table
- `table_text` / `text_table` -- table with text column
- `two_table` -- two side-by-side tables

All positions are in inches internally; use `to_emu()` to convert to EMU for the API.

## Dependencies

- Python 3.12+
- `gws` CLI for Google Workspace API access (runtime, for actually creating presentations)
- `matplotlib` (optional, for LaTeX formula rendering)

## Tests

```bash
cd google-slides-skill
pip install -e ".[dev]"
pytest
```

These are pure unit tests. They make no Google API calls and need no network access or credentials.

Shape IDs come from a global counter, `_next_id()` in `shapes.py`. Call `reset_ids()` between test runs so IDs stay deterministic.

## Unit Coordinates

All positioning uses **EMU** (English Metric Units) internally:
- 1 inch = 914,400 EMU
- The public API accepts inches; use `to_emu()` when building raw API requests
