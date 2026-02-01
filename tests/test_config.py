"""Tests for config.py - configuration constants and environment variable overrides.

This module tests:
- Default configuration values
- Environment variable overrides
- Set and list population
- Type correctness of configurations
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch
import importlib

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfigDefaults:
    """Tests for default configuration values."""

    def test_default_model(self):
        """Test default model configuration."""
        import config

        assert config.DEFAULT_MODEL == "co/claude-opus-4-5"

    def test_fast_model(self):
        """Test fast model configuration."""
        import config

        assert config.FAST_MODEL == "co/gemini-2.5-flash"

    def test_max_iterations_main(self):
        """Test max iterations for main agent."""
        import config

        assert config.MAX_ITERATIONS_MAIN == 20
        assert isinstance(config.MAX_ITERATIONS_MAIN, int)

    def test_max_iterations_crm(self):
        """Test max iterations for CRM agent."""
        import config

        assert config.MAX_ITERATIONS_CRM == 30
        assert isinstance(config.MAX_ITERATIONS_CRM, int)

    def test_personal_email_domains_populated(self):
        """Test that personal email domains are populated."""
        import config

        assert len(config.PERSONAL_EMAIL_DOMAINS) > 0
        assert isinstance(config.PERSONAL_EMAIL_DOMAINS, set)

    def test_personal_email_domains_common(self):
        """Test that common personal email domains are included."""
        import config

        expected_domains = {
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "icloud.com",
            "aol.com",
        }
        assert expected_domains.issubset(config.PERSONAL_EMAIL_DOMAINS)

    def test_personal_email_domains_complete_list(self):
        """Test all personal email domains."""
        import config

        expected_domains = {
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "icloud.com",
            "aol.com",
            "protonmail.com",
            "proton.me",
            "mail.com",
            "zoho.com",
            "yandex.com",
            "gmx.com",
            "fastmail.com",
            "tutanota.com",
            "hey.com",
        }
        assert config.PERSONAL_EMAIL_DOMAINS == expected_domains

    def test_blocked_domain_patterns_populated(self):
        """Test that blocked domain patterns are populated."""
        import config

        assert len(config.BLOCKED_DOMAIN_PATTERNS) > 0
        assert isinstance(config.BLOCKED_DOMAIN_PATTERNS, list)

    def test_blocked_domain_patterns_content(self):
        """Test that blocked domain patterns contain expected patterns."""
        import config

        patterns_str = " ".join(config.BLOCKED_DOMAIN_PATTERNS)
        assert "127" in patterns_str  # localhost patterns
        assert "localhost" in patterns_str
        assert "192" in patterns_str  # private IP patterns
        assert "10" in patterns_str
        assert "172" in patterns_str

    def test_blocked_domain_patterns_count(self):
        """Test that blocked domain patterns has expected count."""
        import config

        assert len(config.BLOCKED_DOMAIN_PATTERNS) == 15

    def test_max_page_content_length(self):
        """Test max page content length."""
        import config

        assert config.MAX_PAGE_CONTENT_LENGTH == 4000
        assert isinstance(config.MAX_PAGE_CONTENT_LENGTH, int)

    def test_max_email_preview_length(self):
        """Test max email preview length."""
        import config

        assert config.MAX_EMAIL_PREVIEW_LENGTH == 2000
        assert isinstance(config.MAX_EMAIL_PREVIEW_LENGTH, int)

    def test_max_body_preview_length(self):
        """Test max body preview length."""
        import config

        assert config.MAX_BODY_PREVIEW_LENGTH == 200
        assert isinstance(config.MAX_BODY_PREVIEW_LENGTH, int)

    def test_min_valid_page_content(self):
        """Test minimum valid page content."""
        import config

        assert config.MIN_VALID_PAGE_CONTENT == 100
        assert isinstance(config.MIN_VALID_PAGE_CONTENT, int)

    def test_min_valid_cache_length(self):
        """Test minimum valid cache length."""
        import config

        assert config.MIN_VALID_CACHE_LENGTH == 50
        assert isinstance(config.MIN_VALID_CACHE_LENGTH, int)

    def test_relationship_critical_days(self):
        """Test relationship critical days threshold."""
        import config

        assert config.RELATIONSHIP_CRITICAL_DAYS == 14
        assert isinstance(config.RELATIONSHIP_CRITICAL_DAYS, int)

    def test_relationship_warning_days(self):
        """Test relationship warning days threshold."""
        import config

        assert config.RELATIONSHIP_WARNING_DAYS == 7
        assert isinstance(config.RELATIONSHIP_WARNING_DAYS, int)

    def test_relationship_fallback_days(self):
        """Test relationship fallback days."""
        import config

        assert config.RELATIONSHIP_FALLBACK_DAYS == 5
        assert isinstance(config.RELATIONSHIP_FALLBACK_DAYS, int)

    def test_default_crm_max_emails(self):
        """Test default CRM max emails."""
        import config

        assert config.DEFAULT_CRM_MAX_EMAILS == 500
        assert isinstance(config.DEFAULT_CRM_MAX_EMAILS, int)

    def test_default_crm_top_n(self):
        """Test default CRM top N."""
        import config

        assert config.DEFAULT_CRM_TOP_N == 10
        assert isinstance(config.DEFAULT_CRM_TOP_N, int)

    def test_default_gmail_search_limit(self):
        """Test default Gmail search limit."""
        import config

        assert config.DEFAULT_GMAIL_SEARCH_LIMIT == 50
        assert isinstance(config.DEFAULT_GMAIL_SEARCH_LIMIT, int)

    def test_max_topics_display(self):
        """Test max topics display."""
        import config

        assert config.MAX_TOPICS_DISPLAY == 3
        assert isinstance(config.MAX_TOPICS_DISPLAY, int)

    def test_subprocess_timeout(self):
        """Test subprocess timeout."""
        import config

        assert config.SUBPROCESS_TIMEOUT == 120
        assert isinstance(config.SUBPROCESS_TIMEOUT, int)

    def test_llm_retry_attempts(self):
        """Test LLM retry attempts."""
        import config

        assert config.LLM_RETRY_ATTEMPTS == 3
        assert isinstance(config.LLM_RETRY_ATTEMPTS, int)

    def test_llm_retry_delay(self):
        """Test LLM retry delay."""
        import config

        assert config.LLM_RETRY_DELAY == 1.0
        assert isinstance(config.LLM_RETRY_DELAY, float)

    def test_max_audio_file_size_mb(self):
        """Test max audio file size in MB."""
        import config

        assert config.MAX_AUDIO_FILE_SIZE_MB == 25
        assert isinstance(config.MAX_AUDIO_FILE_SIZE_MB, int)

    def test_max_audio_file_size_bytes(self):
        """Test max audio file size in bytes."""
        import config

        assert config.MAX_AUDIO_FILE_SIZE_BYTES == 25 * 1024 * 1024
        assert isinstance(config.MAX_AUDIO_FILE_SIZE_BYTES, int)

    def test_max_audio_file_size_bytes_calculation(self):
        """Test that audio file size bytes is correctly calculated."""
        import config

        expected_bytes = config.MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024
        assert config.MAX_AUDIO_FILE_SIZE_BYTES == expected_bytes

    def test_supported_audio_formats_populated(self):
        """Test that supported audio formats are populated."""
        import config

        assert len(config.SUPPORTED_AUDIO_FORMATS) > 0
        assert isinstance(config.SUPPORTED_AUDIO_FORMATS, set)

    def test_supported_audio_formats_content(self):
        """Test that supported audio formats contain expected formats."""
        import config

        expected_formats = {".wav", ".mp3", ".aiff", ".aac", ".ogg", ".flac", ".m4a"}
        assert config.SUPPORTED_AUDIO_FORMATS == expected_formats

    def test_data_dir(self):
        """Test data directory path."""
        import config

        assert config.DATA_DIR == "data"

    def test_memory_file_path(self):
        """Test memory file path."""
        import config

        assert "memory.md" in config.MEMORY_FILE
        assert config.MEMORY_FILE.startswith("data")

    def test_contacts_file_path(self):
        """Test contacts file path."""
        import config

        assert "contacts.csv" in config.CONTACTS_FILE
        assert config.CONTACTS_FILE.startswith("data")

    def test_env_file_path(self):
        """Test environment file path."""
        import config

        assert config.ENV_FILE == ".env"

    def test_insights_cache_ttl_seconds(self):
        """Test insights cache TTL in seconds."""
        import config

        assert config.INSIGHTS_CACHE_TTL_SECONDS == 300
        assert isinstance(config.INSIGHTS_CACHE_TTL_SECONDS, int)


class TestConfigEnvOverrides:
    """Tests for environment variable overrides."""

    def test_email_agent_model_override(self):
        """Test EMAIL_AGENT_MODEL environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_MODEL": "co/gpt-5"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.DEFAULT_MODEL == "co/gpt-5"

    def test_email_agent_fast_model_override(self):
        """Test EMAIL_AGENT_FAST_MODEL environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_FAST_MODEL": "co/claude-haiku"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.FAST_MODEL == "co/claude-haiku"

    def test_email_agent_max_iterations_override(self):
        """Test EMAIL_AGENT_MAX_ITERATIONS environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_MAX_ITERATIONS": "50"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.MAX_ITERATIONS_MAIN == 50

    def test_email_agent_crm_max_iterations_override(self):
        """Test EMAIL_AGENT_CRM_MAX_ITERATIONS environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_CRM_MAX_ITERATIONS": "60"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.MAX_ITERATIONS_CRM == 60

    def test_email_agent_max_page_content_override(self):
        """Test EMAIL_AGENT_MAX_PAGE_CONTENT environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_MAX_PAGE_CONTENT": "8000"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.MAX_PAGE_CONTENT_LENGTH == 8000

    def test_email_agent_max_email_preview_override(self):
        """Test EMAIL_AGENT_MAX_EMAIL_PREVIEW environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_MAX_EMAIL_PREVIEW": "3000"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.MAX_EMAIL_PREVIEW_LENGTH == 3000

    def test_email_agent_max_body_preview_override(self):
        """Test EMAIL_AGENT_MAX_BODY_PREVIEW environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_MAX_BODY_PREVIEW": "500"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.MAX_BODY_PREVIEW_LENGTH == 500

    def test_email_agent_critical_days_override(self):
        """Test EMAIL_AGENT_CRITICAL_DAYS environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_CRITICAL_DAYS": "21"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.RELATIONSHIP_CRITICAL_DAYS == 21

    def test_email_agent_warning_days_override(self):
        """Test EMAIL_AGENT_WARNING_DAYS environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_WARNING_DAYS": "10"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.RELATIONSHIP_WARNING_DAYS == 10

    def test_email_agent_crm_max_emails_override(self):
        """Test EMAIL_AGENT_CRM_MAX_EMAILS environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_CRM_MAX_EMAILS": "1000"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.DEFAULT_CRM_MAX_EMAILS == 1000

    def test_email_agent_crm_top_n_override(self):
        """Test EMAIL_AGENT_CRM_TOP_N environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_CRM_TOP_N": "20"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.DEFAULT_CRM_TOP_N == 20

    def test_email_agent_gmail_search_limit_override(self):
        """Test EMAIL_AGENT_GMAIL_SEARCH_LIMIT environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_GMAIL_SEARCH_LIMIT": "100"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.DEFAULT_GMAIL_SEARCH_LIMIT == 100

    def test_email_agent_max_topics_display_override(self):
        """Test EMAIL_AGENT_MAX_TOPICS_DISPLAY environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_MAX_TOPICS_DISPLAY": "5"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.MAX_TOPICS_DISPLAY == 5

    def test_email_agent_subprocess_timeout_override(self):
        """Test EMAIL_AGENT_SUBPROCESS_TIMEOUT environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_SUBPROCESS_TIMEOUT": "300"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.SUBPROCESS_TIMEOUT == 300

    def test_email_agent_llm_retries_override(self):
        """Test EMAIL_AGENT_LLM_RETRIES environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_LLM_RETRIES": "5"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.LLM_RETRY_ATTEMPTS == 5

    def test_email_agent_llm_retry_delay_override(self):
        """Test EMAIL_AGENT_LLM_RETRY_DELAY environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_LLM_RETRY_DELAY": "2.5"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.LLM_RETRY_DELAY == 2.5

    def test_email_agent_max_audio_mb_override(self):
        """Test EMAIL_AGENT_MAX_AUDIO_MB environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_MAX_AUDIO_MB": "50"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.MAX_AUDIO_FILE_SIZE_MB == 50
            assert config.MAX_AUDIO_FILE_SIZE_BYTES == 50 * 1024 * 1024

    def test_email_agent_insights_cache_ttl_override(self):
        """Test EMAIL_AGENT_INSIGHTS_CACHE_TTL environment variable override."""
        with patch.dict(os.environ, {"EMAIL_AGENT_INSIGHTS_CACHE_TTL": "600"}):
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            import config

            assert config.INSIGHTS_CACHE_TTL_SECONDS == 600


class TestConfigTypeConsistency:
    """Tests for type consistency of configuration values."""

    def test_all_integer_configs_are_integers(self):
        """Test that all integer configurations are integers."""
        import config

        int_configs = [
            config.MAX_ITERATIONS_MAIN,
            config.MAX_ITERATIONS_CRM,
            config.MAX_PAGE_CONTENT_LENGTH,
            config.MAX_EMAIL_PREVIEW_LENGTH,
            config.MAX_BODY_PREVIEW_LENGTH,
            config.MIN_VALID_PAGE_CONTENT,
            config.MIN_VALID_CACHE_LENGTH,
            config.RELATIONSHIP_CRITICAL_DAYS,
            config.RELATIONSHIP_WARNING_DAYS,
            config.RELATIONSHIP_FALLBACK_DAYS,
            config.DEFAULT_CRM_MAX_EMAILS,
            config.DEFAULT_CRM_TOP_N,
            config.DEFAULT_GMAIL_SEARCH_LIMIT,
            config.MAX_TOPICS_DISPLAY,
            config.SUBPROCESS_TIMEOUT,
            config.LLM_RETRY_ATTEMPTS,
            config.MAX_AUDIO_FILE_SIZE_MB,
            config.MAX_AUDIO_FILE_SIZE_BYTES,
            config.INSIGHTS_CACHE_TTL_SECONDS,
        ]
        for value in int_configs:
            assert isinstance(value, int), f"Expected int, got {type(value)}"

    def test_float_configs_are_floats(self):
        """Test that float configurations are floats."""
        import config

        assert isinstance(config.LLM_RETRY_DELAY, float)

    def test_string_configs_are_strings(self):
        """Test that string configurations are strings."""
        import config

        string_configs = [
            config.DEFAULT_MODEL,
            config.FAST_MODEL,
            config.DATA_DIR,
            config.MEMORY_FILE,
            config.CONTACTS_FILE,
            config.ENV_FILE,
        ]
        for value in string_configs:
            assert isinstance(value, str), f"Expected str, got {type(value)}"

    def test_set_configs_are_sets(self):
        """Test that set configurations are sets."""
        import config

        assert isinstance(config.PERSONAL_EMAIL_DOMAINS, set)
        assert isinstance(config.SUPPORTED_AUDIO_FORMATS, set)

    def test_list_configs_are_lists(self):
        """Test that list configurations are lists."""
        import config

        assert isinstance(config.BLOCKED_DOMAIN_PATTERNS, list)


class TestConfigRelationships:
    """Tests for relationships between configuration values."""

    def test_max_audio_file_size_consistency(self):
        """Test that audio file size MB and bytes are consistent."""
        import config

        expected_bytes = config.MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024
        assert config.MAX_AUDIO_FILE_SIZE_BYTES == expected_bytes

    def test_email_content_limits_hierarchy(self):
        """Test that email content limits have logical hierarchy."""
        import config

        assert config.MAX_PAGE_CONTENT_LENGTH > config.MAX_EMAIL_PREVIEW_LENGTH
        assert config.MAX_EMAIL_PREVIEW_LENGTH > config.MAX_BODY_PREVIEW_LENGTH

    def test_minimum_values_positive(self):
        """Test that minimum content values are positive."""
        import config

        assert config.MIN_VALID_PAGE_CONTENT > 0
        assert config.MIN_VALID_CACHE_LENGTH > 0

    def test_timeout_values_reasonable(self):
        """Test that timeout values are reasonable."""
        import config

        assert config.SUBPROCESS_TIMEOUT > 0
        assert config.LLM_RETRY_ATTEMPTS > 0
        assert config.LLM_RETRY_DELAY > 0

    def test_relationship_days_logical_order(self):
        """Test that relationship days have logical order."""
        import config

        assert config.RELATIONSHIP_WARNING_DAYS < config.RELATIONSHIP_CRITICAL_DAYS
        assert config.RELATIONSHIP_FALLBACK_DAYS < config.RELATIONSHIP_WARNING_DAYS

    def test_crm_defaults_reasonable(self):
        """Test that CRM defaults are reasonable."""
        import config

        assert config.DEFAULT_CRM_TOP_N < config.DEFAULT_CRM_MAX_EMAILS
        assert config.DEFAULT_CRM_TOP_N > 0
        assert config.DEFAULT_CRM_MAX_EMAILS > 0

    def test_max_iterations_positive(self):
        """Test that max iterations are positive."""
        import config

        assert config.MAX_ITERATIONS_MAIN > 0
        assert config.MAX_ITERATIONS_CRM > 0

    def test_max_topics_display_positive(self):
        """Test that max topics display is positive."""
        import config

        assert config.MAX_TOPICS_DISPLAY > 0


class TestConfigEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_environment_uses_defaults(self):
        """Test that empty environment variables use defaults."""
        # This test verifies the behavior when no env vars are set
        # The config module should use the hardcoded defaults
        import config

        assert config.DEFAULT_MODEL == "co/claude-opus-4-5"
        assert config.FAST_MODEL == "co/gemini-2.5-flash"

    def test_path_construction_correct(self):
        """Test that file paths are constructed correctly."""
        import config

        assert config.MEMORY_FILE == os.path.join("data", "memory.md")
        assert config.CONTACTS_FILE == os.path.join("data", "contacts.csv")

    def test_personal_email_domains_no_duplicates(self):
        """Test that personal email domains has no duplicates."""
        import config

        original_len = len(config.PERSONAL_EMAIL_DOMAINS)
        unique_len = len(set(config.PERSONAL_EMAIL_DOMAINS))
        assert original_len == unique_len

    def test_blocked_domain_patterns_no_duplicates(self):
        """Test that blocked domain patterns has no duplicates."""
        import config

        original_len = len(config.BLOCKED_DOMAIN_PATTERNS)
        unique_len = len(set(config.BLOCKED_DOMAIN_PATTERNS))
        assert original_len == unique_len

    def test_supported_audio_formats_no_duplicates(self):
        """Test that supported audio formats has no duplicates."""
        import config

        original_len = len(config.SUPPORTED_AUDIO_FORMATS)
        unique_len = len(set(config.SUPPORTED_AUDIO_FORMATS))
        assert original_len == unique_len

    def test_audio_formats_lowercase(self):
        """Test that audio format extensions are lowercase."""
        import config

        for fmt in config.SUPPORTED_AUDIO_FORMATS:
            assert fmt == fmt.lower()

    def test_blocked_patterns_not_empty_string(self):
        """Test that blocked patterns are not empty strings."""
        import config

        for pattern in config.BLOCKED_DOMAIN_PATTERNS:
            assert len(pattern) > 0

    def test_personal_domains_not_empty_string(self):
        """Test that personal domains are not empty strings."""
        import config

        for domain in config.PERSONAL_EMAIL_DOMAINS:
            assert len(domain) > 0
            assert domain == domain.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
