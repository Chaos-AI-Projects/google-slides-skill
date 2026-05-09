# Google Slides Skill

## Overview

Python toolkit for programmatically generating Google Slides presentations via the native Slides API. Generates `batchUpdate` request lists -- does not call the API directly.

## Architecture

- **`fonts.py`** -- Font specifications (families, weights, sizes) for 5 text roles
- **`layouts.py`** -- 16 slide layout definitions with element positions in inches; EMU conversion via `to_emu()`
- **`capacity.py`** -- Text capacity estimation per (role, area) pair; `fit_font_size()` for overflow handling
- **`tables.py`** -- Table request builders with header styling, alternating rows, 4 layout variants
- **`shapes.py`** -- Primitive shape builders (rectangle, ellipse, diamond, etc.); shared `_next_id()` counter
- **`connectors.py`** -- Straight and smart elbow connectors with obstacle-aware routing
- **`containers.py`** -- Container boxes with title bars, auto-grid child layout, z-ordering
- **`formulas.py`** -- LaTeX-to-PNG via matplotlib (optional dependency)
- **`diagrams/`** -- High-level diagram generators (flowchart, chart, architecture, sequence)

## Key Conventions

- All positions are in **inches** at the API surface; internal conversion to EMU (1 inch = 914,400 EMU)
- Slide canvas: **10.0 x 5.625 inches** (standard 16:9)
- Shape IDs use a global counter (`_next_id()` in shapes.py); call `reset_ids()` between test runs
- Diagram modules import from parent package using relative imports (`from ..shapes import ...`)

## Running Tests

```bash
cd google-slides-skill
pip install -e ".[dev]"
pytest
```

Tests are pure unit tests -- no Google API calls, no network, no credentials needed.
