"""Render the Typst source of the PDF with rendercv's own templates."""

from pathlib import Path

from rendercv.renderer.templater.templater import render_full_template
from rendercv.schema.models.rendercv_model import RenderCVModel

from .logger import make_logger

logger = make_logger(__name__)


def render_typst(model: RenderCVModel, output: Path) -> None:
    """Write the Typst document for model (theme from ``design.theme``)."""
    content: str = render_full_template(model, "typst")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    logger.info("Written: %s", output)
