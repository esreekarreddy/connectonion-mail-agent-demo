"""Email insights plugin - adds AI-powered analysis to email results."""

from __future__ import annotations

import hashlib
import logging
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from connectonion import after_tools, llm_do
from pydantic import BaseModel
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    INSIGHTS_CACHE_TTL_SECONDS,
    FAST_MODEL,
    MAX_EMAIL_PREVIEW_LENGTH,
    MAX_TOPICS_DISPLAY,
)
from utils import retry_with_backoff

logger = logging.getLogger(__name__)
console = Console()


class EmailInsight(BaseModel):
    priority_level: str
    action_needed: bool
    key_topics: List[str]
    sentiment: str
    suggested_action: Optional[str] = None


_insights_cache: Dict[str, Tuple[EmailInsight, float]] = {}


def _get_cache_key(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()


def _get_cached_insight(content: str) -> Optional[EmailInsight]:
    cache_key = _get_cache_key(content)
    if cache_key in _insights_cache:
        insight, timestamp = _insights_cache[cache_key]
        if time.time() - timestamp < INSIGHTS_CACHE_TTL_SECONDS:
            return insight
        del _insights_cache[cache_key]
    return None


def _cache_insight(content: str, insight: EmailInsight) -> None:
    cache_key = _get_cache_key(content)
    _insights_cache[cache_key] = (insight, time.time())


def add_email_insights(agent):
    last_result = agent.current_session.get("last_result", "")
    last_tool = agent.current_session.get("last_tool", {})
    tool_name = last_tool.get("name", "")

    if "read" not in tool_name.lower() and "inbox" not in tool_name.lower():
        return

    if not last_result or len(last_result) < 50:
        return

    content_to_analyze = last_result[:MAX_EMAIL_PREVIEW_LENGTH]

    cached = _get_cached_insight(content_to_analyze)
    if cached:
        _display_insight(cached)
        return

    try:
        insight = retry_with_backoff(
            llm_do,
            f"Analyze this email and provide structured insights:\n\n{content_to_analyze}",
            output=EmailInsight,
            model=FAST_MODEL,
            temperature=0.3,
        )

        _cache_insight(content_to_analyze, insight)
        _display_insight(insight)

    except Exception as e:
        logger.warning(f"Email insights failed: {e}")


def _display_insight(insight: EmailInsight) -> None:
    priority_emoji = {"urgent": "🔴", "high": "🟠", "normal": "🟢", "low": "⚪"}.get(
        insight.priority_level.lower(), "🟢"
    )

    sentiment_emoji = {"positive": "😊", "neutral": "😐", "negative": "😟", "mixed": "🤔"}.get(
        insight.sentiment.lower(), "😐"
    )

    console.print(f"\n[bold cyan]📊 Email Insight:[/bold cyan]")
    console.print(
        f"{priority_emoji} Priority: {insight.priority_level.upper()} | {sentiment_emoji} Sentiment: {insight.sentiment}"
    )
    console.print(f"Topics: {', '.join(insight.key_topics[:MAX_TOPICS_DISPLAY])}")
    if insight.action_needed and insight.suggested_action:
        console.print(f"💡 Suggested: {insight.suggested_action}")


email_insights_plugin = [after_tools(add_email_insights)]
