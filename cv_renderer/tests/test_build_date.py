"""Tests for build_date module."""

from datetime import date
from pathlib import Path

import pytest

from cv_renderer.build_date import build_date, date_from_source_date_epoch
from cv_renderer.inputs import load_cv

FIXTURES = Path(__file__).parent / "fixtures"


class TestDateFromSourceDateEpoch:
    """Test cases for date_from_source_date_epoch function."""

    @pytest.mark.parametrize("value", [None, ""])
    def test_unset(self, value):
        """Test that an unset or empty value means no source date."""
        assert date_from_source_date_epoch(value) is None

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("0", date(1970, 1, 1)),
            ("1714521600", date(2024, 5, 1)),
            # 2024-05-01 23:30 UTC is already May 2 east of UTC: UTC decides
            ("1714606200", date(2024, 5, 1)),
        ],
    )
    def test_valid(self, value, expected):
        """Test that a non-negative integer gives its date in UTC."""
        assert date_from_source_date_epoch(value) == expected

    @pytest.mark.parametrize(
        "value", ["-1", "abc", "1.5", " 1", "1e9", "+1", "²", "9" * 30]
    )
    def test_invalid(self, value):
        """Test that anything else is an error naming the variable."""
        with pytest.raises(ValueError, match="SOURCE_DATE_EPOCH"):
            date_from_source_date_epoch(value)


class TestBuildDate:
    """Test cases for build_date function."""

    def test_explicit_date(self):
        """Test that an explicit current_date is the build date."""
        model = load_cv(
            FIXTURES / "cv_minimal.yaml", settings=FIXTURES / "settings.yaml"
        )

        assert build_date(model) == date(2024, 5, 1)

    def test_today(self):
        """Test that current_date "today" gives today's date."""
        model = load_cv(FIXTURES / "cv_minimal.yaml")

        assert build_date(model) == date.today()
