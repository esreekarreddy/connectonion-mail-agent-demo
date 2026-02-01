"""Email Agent - Email management with unique capabilities.

Features:
1. Contact Intelligence: Research contacts via web before emailing
2. Voice Email: Dictate emails via audio, agent transcribes and drafts
"""

import logging
import os
import threading
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel
from connectonion import Memory, WebFetch, Shell, TodoList, llm_do, transcribe
from connectonion.useful_plugins import re_act, gmail_plugin, calendar_plugin

logger = logging.getLogger(__name__)

from config import (
    DEFAULT_MODEL,
    MAX_ITERATIONS_MAIN,
    MAX_ITERATIONS_CRM,
    PERSONAL_EMAIL_DOMAINS,
    MAX_PAGE_CONTENT_LENGTH,
    MIN_VALID_PAGE_CONTENT,
    MIN_VALID_CACHE_LENGTH,
    MEMORY_FILE,
    DEFAULT_CRM_MAX_EMAILS,
    DEFAULT_CRM_TOP_N,
    SUPPORTED_AUDIO_FORMATS,
    MAX_AUDIO_FILE_SIZE_BYTES,
)
from utils import (
    is_safe_domain,
    is_valid_email,
    is_personal_email,
    extract_domain,
    safe_truncate,
    retry_with_backoff,
)

memory = Memory(memory_file=MEMORY_FILE)
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
    if not is_valid_email(email):
        return f"Invalid email: {email}"

    # MEMORY-FIRST: Check if already researched to avoid expensive API calls
    cached = memory.read_memory(f"contact:{email}")
    if (
        cached
        and len(str(cached)) > MIN_VALID_CACHE_LENGTH
        and "not found" not in str(cached).lower()
    ):
        return f"📋 Using cached intelligence for {email}:\n\n{cached}\n\n_To refresh this data, run: `/research {email}` again_"

    domain = extract_domain(email)
    if not domain:
        return f"Could not extract domain from: {email}"

    if is_personal_email(email):
        return f"Personal email domain ({domain}). No company website to research."

    # SSRF protection: validate domain before fetching
    if not is_safe_domain(domain):
        return f"Cannot research domain: {domain} (blocked for security)"

    url = f"https://{domain}"
    try:
        page_content = web.fetch(url)
        if not page_content or len(page_content) < MIN_VALID_PAGE_CONTENT:
            return f"Could not fetch {url}"
    except Exception as e:
        return f"Error fetching {url}: {e}"

    try:
        social_links = web.get_social_links(url)
    except Exception as e:
        logger.debug(f"Social links extraction failed: {e}")
        social_links = []

    prompt = f"""Analyze this company website for someone about to email {email}.

Website content from {url}:
{safe_truncate(page_content, MAX_PAGE_CONTENT_LENGTH)}

Social links found: {social_links}

Provide intelligence for crafting a personalized email."""

    try:
        intel = retry_with_backoff(llm_do, prompt, output=ContactIntel, temperature=0.3)

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

    resolved_path = audio_path.resolve()
    cwd = Path.cwd().resolve()
    if not str(resolved_path).startswith(str(cwd)):
        logger.warning(f"Path traversal attempt blocked: {audio_file}")
        return f"Error: Audio file must be within project directory"

    if audio_path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
        return f"Error: Unsupported format {audio_path.suffix}. Use: {', '.join(SUPPORTED_AUDIO_FORMATS)}"

    file_size = audio_path.stat().st_size
    if file_size > MAX_AUDIO_FILE_SIZE_BYTES:
        return f"Error: Audio file too large ({file_size // (1024 * 1024)}MB). Max: {MAX_AUDIO_FILE_SIZE_BYTES // (1024 * 1024)}MB"

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
        intent = retry_with_backoff(llm_do, intent_prompt, output=EmailIntent, temperature=0.2)
    except Exception as e:
        return f"Could not understand intent: {e}"

    recipient = recipient_hint or intent.recipient or ""
    contact_context = ""

    if recipient and "@" in recipient:
        if not is_personal_email(recipient):
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
        draft = retry_with_backoff(llm_do, draft_prompt, output=EmailDraft, temperature=0.4)
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
    """Build the list of tools available to the main agent.

    Returns:
        list: Tools including memory, shell, todo, web, and unique features.
        Gmail and Calendar are added if authenticated.
    """
    tools = [memory, shell, todo, web, research_contact, voice_to_email]
    if gmail:
        tools.insert(0, gmail)
    if calendar:
        tools.insert(1 if gmail else 0, calendar)
    return tools


def _build_plugins():
    """Build the list of plugins for the main agent.

    Returns:
        list: Plugin lists including re_act, approval_workflow,
        email_insights, agent_visibility, and optional gmail/calendar plugins.
    """
    from plugins import approval_workflow, email_insights_plugin, agent_visibility_plugin

    plugins = [re_act]
    plugins.extend([approval_workflow, email_insights_plugin, agent_visibility_plugin])

    if gmail:
        plugins.append(gmail_plugin)
    if calendar:
        plugins.append(calendar_plugin)

    return plugins


def get_agent():
    """Get the singleton Email Agent instance.

    Thread-safe lazy initialization of the main agent.
    Creates the agent on first call, returns cached instance thereafter.

    Returns:
        Agent: The configured Email Agent instance.
    """
    global _agent
    with _lock:
        if _agent is None:
            from connectonion import Agent

            _agent = Agent(
                name="email-agent",
                system_prompt="prompts/agent.md",
                tools=_build_tools() + [init_crm_database],
                plugins=_build_plugins(),
                model=DEFAULT_MODEL,
                max_iterations=MAX_ITERATIONS_MAIN,
            )
        return _agent


def reset_agent():
    """Reset the agent singleton for testing purposes.

    Clears the cached agent instance so get_agent() will create
    a fresh instance on next call. Only use in tests.
    """
    global _agent, _init_crm_agent
    with _lock:
        _agent = None
        _init_crm_agent = None


def _get_init_crm_agent():
    """Get the singleton CRM initialization agent.

    Thread-safe lazy initialization of the sub-agent used for
    CRM database setup. Uses a focused system prompt for contact extraction.

    Returns:
        Agent: The CRM initialization agent instance.
    """
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
                max_iterations=MAX_ITERATIONS_CRM,
                model=DEFAULT_MODEL,
                log=False,
            )
        return _init_crm_agent


def init_crm_database(
    max_emails: int = DEFAULT_CRM_MAX_EMAILS, top_n: int = DEFAULT_CRM_TOP_N
) -> str:
    """Initialize CRM by extracting and analyzing top contacts from emails."""
    if not gmail:
        return "Gmail not connected. Run 'co auth google' first."

    # MEMORY-FIRST: Check if CRM already initialized
    cached_contacts = memory.read_memory("crm:all_contacts")
    if (
        cached_contacts
        and len(str(cached_contacts)) > 100
        and "not found" not in str(cached_contacts).lower()
    ):
        return f"📋 CRM already initialized with {len(str(cached_contacts).split(chr(10)))} contacts.\n\n_Use `/init-crm` with force=True to re-initialize or run `/contacts` to view._"

    agent = _get_init_crm_agent()
    result = agent.input(f"Initialize CRM: Extract top {top_n} contacts from {max_emails} emails.")
    return f"✅ CRM initialized. Use read_memory() to access contact data.\n\n{result}"
