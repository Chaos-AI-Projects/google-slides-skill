"""
Tests for formula rendering module.

Tests the API contract and error handling. Rendering tests are skipped
if matplotlib is not installed (ChaosEternal/memory-solution#261).
"""

import os

from google_slides_skill.shapes import reset_ids, to_emu
from google_slides_skill.formulas import render_formula, formula_image_request, _check_matplotlib


def setup():
    reset_ids()


# ---------------------------------------------------------------------------
# formula_image_request: always testable (no matplotlib needed)
# ---------------------------------------------------------------------------

def test_formula_image_request_structure():
    """Request should have correct createImage structure."""
    setup()
    reqs = formula_image_request(
        "slide1", "https://example.com/formula.png",
        x=2.0, y=3.0, w=4.0, h=1.0,
    )
    assert len(reqs) == 1
    req = reqs[0]
    assert "createImage" in req
    ci = req["createImage"]
    assert ci["url"] == "https://example.com/formula.png"
    props = ci["elementProperties"]
    assert props["pageObjectId"] == "slide1"
    assert props["size"]["width"]["magnitude"] == to_emu(4.0)
    assert props["size"]["height"]["magnitude"] == to_emu(1.0)
    assert props["transform"]["translateX"] == to_emu(2.0)
    assert props["transform"]["translateY"] == to_emu(3.0)


def test_formula_image_request_custom_id():
    """Custom object_id should be used."""
    setup()
    reqs = formula_image_request(
        "slide1", "https://example.com/f.png",
        x=0, y=0, w=1, h=1, object_id="my_formula",
    )
    assert reqs[0]["createImage"]["objectId"] == "my_formula"


# ---------------------------------------------------------------------------
# render_formula: requires matplotlib
# ---------------------------------------------------------------------------

def test_render_formula_no_matplotlib():
    """Without matplotlib, render_formula should raise RuntimeError."""
    if _check_matplotlib():
        return  # skip: matplotlib is installed
    try:
        render_formula(r"$E = mc^2$")
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "matplotlib" in str(e).lower()


def test_render_formula_produces_png():
    """With matplotlib, render_formula should produce a PNG file."""
    if not _check_matplotlib():
        return  # skip: matplotlib not installed
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        out_path = f.name
    try:
        result = render_formula(r"$E = mc^2$", output_path=out_path)
        assert result == out_path
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_render_formula_temp_file():
    """Without explicit path, a temp file should be created."""
    if not _check_matplotlib():
        return  # skip: matplotlib not installed
    path = render_formula(r"$\int_0^1 x^2 dx$")
    try:
        assert os.path.exists(path)
        assert path.endswith(".png")
        assert os.path.getsize(path) > 0
    finally:
        if os.path.exists(path):
            os.unlink(path)
