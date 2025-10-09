"""Tests for template_utils module."""

from datetime import datetime
from unittest.mock import patch

import pytest

from cv_renderer.template_utils import format_current_time, normalize_url


class TestFormatCurrentTime:
    """
    Test cases for format_current_time function.

    datetime library is used to format the current time,
    so the basic test should be enough.
    """

    @patch("cv_renderer.template_utils._now")
    def test_datetime_formatting(self, mock_now):
        """Test date and time formatting."""
        # Mock a specific datetime
        mock_datetime = datetime(2023, 3, 10, 16, 45, 0)
        mock_now.return_value = mock_datetime

        assert format_current_time("%Y-%m-%d %H:%M:%S") == "2023-03-10 16:45:00"
        assert (
            format_current_time("%B %d, %Y at %I:%M %p") == "March 10, 2023 at 04:45 PM"
        )
        assert format_current_time("%a, %b %d, %Y") == "Fri, Mar 10, 2023"


class TestNormalizeUrl:
    """Test cases for normalize_url function."""

    def test_basic_url_normalization(self):
        """Test basic URL normalization with common URLs."""
        # Basic HTTP URL
        url = "http://example.com/path"
        expected = "http://example.com/path"
        assert normalize_url(url) == expected

        # Basic HTTPS URL
        url = "https://example.com/path"
        expected = "https://example.com/path"
        assert normalize_url(url) == expected

    def test_url_with_query_parameters(self):
        """Test that query parameters are removed."""
        url = "https://example.com/path?param1=value1&param2=value2"
        expected = "https://example.com/path"
        assert normalize_url(url) == expected

        # URL with only query parameters
        url = "https://example.com/?query=test"
        expected = "https://example.com"
        assert normalize_url(url) == expected

    def test_url_with_fragment(self):
        """Test that URL fragments are removed."""
        url = "https://example.com/path#section"
        expected = "https://example.com/path"
        assert normalize_url(url) == expected

        # URL with both query and fragment
        url = "https://example.com/path?param=value#section"
        expected = "https://example.com/path"
        assert normalize_url(url) == expected

    def test_url_with_port(self):
        """Test URLs with port numbers."""
        url = "https://example.com:8080/path"
        expected = "https://example.com:8080/path"
        assert normalize_url(url) == expected

        # HTTP with non-standard port
        url = "http://example.com:3000/api"
        expected = "http://example.com:3000/api"
        assert normalize_url(url) == expected

    def test_url_with_subdomain(self):
        """Test URLs with subdomains."""
        url = "https://api.example.com/v1/users"
        expected = "https://api.example.com/v1/users"
        assert normalize_url(url) == expected

        url = "https://www.example.com/page"
        expected = "https://www.example.com/page"
        assert normalize_url(url) == expected

    def test_url_without_path(self):
        """Test URLs without explicit path."""
        url = "https://example.com"
        expected = "https://example.com"
        assert normalize_url(url) == expected

        # With trailing slash
        url = "https://example.com/"
        expected = "https://example.com"
        assert normalize_url(url) == expected

    def test_complex_paths(self):
        """Test URLs with complex paths."""
        url = "https://example.com/api/v1/users/123/profile"
        expected = "https://example.com/api/v1/users/123/profile"
        assert normalize_url(url) == expected

        # Path with special characters
        url = "https://example.com/path/with-dashes_and_underscores"
        expected = "https://example.com/path/with-dashes_and_underscores"
        assert normalize_url(url) == expected

    def test_different_schemes(self):
        """Test URLs with different schemes."""
        # FTP URL
        url = "ftp://files.example.com/document.pdf"
        expected = "ftp://files.example.com/document.pdf"
        assert normalize_url(url) == expected

        # File URL
        url = "file:///home/user/document.txt"
        expected = "file:///home/user/document.txt"
        assert normalize_url(url) == expected

    def test_url_with_username_password(self):
        """Test URLs with authentication information."""
        # Note: urlparse handles userinfo in netloc
        url = "https://user:pass@example.com/path"
        expected = "https://user:pass@example.com/path"
        assert normalize_url(url) == expected

    def test_edge_cases(self):
        """Test edge cases and potential problem URLs."""
        # Empty path with query
        url = "https://example.com?query=value"
        expected = "https://example.com"
        assert normalize_url(url) == expected

        # Multiple slashes in path
        url = "https://example.com//double//slash//path"
        expected = "https://example.com/double/slash/path"
        assert normalize_url(url) == expected

        # URL with encoded characters
        url = "https://example.com/path%20with%20spaces"
        expected = "https://example.com/path%20with%20spaces"
        assert normalize_url(url) == expected

    def test_localhost_urls(self):
        """Test localhost and IP address URLs."""
        url = "http://localhost:3000/api"
        expected = "http://localhost:3000/api"
        assert normalize_url(url) == expected

        url = "http://127.0.0.1:8080/test"
        expected = "http://127.0.0.1:8080/test"
        assert normalize_url(url) == expected

    @pytest.mark.parametrize(
        "input_url,expected_output",
        [
            ("https://example.com/path", "https://example.com/path"),
            ("http://example.com/path?query=1", "http://example.com/path"),
            ("https://example.com/path#fragment", "https://example.com/path"),
            ("https://example.com/path?q=1#frag", "https://example.com/path"),
            ("https://sub.example.com:8080/api", "https://sub.example.com:8080/api"),
            ("ftp://files.example.com/file.txt", "ftp://files.example.com/file.txt"),
            ("https://example.com", "https://example.com"),
            ("https://example.com/", "https://example.com"),
        ],
    )
    def test_parametrized_normalization(self, input_url, expected_output):
        """Parametrized test for various URL normalization scenarios."""
        assert normalize_url(input_url) == expected_output
