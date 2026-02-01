"""Tests for utils.py - shared utility functions.

Comprehensive test suite covering all utility functions with edge cases,
error conditions, and success scenarios.
"""

import os
import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    is_valid_email,
    is_personal_email,
    is_safe_domain,
    extract_domain,
    set_env_flag,
    safe_truncate,
    parse_memory_line,
    retry_with_backoff,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def mock_logger():
    """Mock logger for testing log output."""
    with patch("utils.logger") as logger_mock:
        yield logger_mock


# =============================================================================
# TEST: is_valid_email
# =============================================================================


class TestIsValidEmail:
    """Tests for is_valid_email function."""

    def test_valid_simple_email(self):
        """Test simple valid email address."""
        assert is_valid_email("test@example.com") is True

    def test_valid_email_with_dot(self):
        """Test valid email with dot in local part."""
        assert is_valid_email("user.name@domain.org") is True

    def test_valid_email_with_plus(self):
        """Test valid email with plus sign (Gmail style)."""
        assert is_valid_email("user+tag@company.co.uk") is True

    def test_valid_email_with_numbers(self):
        """Test valid email with numbers."""
        assert is_valid_email("user123@example.com") is True

    def test_valid_email_with_hyphen(self):
        """Test valid email with hyphen in domain."""
        assert is_valid_email("user@sub-domain.com") is True

    def test_valid_email_uppercase(self):
        """Test uppercase email (should be valid per RFC)."""
        assert is_valid_email("USER@EXAMPLE.COM") is True

    def test_invalid_empty_string(self):
        """Test empty string."""
        assert is_valid_email("") is False

    def test_invalid_no_at_symbol(self):
        """Test email without @ symbol."""
        assert is_valid_email("notanemail") is False

    def test_invalid_at_symbol_only(self):
        """Test string with only @ symbol."""
        assert is_valid_email("@") is False

    def test_invalid_no_local_part(self):
        """Test email with no local part."""
        assert is_valid_email("@nodomain.com") is False

    def test_invalid_no_domain(self):
        """Test email with no domain."""
        assert is_valid_email("noat.com") is False

    def test_invalid_no_tld(self):
        """Test email with no top-level domain."""
        assert is_valid_email("user@com") is False

    def test_invalid_multiple_at_symbols(self):
        """Test email with multiple @ symbols."""
        assert is_valid_email("user@@example.com") is False

    def test_invalid_space_in_email(self):
        """Test email with space."""
        assert is_valid_email("user name@example.com") is False

    def test_invalid_special_characters(self):
        """Test email with invalid special characters."""
        assert is_valid_email("user#@example.com") is False

    def test_none_input(self):
        """Test None input - function returns False for None."""
        # The function checks for falsy values, so None returns False
        assert is_valid_email(None) is False


# =============================================================================
# TEST: is_personal_email
# =============================================================================


class TestIsPersonalEmail:
    """Tests for is_personal_email function."""

    def test_personal_gmail(self):
        """Test Gmail domain."""
        assert is_personal_email("user@gmail.com") is True

    def test_personal_yahoo(self):
        """Test Yahoo domain."""
        assert is_personal_email("user@yahoo.com") is True

    def test_personal_hotmail(self):
        """Test Hotmail domain."""
        assert is_personal_email("user@hotmail.com") is True

    def test_personal_outlook(self):
        """Test Outlook domain."""
        assert is_personal_email("user@outlook.com") is True

    def test_personal_icloud(self):
        """Test iCloud domain."""
        assert is_personal_email("user@icloud.com") is True

    def test_personal_aol(self):
        """Test AOL domain."""
        assert is_personal_email("user@aol.com") is True

    def test_personal_protonmail(self):
        """Test ProtonMail domain."""
        assert is_personal_email("user@protonmail.com") is True

    def test_personal_proton_me(self):
        """Test Proton.me domain."""
        assert is_personal_email("user@proton.me") is True

    def test_personal_fastmail(self):
        """Test FastMail domain."""
        assert is_personal_email("user@fastmail.com") is True

    def test_corporate_domain(self):
        """Test corporate domain."""
        assert is_personal_email("user@acme.com") is False

    def test_corporate_org(self):
        """Test corporate .org domain."""
        assert is_personal_email("user@company.org") is False

    def test_personal_case_insensitive(self):
        """Test case insensitivity."""
        assert is_personal_email("user@GMAIL.COM") is True
        assert is_personal_email("user@Gmail.Com") is True

    def test_invalid_no_at_symbol(self):
        """Test string without @ symbol."""
        assert is_personal_email("notanemail") is False

    def test_invalid_empty_string(self):
        """Test empty string."""
        assert is_personal_email("") is False


# =============================================================================
# TEST: is_safe_domain
# =============================================================================


class TestIsSafeDomain:
    """Tests for is_safe_domain function (SSRF protection)."""

    def test_safe_google_domain(self):
        """Test safe public domain."""
        assert is_safe_domain("google.com") is True

    def test_safe_acme_domain(self):
        """Test another safe domain."""
        assert is_safe_domain("acme.com") is True

    def test_safe_org_domain(self):
        """Test safe .org domain."""
        assert is_safe_domain("example.org") is True

    def test_blocked_localhost(self):
        """Test localhost is blocked."""
        assert is_safe_domain("localhost") is False

    def test_blocked_127_0_0_1(self):
        """Test 127.0.0.1 is blocked."""
        assert is_safe_domain("127.0.0.1") is False

    def test_blocked_10_network(self):
        """Test 10.x.x.x private network is blocked."""
        assert is_safe_domain("10.0.0.1") is False
        assert is_safe_domain("10.255.255.255") is False

    def test_blocked_192_168_network(self):
        """Test 192.168.x.x private network is blocked."""
        assert is_safe_domain("192.168.1.1") is False
        assert is_safe_domain("192.168.255.255") is False

    def test_blocked_172_network(self):
        """Test 172.16-31.x.x private network is blocked."""
        assert is_safe_domain("172.16.0.1") is False
        assert is_safe_domain("172.31.255.255") is False

    def test_blocked_169_254_network(self):
        """Test 169.254.x.x link-local is blocked."""
        assert is_safe_domain("169.254.1.1") is False

    def test_blocked_0_network(self):
        """Test 0.x.x.x network is blocked."""
        assert is_safe_domain("0.0.0.1") is False

    def test_blocked_ipv6_localhost(self):
        """Test IPv6 localhost is blocked."""
        assert is_safe_domain("::1") is False

    def test_blocked_ipv6_private(self):
        """Test IPv6 private addresses are blocked."""
        assert is_safe_domain("fd00::1") is False
        assert is_safe_domain("fe80::1") is False

    def test_blocked_internal_suffix(self):
        """Test .internal suffix is blocked."""
        assert is_safe_domain("server.internal") is False
        assert is_safe_domain("api.internal") is False

    def test_blocked_local_suffix(self):
        """Test .local suffix is blocked."""
        assert is_safe_domain("server.local") is False
        assert is_safe_domain("api.local") is False

    def test_blocked_localdomain_suffix(self):
        """Test .localdomain suffix is blocked."""
        assert is_safe_domain("server.localdomain") is False

    def test_blocked_corp_suffix(self):
        """Test .corp suffix is blocked."""
        assert is_safe_domain("server.corp") is False

    def test_blocked_lan_suffix(self):
        """Test .lan suffix is blocked."""
        assert is_safe_domain("server.lan") is False

    def test_case_insensitive(self):
        """Test domain checking is case insensitive."""
        assert is_safe_domain("GOOGLE.COM") is True
        assert is_safe_domain("Server.LOCAL") is False

    def test_whitespace_handling(self):
        """Test that whitespace is stripped."""
        assert is_safe_domain("  google.com  ") is True
        assert is_safe_domain("  localhost  ") is False

    def test_logging_on_blocked(self, mock_logger):
        """Test that blocked domains are logged."""
        is_safe_domain("localhost")
        mock_logger.warning.assert_called()


# =============================================================================
# TEST: extract_domain
# =============================================================================


class TestExtractDomain:
    """Tests for extract_domain function."""

    def test_extract_simple_domain(self):
        """Test extracting domain from simple email."""
        assert extract_domain("user@example.com") == "example.com"

    def test_extract_domain_with_subdomain(self):
        """Test extracting domain with subdomain."""
        assert extract_domain("user@mail.example.com") == "mail.example.com"

    def test_extract_domain_org(self):
        """Test extracting .org domain."""
        assert extract_domain("user@organization.org") == "organization.org"

    def test_extract_domain_lowercase(self):
        """Test that domain is converted to lowercase."""
        assert extract_domain("USER@DOMAIN.ORG") == "domain.org"
        assert extract_domain("user@Domain.Com") == "domain.com"

    def test_extract_domain_mixed_case(self):
        """Test mixed case email."""
        assert extract_domain("JohnDoe@CompanyEmail.Com") == "companyemail.com"

    def test_extract_domain_with_numbers(self):
        """Test domain with numbers."""
        assert extract_domain("user@domain123.com") == "domain123.com"

    def test_invalid_no_at_symbol(self):
        """Test email without @ symbol."""
        assert extract_domain("notanemail") is None

    def test_invalid_empty_string(self):
        """Test empty string."""
        assert extract_domain("") is None

    def test_invalid_at_symbol_only(self):
        """Test string with only @ symbol."""
        assert extract_domain("@") == ""

    def test_invalid_no_domain(self):
        """Test email with @ but no domain."""
        result = extract_domain("user@")
        assert result == ""

    def test_multiple_at_symbols(self):
        """Test email with multiple @ symbols returns second part."""
        result = extract_domain("user@domain@example.com")
        assert result == "domain"


# =============================================================================
# TEST: safe_truncate
# =============================================================================


class TestSafeTruncate:
    """Tests for safe_truncate function."""

    def test_no_truncation_needed(self):
        """Test string shorter than max_length."""
        assert safe_truncate("short", 100) == "short"

    def test_no_truncation_exact_length(self):
        """Test string exactly at max_length."""
        assert safe_truncate("hello", 5) == "hello"

    def test_truncation_with_default_suffix(self):
        """Test truncation with default '...' suffix."""
        result = safe_truncate("hello world", 8)
        assert result == "hello..."
        assert len(result) == 8

    def test_truncation_with_custom_suffix(self):
        """Test truncation with custom suffix."""
        result = safe_truncate("hello world", 8, suffix=">>")
        assert result == "hello >>"
        assert len(result) == 8

    def test_truncation_with_empty_suffix(self):
        """Test truncation with empty suffix."""
        result = safe_truncate("hello world", 5, suffix="")
        assert result == "hello"

    def test_truncation_with_long_suffix(self):
        """Test truncation when suffix is as long as max_length."""
        result = safe_truncate("hello world", 3, suffix="...")
        # Should truncate to 0 chars + suffix
        assert result == "..."
        assert len(result) == 3

    def test_truncation_single_char(self):
        """Test truncation to single character."""
        result = safe_truncate("hello", 4, suffix=".")
        assert len(result) == 4
        assert result.endswith(".")

    def test_very_short_max_length(self):
        """Test with very short max_length."""
        result = safe_truncate("hello world", 2, suffix="")
        assert result == "he"
        assert len(result) == 2

    def test_empty_string(self):
        """Test empty string."""
        assert safe_truncate("", 10) == ""

    def test_unicode_text(self):
        """Test unicode text truncation."""
        result = safe_truncate("hello🌍world", 8)
        assert len(result) <= 8

    def test_multiline_text(self):
        """Test multiline text truncation."""
        text = "line1\nline2\nline3"
        result = safe_truncate(text, 10)
        assert len(result) == 10


# =============================================================================
# TEST: parse_memory_line
# =============================================================================


class TestParseMemoryLine:
    """Tests for parse_memory_line function."""

    def test_valid_line_basic(self):
        """Test parsing basic valid memory line."""
        result = parse_memory_line("contact:test@email.com | 2026-01-01 | notes here")
        assert result is not None
        assert result[0] == "contact:test@email.com"
        assert result[1] == "2026-01-01"
        assert result[2] == "notes here"

    def test_valid_line_with_pipes_in_notes(self):
        """Test parsing with pipes in notes section."""
        result = parse_memory_line(
            "contact:user@example.com | 2026-06-15 | notes | with | multiple | pipes"
        )
        assert result is not None
        assert result[0] == "contact:user@example.com"
        assert result[1] == "2026-06-15"
        assert result[2] == "notes | with | multiple | pipes"

    def test_valid_line_uppercase_contact(self):
        """Test parsing with uppercase CONTACT."""
        result = parse_memory_line("CONTACT:test@email.com | 2026-01-01 | notes")
        assert result is not None

    def test_valid_line_mixed_case_contact(self):
        """Test parsing with mixed case Contact."""
        result = parse_memory_line("Contact:test@email.com | 2026-01-01 | notes")
        assert result is not None

    def test_valid_line_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        result = parse_memory_line(
            "  contact:test@email.com  |  2026-01-01  |  notes with spaces  "
        )
        assert result is not None
        assert result[0] == "contact:test@email.com"
        assert result[1] == "2026-01-01"
        assert result[2] == "notes with spaces"

    def test_valid_line_minimal(self):
        """Test minimal valid line (key + date only)."""
        result = parse_memory_line("contact:test@email.com | 2026-01-01")
        assert result is not None
        assert result[0] == "contact:test@email.com"
        assert result[1] == "2026-01-01"
        assert result[2] is None

    def test_valid_line_empty_notes(self):
        """Test with empty notes section."""
        result = parse_memory_line("contact:test@email.com | 2026-01-01 | ")
        assert result is not None
        assert result[2] == ""

    def test_invalid_no_contact_keyword(self):
        """Test line without 'contact:' keyword."""
        assert parse_memory_line("invalid line without contact") is None

    def test_invalid_empty_string(self):
        """Test empty string."""
        assert parse_memory_line("") is None

    def test_invalid_none_input(self):
        """Test None input."""
        assert parse_memory_line(None) is None

    def test_invalid_insufficient_pipes(self):
        """Test line with only contact, no date."""
        # Only one pipe needed minimum
        result = parse_memory_line("contact:test@email.com")
        assert result is None

    def test_contact_with_special_characters(self):
        """Test contact key with special characters."""
        result = parse_memory_line("contact:user+tag@sub.domain.com | 2026-01-01 | notes")
        assert result is not None
        assert result[0] == "contact:user+tag@sub.domain.com"

    def test_various_date_formats(self):
        """Test with various date formats."""
        # The function doesn't validate date format, just parses
        result = parse_memory_line("contact:test@email.com | Jan 1, 2026 | notes")
        assert result is not None
        assert result[1] == "Jan 1, 2026"

    def test_long_notes_with_special_chars(self):
        """Test notes with special characters."""
        special_notes = "notes: [important] (urgent) {action} <priority>"
        result = parse_memory_line(f"contact:test@email.com | 2026-01-01 | {special_notes}")
        assert result is not None
        assert result[2] == special_notes


# =============================================================================
# TEST: retry_with_backoff
# =============================================================================


class TestRetryWithBackoff:
    """Tests for retry_with_backoff function."""

    def test_success_first_attempt(self):
        """Test successful execution on first attempt."""
        mock_func = MagicMock(return_value="success")
        result = retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)
        assert result == "success"
        assert mock_func.call_count == 1

    def test_success_second_attempt(self):
        """Test successful execution after one failure."""
        mock_func = MagicMock(side_effect=[Exception("fail"), "success"])
        result = retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)
        assert result == "success"
        assert mock_func.call_count == 2

    def test_success_third_attempt(self):
        """Test successful execution after two failures."""
        mock_func = MagicMock(side_effect=[Exception("fail1"), Exception("fail2"), "success"])
        result = retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)
        assert result == "success"
        assert mock_func.call_count == 3

    def test_all_retries_fail(self):
        """Test when all retry attempts fail."""
        mock_func = MagicMock(side_effect=Exception("always fail"))
        with pytest.raises(Exception, match="always fail"):
            retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)
        assert mock_func.call_count == 3

    def test_args_passed_to_function(self):
        """Test that positional arguments are passed to function."""
        mock_func = MagicMock(return_value="success")
        result = retry_with_backoff(mock_func, "arg1", "arg2", max_attempts=1, base_delay=0.01)
        mock_func.assert_called_once_with("arg1", "arg2")

    def test_kwargs_passed_to_function(self):
        """Test that keyword arguments are passed to function."""
        mock_func = MagicMock(return_value="success")
        result = retry_with_backoff(
            mock_func, key1="value1", key2="value2", max_attempts=1, base_delay=0.01
        )
        mock_func.assert_called_once_with(key1="value1", key2="value2")

    def test_args_and_kwargs(self):
        """Test with both positional and keyword arguments."""
        mock_func = MagicMock(return_value="success")
        result = retry_with_backoff(
            mock_func,
            "arg1",
            "arg2",
            key1="value1",
            max_attempts=1,
            base_delay=0.01,
        )
        mock_func.assert_called_once_with("arg1", "arg2", key1="value1")

    def test_exponential_backoff_timing(self):
        """Test that backoff timing increases exponentially."""
        # This test uses a low base delay to keep test fast
        mock_func = MagicMock(side_effect=[Exception("fail1"), Exception("fail2"), "success"])
        with patch("utils.time.sleep") as mock_sleep:
            result = retry_with_backoff(mock_func, max_attempts=3, base_delay=1.0)
            assert result == "success"
            # Check that sleep was called with increasing delays
            # 1.0 * (2**0) = 1.0, then 1.0 * (2**1) = 2.0
            assert mock_sleep.call_count == 2
            calls = mock_sleep.call_args_list
            assert calls[0][0][0] == 1.0
            assert calls[1][0][0] == 2.0

    def test_single_attempt(self):
        """Test with max_attempts=1."""
        mock_func = MagicMock(side_effect=Exception("fail"))
        with pytest.raises(Exception, match="fail"):
            retry_with_backoff(mock_func, max_attempts=1, base_delay=0.01)
        assert mock_func.call_count == 1

    def test_many_attempts(self):
        """Test with many retry attempts."""
        # Create a function that fails 4 times then succeeds
        failures = [Exception("fail") for _ in range(4)]
        failures.append("success")
        mock_func = MagicMock(side_effect=failures)
        result = retry_with_backoff(mock_func, max_attempts=5, base_delay=0.01)
        assert result == "success"
        assert mock_func.call_count == 5

    def test_function_returning_none(self):
        """Test function that returns None."""
        mock_func = MagicMock(return_value=None)
        result = retry_with_backoff(mock_func, max_attempts=1, base_delay=0.01)
        assert result is None

    def test_function_returning_zero(self):
        """Test function that returns 0 (falsy value)."""
        mock_func = MagicMock(return_value=0)
        result = retry_with_backoff(mock_func, max_attempts=1, base_delay=0.01)
        assert result == 0

    def test_function_returning_empty_list(self):
        """Test function that returns empty list."""
        mock_func = MagicMock(return_value=[])
        result = retry_with_backoff(mock_func, max_attempts=1, base_delay=0.01)
        assert result == []

    def test_logging_on_failure(self, mock_logger):
        """Test that failures are logged."""
        mock_func = MagicMock(side_effect=[Exception("fail1"), Exception("fail2"), "success"])
        result = retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)
        # Should log warning for each failed attempt (2 failures)
        assert mock_logger.warning.call_count == 2
        # Should log error after all attempts fail (none, since 3rd succeeds)
        assert mock_logger.error.call_count == 0

    def test_logging_all_fail(self, mock_logger):
        """Test logging when all attempts fail."""
        mock_func = MagicMock(side_effect=Exception("fail"))
        with pytest.raises(Exception):
            retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)
        # Should log warning for first 2 failures
        assert mock_logger.warning.call_count == 2
        # Should log error for final failure
        assert mock_logger.error.call_count == 1

    def test_different_exception_types(self):
        """Test handling of different exception types."""
        mock_func = MagicMock(
            side_effect=[ValueError("value error"), TypeError("type error"), "success"]
        )
        result = retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)
        assert result == "success"

    def test_custom_base_delay(self):
        """Test with custom base delay."""
        mock_func = MagicMock(return_value="success")
        with patch("utils.time.sleep") as mock_sleep:
            retry_with_backoff(mock_func, max_attempts=1, base_delay=5.0)
            mock_sleep.assert_not_called()  # Success on first try

    def test_with_default_max_attempts(self):
        """Test using default max_attempts from config."""
        mock_func = MagicMock(return_value="success")
        result = retry_with_backoff(mock_func)
        assert result == "success"
        assert mock_func.call_count == 1


# =============================================================================
# TEST: set_env_flag
# =============================================================================


class TestSetEnvFlag:
    """Tests for set_env_flag function."""

    @patch("utils.ENV_FILE", "/tmp/test.env")
    def test_set_new_flag(self, temp_env_file):
        """Test setting a new environment flag."""
        with patch("utils.ENV_FILE", temp_env_file):
            result = set_env_flag("NEW_KEY", "new_value")
            assert result is True

    @patch("utils.ENV_FILE", "/tmp/test.env")
    def test_set_flag_creates_file(self, temp_env_file):
        """Test that set_env_flag creates file if it doesn't exist."""
        with patch("utils.ENV_FILE", temp_env_file):
            result = set_env_flag("TEST_KEY", "test_value")
            assert result is True
            # Verify file was created and contains the flag
            with open(temp_env_file, "r") as f:
                content = f.read()
                assert "TEST_KEY=test_value" in content

    @patch("utils.ENV_FILE", "/tmp/test.env")
    def test_set_flag_new_flag(self, temp_env_file):
        """Test adding a new flag to existing file."""
        with patch("utils.ENV_FILE", temp_env_file):
            # Add first flag
            set_env_flag("KEY1", "value1")
            # Add second flag
            set_env_flag("KEY2", "value2")
            # Verify both are in file
            with open(temp_env_file, "r") as f:
                content = f.read()
                assert "KEY1=value1" in content
                assert "KEY2=value2" in content

    @patch("utils.ENV_FILE", "/tmp/test.env")
    def test_set_flag_update_existing(self, temp_env_file):
        """Test updating an existing flag."""
        with patch("utils.ENV_FILE", temp_env_file):
            # Set initial value
            set_env_flag("KEY", "old_value")
            # Update value
            set_env_flag("KEY", "new_value")
            # Verify updated value
            with open(temp_env_file, "r") as f:
                content = f.read()
                assert "KEY=new_value" in content
                assert "old_value" not in content

    @patch("utils.ENV_FILE", "/tmp/test.env")
    def test_set_flag_preserves_other_flags(self, temp_env_file):
        """Test that updating one flag preserves others."""
        with patch("utils.ENV_FILE", temp_env_file):
            set_env_flag("KEY1", "value1")
            set_env_flag("KEY2", "value2")
            set_env_flag("KEY1", "updated_value1")
            with open(temp_env_file, "r") as f:
                content = f.read()
                assert "KEY1=updated_value1" in content
                assert "KEY2=value2" in content

    @patch("utils.ENV_FILE", "/tmp/test.env")
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_set_flag_io_error(self, mock_file):
        """Test handling of IO errors."""
        result = set_env_flag("KEY", "value")
        assert result is False

    @patch("utils.ENV_FILE", "/tmp/test.env")
    @patch("builtins.open", side_effect=OSError("OS error"))
    def test_set_flag_os_error(self, mock_file):
        """Test handling of OS errors."""
        result = set_env_flag("KEY", "value")
        assert result is False

    @patch("utils.ENV_FILE", "/tmp/test.env")
    @patch("utils.logger")
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_set_flag_logs_error(self, mock_file, mock_logger):
        """Test that errors are logged."""
        set_env_flag("KEY", "value")
        mock_logger.error.assert_called()

    @patch("utils.ENV_FILE", "/tmp/test.env")
    def test_set_flag_empty_value(self, temp_env_file):
        """Test setting flag with empty value."""
        with patch("utils.ENV_FILE", temp_env_file):
            set_env_flag("EMPTY_KEY", "")
            with open(temp_env_file, "r") as f:
                content = f.read()
                assert "EMPTY_KEY=" in content

    @patch("utils.ENV_FILE", "/tmp/test.env")
    def test_set_flag_special_characters(self, temp_env_file):
        """Test setting flag with special characters."""
        with patch("utils.ENV_FILE", temp_env_file):
            set_env_flag("SPECIAL", "value=with|special:chars")
            with open(temp_env_file, "r") as f:
                content = f.read()
                assert "SPECIAL=value=with|special:chars" in content

    @patch("utils.ENV_FILE", "/tmp/test.env")
    def test_set_flag_multiple_operations(self, temp_env_file):
        """Test multiple set operations."""
        with patch("utils.ENV_FILE", temp_env_file):
            for i in range(5):
                result = set_env_flag(f"KEY{i}", f"value{i}")
                assert result is True


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests combining multiple utility functions."""

    def test_email_validation_and_domain_extraction(self):
        """Test validating email and extracting domain."""
        email = "user@example.com"
        assert is_valid_email(email) is True
        domain = extract_domain(email)
        assert domain == "example.com"
        assert is_safe_domain(domain) is True

    def test_personal_email_and_domain_safety(self):
        """Test checking personal email and domain safety."""
        email = "user@gmail.com"
        assert is_personal_email(email) is True
        domain = extract_domain(email)
        assert is_safe_domain(domain) is True

    def test_unsafe_domain_extraction(self):
        """Test extracting domain from email and checking safety."""
        email = "user@localhost"
        domain = extract_domain(email)
        assert domain == "localhost"
        assert is_safe_domain(domain) is False

    def test_safe_truncate_and_memory_parsing(self):
        """Test truncating text and parsing memory line."""
        long_text = "This is a very long note about the contact" * 3
        truncated = safe_truncate(long_text, 50)
        memory_line = f"contact:user@example.com | 2026-01-01 | {truncated}"
        parsed = parse_memory_line(memory_line)
        assert parsed is not None
        assert len(parsed[2]) <= 50

    def test_retry_with_backoff_for_email_validation(self):
        """Test retry logic with email validation function."""
        call_count = 0

        def validate_email_with_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Network error")
            return is_valid_email("user@example.com")

        result = retry_with_backoff(validate_email_with_retry, max_attempts=3, base_delay=0.01)
        assert result is True
        assert call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
