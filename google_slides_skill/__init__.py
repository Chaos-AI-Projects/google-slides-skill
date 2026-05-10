"""Google Slides presentation builder -- programmatic slide generation via the Slides API."""

from .fonts import FONT_SPEC, to_slides_text_style
from .layouts import LAYOUTS, get_layout, list_layouts, to_emu
from .capacity import get_capacity, get_bullet_capacity, fit_text, fit_font_size
from .containers import Container, render_containers
from .formulas import render_formula, formula_image_request, upload_formula

__all__ = [
    "FONT_SPEC",
    "to_slides_text_style",
    "LAYOUTS",
    "get_layout",
    "list_layouts",
    "to_emu",
    "get_capacity",
    "get_bullet_capacity",
    "fit_text",
    "fit_font_size",
    "Container",
    "render_containers",
    "render_formula",
    "formula_image_request",
    "upload_formula",
]
