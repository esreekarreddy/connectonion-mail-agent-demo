"""Email insights plugin - adds AI-powered analysis to email results."""

from connectonion import after_tools, llm_do
from pydantic import BaseModel
from typing import List, Optional
from rich.console import Console

console = Console()


class EmailInsight(BaseModel):
    """Structured email analysis."""

    priority_level: str  # urgent, high, normal, low
    action_needed: bool
    key_topics: List[str]
    sentiment: str  # positive, neutral, negative, mixed
    suggested_action: Optional[str] = None


def add_email_insights(agent):
    """Add AI insights to email read results.

    Analyzes emails and adds priority badges and action suggestions.
    """
    last_result = agent.current_session.get("last_result", "")
    last_tool = agent.current_session.get("last_tool", {})
    tool_name = last_tool.get("name", "")

    # Only analyze email read operations
    if "read" not in tool_name.lower() and "inbox" not in tool_name.lower():
        return

    # Skip if result is too short (no email content)
    if not last_result or len(last_result) < 50:
        return

    try:
        # Analyze email content
        insight = llm_do(
            f"Analyze this email and provide structured insights:\n\n{last_result[:2000]}",
            output=EmailInsight,
            model="co/gemini-2.5-flash",
            temperature=0.3,
        )

        # Format insight annotation
        priority_emoji = {"urgent": "🔴", "high": "🟠", "normal": "🟢", "low": "⚪"}.get(
            insight.priority_level.lower(), "🟢"
        )

        sentiment_emoji = {"positive": "😊", "neutral": "😐", "negative": "😟", "mixed": "🤔"}.get(
            insight.sentiment.lower(), "😐"
        )

        # Display insight
        console.print(f"\n[bold cyan]📊 Email Insight:[/bold cyan]")
        console.print(
            f"{priority_emoji} Priority: {insight.priority_level.upper()} | {sentiment_emoji} Sentiment: {insight.sentiment}"
        )
        console.print(f"Topics: {', '.join(insight.key_topics[:3])}")
        if insight.action_needed and insight.suggested_action:
            console.print(f"💡 Suggested: {insight.suggested_action}")

    except Exception as e:
        # Insights are non-critical - log error but don't break user experience
        import logging

        logging.warning(f"Email insights failed: {e}")


# Export as plugin
email_insights_plugin = [after_tools(add_email_insights)]
