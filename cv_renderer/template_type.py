"""Template type detection module."""

from enum import Enum
from pathlib import Path
from typing import List, Optional


class TemplateType(Enum):
    """Template type."""

    HTML = "html"
    TEX = "latex"


def detect_template_type(template_path: Path) -> Optional[TemplateType]:
    """Detect template type from template path."""
    SUFFIX_TO_TYPE = [
        ([".html"], TemplateType.HTML),
        ([".tex", ".latex"], TemplateType.TEX),
    ]

    suffixes = [s.lower() for s in template_path.suffixes]
    for suffixes_to_match, template_type in SUFFIX_TO_TYPE:
        if _match_suffixes(suffixes, suffixes_to_match):
            return template_type

    return None


def _match_suffixes(filename_suffixes: List[str], suffixes_to_match: List[str]) -> bool:
    """Match suffixes."""
    return any(suffix in filename_suffixes for suffix in suffixes_to_match)
