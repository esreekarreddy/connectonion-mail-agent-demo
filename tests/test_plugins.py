"""
Tests for custom plugins.

Verifies that plugins are properly structured and can be imported/used.
"""

import pytest
from plugins import approval_workflow, email_insights_plugin, agent_visibility_plugin


def test_plugins_importable():
    """Test that all plugins can be imported."""
    assert approval_workflow is not None
    assert email_insights_plugin is not None
    assert agent_visibility_plugin is not None


def test_approval_workflow_structure():
    """Test that approval_workflow is a list of event handlers."""
    assert isinstance(approval_workflow, list)
    assert len(approval_workflow) > 0
    # Each item should be an event handler (callable)
    for handler in approval_workflow:
        assert callable(handler)


def test_email_insights_plugin_structure():
    """Test that email_insights_plugin is a list of event handlers."""
    assert isinstance(email_insights_plugin, list)
    assert len(email_insights_plugin) > 0
    for handler in email_insights_plugin:
        assert callable(handler)


def test_agent_visibility_plugin_structure():
    """Test that agent_visibility_plugin is a list of event handlers."""
    assert isinstance(agent_visibility_plugin, list)
    assert len(agent_visibility_plugin) > 0
    for handler in agent_visibility_plugin:
        assert callable(handler)


def test_plugin_integration():
    """Test that plugins can be added to an agent."""
    from agent import _build_plugins

    plugins = _build_plugins()

    # Should have at least our 3 custom plugins + re_act
    assert len(plugins) >= 4

    # Verify our custom plugins are included
    assert approval_workflow in plugins
    assert email_insights_plugin in plugins
    assert agent_visibility_plugin in plugins


@pytest.mark.skipif(True, reason="Requires ConnectOnion agent instance")
def test_approval_workflow_handler():
    """Test that approval workflow handler works (requires agent)."""
    # This would test the actual handler logic
    # Skipped in unit tests as it requires a full agent setup
    pass


@pytest.mark.skipif(True, reason="Requires LLM API")
def test_email_insights_handler():
    """Test that email insights handler works (requires LLM API)."""
    # This would test the actual handler logic with llm_do()
    # Skipped as it requires API access
    pass
