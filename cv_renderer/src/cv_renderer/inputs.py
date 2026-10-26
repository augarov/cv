"""Load and validate the CV inputs: rendercv's YAML files and website.yaml."""

from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

import pydantic
import yaml
from rendercv.exception import (
    RenderCVUserError,
    RenderCVUserValidationError,
    RenderCVValidationError,
)
from rendercv.schema.models.cv.cv import Cv
from rendercv.schema.models.rendercv_model import RenderCVModel
from rendercv.schema.rendercv_model_builder import (
    build_rendercv_dictionary,
    build_rendercv_model_from_commented_map,
)

from .logger import make_logger
from .models import Website

logger = make_logger(__name__)


class InputError(Exception):
    """An input file is missing or invalid; the message names the file."""


def load_cv(
    cv: Path,
    design: Path | None = None,
    locale: Path | None = None,
    settings: Path | None = None,
    source_date: date | None = None,
) -> RenderCVModel:
    """Load and validate the rendercv inputs.

    Optional files that aren't given are left to rendercv's defaults. A file
    replaces the whole section of the same name in ``cv.yaml``.

    ``source_date`` (from SOURCE_DATE_EPOCH) replaces a ``current_date`` that
    is unset or ``today``; an explicit date in the settings wins.
    """
    cv_text = _read(cv)
    sections = (("design", design), ("locale", locale), ("settings", settings))
    overlays = {key: (path, _read(path)) for key, path in sections if path is not None}
    inline_sections = _top_level(cv_text)
    for key, (path, text) in overlays.items():
        if key not in _top_level(text):
            raise InputError(f"{path}: must contain a top-level `{key}:` section")
        if key in inline_sections:
            logger.warning(
                "%s: the inline `%s:` section is ignored, %s replaces it",
                cv,
                key,
                path,
            )
    # rendercv's builder crashes on a settings section that isn't a mapping
    settings_path, settings_text = overlays.get("settings", (cv, cv_text))
    settings_section = _top_level(settings_text).get("settings", {})
    if not isinstance(settings_section, Mapping):
        raise InputError(f"{settings_path}: `settings:` must be a mapping")

    sources = {"main_yaml_file": cv} | {
        f"{key}_yaml_file": path for key, (path, _) in overlays.items()
    }
    try:
        dictionary, overlay_sources = build_rendercv_dictionary(
            cv_text,
            **{f"{key}_yaml_file": text for key, (_, text) in overlays.items()},
        )
        # build_rendercv_dictionary always creates the settings section
        settings_section = dictionary["settings"]
        if (
            source_date is not None
            and settings_section.get("current_date", "today") == "today"
        ):
            # A date, not an ISO string: rendercv's validation context only
            # understands a date or "today"
            settings_section["current_date"] = source_date
        return build_rendercv_model_from_commented_map(
            dictionary, input_file_path=cv, overlay_sources=overlay_sources
        )
    except RenderCVUserValidationError as e:
        raise InputError(
            "\n".join(_format_error(error, sources) for error in e.validation_errors)
        ) from e
    except RenderCVUserError as e:
        raise InputError(f"{cv}: {e.message}") from e


def load_website(website: Path, cv: Cv) -> Website:
    """Load website.yaml and fill in the defaults derived from the CV."""
    try:
        data = yaml.safe_load(_read(website))
        return Website.model_validate(data, context={"cv": cv})
    except yaml.YAMLError as e:
        raise InputError(f"{website}: not a valid YAML file: {e}") from e
    except pydantic.ValidationError as e:
        errors = e.errors()
        if any(error["loc"] == ("url",) for error in errors):
            # pdf_url defaults to one derived from url: don't repeat url's error
            errors = [
                error
                for error in errors
                if not (error["loc"] == ("pdf_url",) and error["type"] == "missing")
            ]
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc']) or 'file'}: {error['msg']}"
            for error in errors
        )
        raise InputError(f"{website}: {details}") from e


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        raise InputError(f"{path}: {e.strerror}") from e


def _top_level(text: str) -> dict[str, Any]:
    # Invalid YAML is left to rendercv, which reports it with its position
    try:
        data: Any = yaml.safe_load(text)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _format_error(error: RenderCVValidationError, sources: dict[str, Path]) -> str:
    location = str(sources[error.yaml_source])
    if error.yaml_location is not None:
        (line, column), _ = error.yaml_location
        location = f"{location}:{line}:{column}"
    field = ".".join(error.schema_location or ())
    prefix = f"{location}: {field}: " if field else f"{location}: "
    return f"{prefix}{error.message}"
