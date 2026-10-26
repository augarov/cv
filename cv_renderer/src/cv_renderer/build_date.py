"""The build date: one value for the PDF, its time spans and the website."""

import re
from datetime import date, datetime, timezone

from rendercv.schema.models.rendercv_model import RenderCVModel


def date_from_source_date_epoch(value: str | None) -> date | None:
    """Return the UTC date of a SOURCE_DATE_EPOCH value, or None if unset.

    Follows https://reproducible-builds.org/specs/source-date-epoch/: an
    invalid value is an error, not silently ignored.
    """
    if not value:
        return None
    if not re.fullmatch(r"[0-9]+", value):
        raise ValueError(
            f"SOURCE_DATE_EPOCH must be a non-negative integer, got {value!r}"
        )
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).date()
    except (OverflowError, OSError, ValueError) as e:
        raise ValueError(f"SOURCE_DATE_EPOCH is out of range: {value!r}") from e


def build_date(model: RenderCVModel) -> date:
    """Return the date rendercv uses as "today" for this CV."""
    current_date = model.settings.current_date
    return current_date if isinstance(current_date, date) else date.today()
