"""Custom ConnectOnion plugins for mailAgent."""

from plugins.approval_workflow import approval_workflow
from plugins.email_insights import email_insights_plugin
from plugins.agent_visibility import agent_visibility_plugin

__all__ = [
    "approval_workflow",
    "email_insights_plugin",
    "agent_visibility_plugin",
]
