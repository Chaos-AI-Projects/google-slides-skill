---
description: Create a Google Slides presentation programmatically using the google-slides-skill library
---

Create a Google Slides presentation. The user will describe the content they want -- a topic summary, a paper overview, a project status deck, etc.

## Workflow

### Step 1 -- Gather content

Collect the information needed for the presentation:
- If the user provides a URL or file, fetch/read it
- If the user describes the content, use that directly
- Identify the key sections, data points, and visual elements

### Step 2 -- Plan the slides

Produce an outline with slide types. Choose from the available layouts:

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

### Step 3 -- Write the build script

Write a Python script that uses `google_slides_skill` to generate the presentation. The script should:

1. Create a new presentation via `gws slides presentations create --title "..." --json`
2. Parse the presentation ID from the response
3. Build slides using the library modules:
   - `from google_slides_skill import get_layout, to_emu, FONT_SPEC, to_slides_text_style`
   - `from google_slides_skill.shapes import rectangle, rounded_rectangle, text_label, arrow`
   - `from google_slides_skill.tables import create_table`
   - `from google_slides_skill.connectors import straight_connector, elbow_connector`
   - `from google_slides_skill.containers import Container, render_containers`
   - `from google_slides_skill.diagrams.flowchart import render_flowchart`
   - `from google_slides_skill.diagrams.chart import render_bar_chart, render_comparison_chart`
   - `from google_slides_skill.diagrams.sequence import render_sequence`
   - `from google_slides_skill.diagrams.architecture import render_architecture`
4. For each slide:
   - Create a blank slide: `gws slides presentations.pages create --params '{"presentationId":"..."}' --json '{"slideLayoutReference":{"predefinedLayout":"BLANK"}}'`
   - Build requests using layout positions and shape helpers
   - Apply requests: `gws slides presentations batchUpdate --params '{"presentationId":"..."}' --json '{"requests":[...]}'`
5. For formulas (optional, requires matplotlib):
   - `from google_slides_skill.formulas import render_formula, upload_formula, formula_image_request`
   - Render LaTeX to PNG, upload to Drive, insert into slide
6. Share the presentation if requested

### Step 4 -- Run and verify

Execute the script and verify the presentation URL is returned.

### Step 5 -- Report

Return the Google Slides URL to the caller.

## Library Reference

### Layouts (`google_slides_skill.layouts`)

- `get_layout(name)` -- returns layout dict with element positions
- `list_layouts()` -- returns all available layout names
- `to_emu(inches)` -- convert inches to EMU (1 inch = 914,400 EMU)
- Canvas: 10.0 x 5.625 inches (16:9)

### Fonts (`google_slides_skill.fonts`)

- `FONT_SPEC` -- dict of text roles: `slide_title` (36pt), `subtitle` (24pt), `body` (18pt), `caption` (14pt), `code` (14pt mono)
- `to_slides_text_style(role)` -- returns Slides API `TextStyle` dict for a role

### Capacity (`google_slides_skill.capacity`)

- `fit_text(text, role, width_inches)` -- fit text to width, returns truncated text
- `fit_font_size(text, role, area)` -- compute font size to avoid overflow
- `get_capacity(role, area)` -- estimated character capacity for a text role in an area

### Shapes (`google_slides_skill.shapes`)

- `rectangle()`, `rounded_rectangle()`, `ellipse()`, `diamond()` -- shape builders
- `text_label()` -- text box with optional background
- `line()`, `arrow()` -- line primitives

### Tables (`google_slides_skill.tables`)

- `create_table(page_id, data, x, y, width, height, ...)` -- build a styled table
- Supports header styling, alternating row colors, 4 layout variants

### Connectors (`google_slides_skill.connectors`)

- `straight_connector()` -- point-to-point line
- `elbow_connector()` -- L-shaped connector
- `smart_elbow_connector()` -- obstacle-aware routed connector

### Containers (`google_slides_skill.containers`)

- `Container(id, title, children=[...])` -- grouped box with title bar
- `render_containers(page_id, containers, connectors_spec=[...])` -- render containers with connections

### Diagrams

- `diagrams.flowchart.render_flowchart(page_id, nodes, edges)` -- auto-layout flowchart
- `diagrams.chart.render_bar_chart(page_id, data, ...)` -- bar chart
- `diagrams.chart.render_comparison_chart(page_id, data, ...)` -- side-by-side comparison
- `diagrams.sequence.render_sequence(page_id, participants, messages)` -- sequence diagram
- `diagrams.architecture.render_architecture(page_id, groups, connections)` -- architecture diagram

### Formulas (`google_slides_skill.formulas`)

- `render_formula(latex_str)` -- render LaTeX to PNG (requires matplotlib)
- `upload_formula(png_path)` -- upload to Google Drive, returns public URL
- `formula_image_request(page_id, url, x, y, w, h)` -- insert formula image

## Canvas Constants

- Width: 10.0 inches / Height: 5.625 inches
- Standard margins: 0.5-1.0 inches
- Title area: y=0.3-0.5, h=0.6-0.8
- Body area: y=1.3-1.5, fills remaining space

## Style Guidelines

- Use dark backgrounds for title and closing slides
- Use white or light backgrounds for content slides
- Accent color: #3366CC
- Keep text concise -- max ~6 bullet points per slide
- Use diagrams to convey structure visually
