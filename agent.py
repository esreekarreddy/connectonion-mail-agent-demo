"""Email Agent - Email management with unique capabilities.

Features:
1. Contact Intelligence: Research contacts via web before emailing
2. Voice Email: Dictate emails via audio, agent transcribes and drafts
"""

import os
import threading
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel
from connectonion import Memory, WebFetch, Shell, TodoList, llm_do, transcribe
from connectonion.useful_plugins import re_act, gmail_plugin, calendar_plugin

memory = Memory(memory_file="data/memory.md")
web = WebFetch()
shell = Shell()
todo = TodoList()

has_gmail = (
    os.getenv("LINKED_GMAIL", "").lower() == "true" or os.getenv("GOOGLE_ACCESS_TOKEN", "") != ""
)
has_calendar = (
    os.getenv("LINKED_CALENDAR", "").lower() == "true" or os.getenv("GOOGLE_ACCESS_TOKEN", "") != ""
)

gmail = None
calendar = None

if has_gmail:
    from connectonion import Gmail

    gmail = Gmail()

if has_calendar:
    from connectonion import GoogleCalendar

    calendar = GoogleCalendar()


class ContactIntel(BaseModel):
    company: str
    role_guess: Optional[str] = None
    industry: str
    talking_points: List[str]
    tone_suggestion: str
    recent_news: Optional[str] = None


def research_contact(email: str) -> str:
    """Research a contact by fetching their company website and analyzing it."""
    if "@" not in email:
        return f"Invalid email: {email}"

    domain = email.split("@")[1]
    common = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]
    if domain in common:
        return f"Personal email domain ({domain}). No company website to research."

    url = f"https://{domain}"
    try:
        page_content = web.fetch(url)
        if not page_content or len(page_content) < 100:
            return f"Could not fetch {url}"
    except Exception as e:
        return f"Error fetching {url}: {e}"

    try:
        social_links = web.get_social_links(url)
    except Exception:
        social_links = []

    prompt = f"""Analyze this company website for someone about to email {email}.

Website content from {url}:
{page_content[:4000]}

Social links found: {social_links}

Provide intelligence for crafting a personalized email."""

    try:
        intel = llm_do(prompt, output=ContactIntel, temperature=0.3)

        result = f"""## Contact Intelligence: {email}

**Company:** {intel.company}
**Industry:** {intel.industry}
**Likely Role:** {intel.role_guess or "Unknown"}
**Suggested Tone:** {intel.tone_suggestion}

### Talking Points
"""
        for i, point in enumerate(intel.talking_points, 1):
            result += f"{i}. {point}\n"

        if intel.recent_news:
            result += f"\n### Recent News\n{intel.recent_news}\n"

        if social_links:
            result += f"\n### Social Links\n" + "\n".join(f"- {link}" for link in social_links[:5])

        memory.write_memory(f"contact:{email}", result)
        return result

    except Exception as e:
        return f"Analysis failed: {e}"


class EmailIntent(BaseModel):
    recipient: Optional[str] = None
    subject_hint: str
    key_points: List[str]
    tone: str
    action: str


class EmailDraft(BaseModel):
    to: str
    subject: str
    body: str
    needs_research: bool = False


def voice_to_email(audio_file: str, recipient_hint: str = "") -> str:
    """Convert voice memo to email draft using transcription and AI."""
    audio_path = Path(audio_file)
    if not audio_path.exists():
        return f"Error: Audio file not found: {audio_file}"

    valid_formats = {".wav", ".mp3", ".aiff", ".aac", ".ogg", ".flac", ".m4a"}
    if audio_path.suffix.lower() not in valid_formats:
        return f"Error: Unsupported format {audio_path.suffix}. Use: {', '.join(valid_formats)}"

    try:
        transcript = transcribe(
            audio=str(audio_path),
            prompt="Email dictation. The speaker is dictating an email to send.",
        )
    except Exception as e:
        return f"Transcription failed: {e}"

    if not transcript or len(transcript.strip()) < 10:
        return "Error: Could not transcribe audio. Please speak clearly and try again."

    intent_prompt = f"""Extract email intent from this voice memo transcript.

Transcript:
{transcript}

Recipient hint: {recipient_hint or "Not specified"}

Identify:
- Who should receive this email (look for names, emails, or roles)
- What is the main subject/topic
- Key points to include
- Appropriate tone (formal/casual/urgent)
- Action type (send new email, reply, or forward)"""

    try:
        intent = llm_do(intent_prompt, output=EmailIntent, temperature=0.2)
    except Exception as e:
        return f"Could not understand intent: {e}"

    recipient = recipient_hint or intent.recipient or ""
    contact_context = ""

    if recipient and "@" in recipient:
        domain = recipient.split("@")[1]
        personal_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]
        if domain not in personal_domains:
            contact_context = research_contact(recipient)

    draft_prompt = f"""Draft an email based on this voice memo.

Voice memo transcript:
{transcript}

Extracted intent:
- Recipient: {recipient or "Unknown - ask user"}
- Subject hint: {intent.subject_hint}
- Key points: {", ".join(intent.key_points)}
- Tone: {intent.tone}

Contact research:
{contact_context if contact_context else "No research available"}

Write a complete, ready-to-send email. Match the tone indicated.
If recipient is unknown, use [RECIPIENT] as placeholder."""

    try:
        draft = llm_do(draft_prompt, output=EmailDraft, temperature=0.4)
    except Exception as e:
        return f"Drafting failed: {e}"

    result = f"""## Voice Email Draft

**Transcription:**
> {transcript}

---

**To:** {draft.to}
**Subject:** {draft.subject}

{draft.body}

---

### Actions
- Say "send" to send this email
- Say "edit" to modify
- Say "research" to learn more about the recipient
- Say "cancel" to discard
"""

    memory.write_memory("voice_email:latest", result)
    memory.write_memory(
        "voice_email:draft", f"TO: {draft.to}\nSUBJECT: {draft.subject}\n\n{draft.body}"
    )

    return result


_agent = None
_init_crm_agent = None
_lock = threading.Lock()


def _build_tools():
    tools = [memory, shell, todo, web, research_contact, voice_to_email]
    if gmail:
        tools.insert(0, gmail)
    if calendar:
        tools.insert(1 if gmail else 0, calendar)
    return tools


def _build_plugins():
    from plugins import approval_workflow, email_insights_plugin, agent_visibility_plugin

    plugins = [re_act]
    plugins.extend([approval_workflow, email_insights_plugin, agent_visibility_plugin])

    if gmail:
        plugins.append(gmail_plugin)
    if calendar:
        plugins.append(calendar_plugin)

    return plugins


def get_agent():
    global _agent
    with _lock:
        if _agent is None:
            from connectonion import Agent

            _agent = Agent(
                name="email-agent",
                system_prompt="prompts/agent.md",
                tools=_build_tools() + [init_crm_database],
                plugins=_build_plugins(),
                model="co/claude-opus-4-5",
                max_iterations=20,
            )
        return _agent


def _get_init_crm_agent():
    global _init_crm_agent
    with _lock:
        if _init_crm_agent is None:
            from connectonion import Agent

            crm_tools = [memory, web]
            if gmail:
                crm_tools.insert(0, gmail)
            _init_crm_agent = Agent(
                name="crm-init",
                system_prompt="prompts/crm_init.md",
                tools=crm_tools,
                max_iterations=30,
                model="co/claude-sonnet-4-5",
                log=False,
            )
        return _init_crm_agent


def init_crm_database(max_emails: int = 500, top_n: int = 10) -> str:
    """Initialize CRM by extracting and analyzing top contacts from emails."""
    if not gmail:
        return "Gmail not connected. Run 'co auth google' first."
    agent = _get_init_crm_agent()
    result = agent.input(f"Initialize CRM: Extract top {top_n} contacts from {max_emails} emails.")
    return f"CRM initialized. Use read_memory() to access contact data.\n\n{result}"
