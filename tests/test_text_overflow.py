"""
Tests for text overflow enforcement -- programmatic font size reduction.

When text exceeds the capacity limit for a given (role, area), the font size
should be reduced proportionally to fit within the box.
"""

from google_slides_skill.fonts import FONT_SPEC
from google_slides_skill.capacity import (
    get_capacity, fit_font_size, estimate_capacity_at_size,
)


# ---------------------------------------------------------------------------
# fit_font_size: returns reduced font size when text exceeds capacity
# ---------------------------------------------------------------------------

def test_fit_under_capacity():
    """Text within capacity should keep the default font size."""
    text = "This is a short sentence."  # 5 words
    size = fit_font_size(text, "body", "full_body")
    default = FONT_SPEC["body"]["fontSize"]
    assert size == default, f"Expected {default}, got {size}"


def test_fit_over_capacity():
    """Text exceeding capacity should get a smaller font size."""
    text = " ".join(["word"] * 200)  # 200 words -- well over 102
    size = fit_font_size(text, "body", "full_body")
    default = FONT_SPEC["body"]["fontSize"]
    assert size < default, f"Expected less than {default}, got {size}"


def test_fit_minimum_font_size():
    """Font size should not go below a minimum threshold (8pt)."""
    text = " ".join(["word"] * 1000)  # extreme overflow
    size = fit_font_size(text, "body", "full_body")
    assert size >= 8, f"Expected >= 8, got {size}"


def test_fit_unknown_area():
    """Unknown role/area combo should return the default font size unchanged."""
    text = " ".join(["word"] * 200)
    size = fit_font_size(text, "body", "nonexistent_area")
    default = FONT_SPEC["body"]["fontSize"]
    assert size == default, f"Expected {default}, got {size}"


def test_fit_two_tier_reduction():
    """Over-capacity text should reduce to the reduced font size."""
    text_over = " ".join(["word"] * 120)  # exceeds normal capacity
    text_under = " ".join(["word"] * 20)  # under normal capacity

    size_over = fit_font_size(text_over, "body", "full_body")
    size_under = fit_font_size(text_under, "body", "full_body")

    default = FONT_SPEC["body"]["fontSize"]
    assert size_under == default, f"Expected {default}, got {size_under}"
    assert size_over < default, f"Expected less than {default}, got {size_over}"


def test_fit_code_role():
    """Code role should also get font size reduction."""
    text = " ".join(["token"] * 300)  # well over code/code_block capacity (144)
    size = fit_font_size(text, "code", "code_block")
    default = FONT_SPEC["code"]["fontSize"]
    assert size < default, f"Expected less than {default}, got {size}"


# ---------------------------------------------------------------------------
# estimate_capacity_at_size: capacity scales with font size
# ---------------------------------------------------------------------------

def test_estimate_capacity_smaller_font():
    """Smaller font should fit more words."""
    cap_18 = estimate_capacity_at_size("body", "full_body", 18)
    cap_14 = estimate_capacity_at_size("body", "full_body", 14)
    assert cap_14 > cap_18, f"Expected {cap_14} > {cap_18}"


def test_estimate_capacity_at_default():
    """At default font size, estimated capacity should match the table."""
    cap = estimate_capacity_at_size("body", "full_body", 18)
    table_cap = get_capacity("body", "full_body")
    assert cap == table_cap, f"Expected {table_cap}, got {cap}"
