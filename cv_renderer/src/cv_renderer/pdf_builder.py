"""PdfBuilder: compiles a Typst source file to PDF using rendercv's fonts."""

from pathlib import Path

import rendercv_fonts
import typst
from rendercv.renderer.pdf_png import get_package_path

from .inputs import InputError
from .logger import make_logger

logger = make_logger(__name__)


class PdfBuilder:
    """Compiles a pre-rendered .typ file to PDF; no CV model required."""

    def __init__(self, typst_path: Path, output_path: Path) -> None:
        """Store the source .typ path and the destination PDF path."""
        self._typst_path = typst_path
        self._output_path = output_path

    def build(self) -> None:
        """Compile the Typst source and write the PDF."""
        if not self._typst_path.is_file():
            raise InputError(f"{self._typst_path}: file not found")
        logger.debug("Compiling %s → %s", self._typst_path, self._output_path)
        compiler = typst.Compiler(
            root=self._typst_path.parent,
            font_paths=list(rendercv_fonts.paths_to_font_folders),
            package_path=get_package_path(),
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        compiler.compile(
            input=self._typst_path,
            format="pdf",
            output=self._output_path,
        )
        logger.info("PDF written: %s", self._output_path)
