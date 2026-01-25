"""
Tests for the Email Agent.

Simplified to match the new streamlined structure.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestContactIntelligence:
    """Tests for the unique feature: research_contact."""

    def test_research_contact_exists(self):
        """research_contact function should exist."""
        from agent import research_contact

        assert callable(research_contact)

    def test_research_contact_invalid_email(self):
        """Should return error for invalid email."""
        from agent import research_contact

        result = research_contact("not-an-email")
        assert "Invalid email" in result

    def test_research_contact_personal_domain(self):
        """Should return message for personal email domains."""
        from agent import research_contact

        result = research_contact("test@gmail.com")
        assert "Personal email domain" in result

    @patch("agent.web")
    @patch("agent.llm_do")
    def test_research_contact_corporate_domain(self, mock_llm_do, mock_web):
        """Should fetch and analyze corporate domains."""
        from agent import research_contact, ContactIntel

        mock_web.fetch.return_value = "Acme Corp - Enterprise Solutions"
        mock_web.get_social_links.return_value = ["linkedin.com/acme"]
        mock_llm_do.return_value = ContactIntel(
            company="Acme Corp",
            industry="Technology",
            talking_points=["Enterprise focus"],
            tone_suggestion="professional",
        )

        result = research_contact("ceo@acme.com")

        assert "Acme Corp" in result or mock_web.fetch.called


class TestVoiceEmail:
    """Tests for the unique feature: voice_to_email."""

    def test_voice_to_email_exists(self):
        """voice_to_email function should exist."""
        from agent import voice_to_email

        assert callable(voice_to_email)

    def test_voice_to_email_file_not_found(self):
        """Should return error for missing file."""
        from agent import voice_to_email

        result = voice_to_email("/nonexistent/file.mp3")
        assert "not found" in result.lower()

    def test_voice_to_email_invalid_format(self, tmp_path):
        """Should return error for unsupported format."""
        from agent import voice_to_email

        # Create a temp file with invalid extension
        bad_file = tmp_path / "test.txt"
        bad_file.write_text("not audio")
        result = voice_to_email(str(bad_file))
        assert "Unsupported format" in result or "Error" in result

    def test_email_intent_model_exists(self):
        """EmailIntent model should exist."""
        from agent import EmailIntent

        assert EmailIntent is not None

    def test_email_draft_model_exists(self):
        """EmailDraft model should exist."""
        from agent import EmailDraft

        assert EmailDraft is not None


class TestToolInstances:
    """Tests for shared tool instances."""

    def test_memory_exists(self):
        """Memory tool should be available."""
        from agent import memory

        assert memory is not None

    def test_web_exists(self):
        """WebFetch tool should be available."""
        from agent import web

        assert web is not None

    def test_shell_exists(self):
        """Shell tool should be available."""
        from agent import shell

        assert shell is not None


class TestAgentCreation:
    """Tests for agent factory functions."""

    def test_get_agent_function_exists(self):
        """get_agent function should exist."""
        from agent import get_agent

        assert callable(get_agent)

    def test_init_crm_database_exists(self):
        """init_crm_database function should exist."""
        from agent import init_crm_database

        assert callable(init_crm_database)

    def test_init_crm_no_gmail(self):
        """Should return error when Gmail not connected."""
        from agent import init_crm_database, gmail

        if gmail is None:
            result = init_crm_database()
            assert "Gmail not connected" in result


class TestCLICore:
    """Tests for CLI core functions."""

    def test_do_inbox_exists(self):
        """do_inbox function should exist."""
        from cli.core import do_inbox

        assert callable(do_inbox)

    def test_do_search_exists(self):
        """do_search function should exist."""
        from cli.core import do_search

        assert callable(do_search)

    def test_do_research_exists(self):
        """do_research function should exist."""
        from cli.core import do_research

        assert callable(do_research)

    def test_do_today_exists(self):
        """do_today function should exist."""
        from cli.core import do_today

        assert callable(do_today)

    def test_do_contacts_exists(self):
        """do_contacts function should exist."""
        from cli.core import do_contacts

        assert callable(do_contacts)


class TestPromptFiles:
    """Tests for prompt files."""

    def test_agent_prompt_exists(self):
        """Agent prompt file should exist."""
        from pathlib import Path

        prompt_path = Path("prompts/agent.md")
        assert prompt_path.exists()

    def test_agent_prompt_has_content(self):
        """Agent prompt should have substantial content."""
        from pathlib import Path

        prompt_path = Path("prompts/agent.md")
        content = prompt_path.read_text()
        assert len(content) > 1000  # Should be substantial

    def test_agent_prompt_mentions_unique_feature(self):
        """Agent prompt should mention research_contact."""
        from pathlib import Path

        prompt_path = Path("prompts/agent.md")
        content = prompt_path.read_text()
        assert "research_contact" in content or "Contact Intelligence" in content

    def test_crm_init_prompt_exists(self):
        """CRM init prompt file should exist."""
        from pathlib import Path

        prompt_path = Path("prompts/crm_init.md")
        assert prompt_path.exists()


class TestPydanticModels:
    """Tests for Pydantic models."""

    def test_contact_intel_model_exists(self):
        """ContactIntel model should exist."""
        from agent import ContactIntel

        assert ContactIntel is not None

    def test_contact_intel_model_fields(self):
        """ContactIntel should have expected fields."""
        from agent import ContactIntel

        intel = ContactIntel(
            company="Test Co",
            industry="Tech",
            talking_points=["Point 1"],
            tone_suggestion="casual",
        )

        assert intel.company == "Test Co"
        assert intel.industry == "Tech"
        assert len(intel.talking_points) == 1
        assert intel.tone_suggestion == "casual"


class TestCLICommands:
    """Tests for CLI Typer commands."""

    def test_app_exists(self):
        """Typer app should exist."""
        from cli.commands import app

        assert app is not None

    def test_commands_importable(self):
        """Essential command functions should be importable."""
        from cli.commands import inbox, search, research

        assert callable(inbox)
        assert callable(search)
        assert callable(research)
