"""
Formula rendering for Google Slides -- LaTeX to PNG via matplotlib.

Renders LaTeX math expressions as PNG images using matplotlib's mathtext
engine, then provides helpers to insert the rendered image into a slide
via the Google Slides API.

Requires matplotlib (tracked in ChaosEternal/memory-solution#261).
"""

import os
import tempfile

# Lazy import -- matplotlib may not be installed yet.
_HAS_MATPLOTLIB = None


def _check_matplotlib():
    global _HAS_MATPLOTLIB
    if _HAS_MATPLOTLIB is None:
        try:
            import matplotlib
            _HAS_MATPLOTLIB = True
        except ImportError:
            _HAS_MATPLOTLIB = False
    return _HAS_MATPLOTLIB


def render_formula(latex: str, *, dpi: int = 200,
                   fontsize: int = 20,
                   color: str = "black",
                   output_path: str | None = None) -> str:
    """Render a LaTeX math expression to a PNG file.

    Args:
        latex: LaTeX math string (e.g. r"$E = mc^2$"). Wrap in $ signs.
        dpi: Output resolution.
        fontsize: Font size in points.
        color: Text color name or hex.
        output_path: Destination path. If None, a temp file is created.

    Returns:
        Path to the rendered PNG file.

    Raises:
        RuntimeError: If matplotlib is not installed.
    """
    if not _check_matplotlib():
        raise RuntimeError(
            "matplotlib is not installed. "
            "See ChaosEternal/memory-solution#261 for tracking."
        )

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(0.01, 0.01))
    ax.axis("off")
    fig.patch.set_alpha(0.0)

    # Render the formula as text
    text = ax.text(0, 0, latex, fontsize=fontsize, color=color,
                   ha="left", va="bottom",
                   transform=ax.transAxes)

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".png", prefix="formula_")
        os.close(fd)

    fig.savefig(output_path, dpi=dpi, bbox_inches="tight",
                pad_inches=0.05, transparent=True)
    plt.close(fig)

    return output_path


def formula_image_request(page_id: str, image_url: str,
                          x: float, y: float, w: float, h: float,
                          object_id: str | None = None) -> list[dict]:
    """Create Slides API requests to insert a formula image.

    The image_url must be a publicly accessible URL (e.g. served via
    a temporary HTTP endpoint or uploaded to Drive and shared).

    Args:
        page_id: Slide object ID.
        image_url: Public URL of the rendered formula PNG.
        x, y, w, h: Position and size in inches.
        object_id: Optional object ID for the image.

    Returns:
        List of batchUpdate request dicts.
    """
    from .layouts import to_emu
    from .shapes import _next_id

    oid = object_id or _next_id("formula")
    return [{
        "createImage": {
            "objectId": oid,
            "url": image_url,
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {
                    "width": {"magnitude": to_emu(w), "unit": "EMU"},
                    "height": {"magnitude": to_emu(h), "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1, "scaleY": 1,
                    "translateX": to_emu(x),
                    "translateY": to_emu(y),
                    "unit": "EMU",
                },
            },
        }
    }]
