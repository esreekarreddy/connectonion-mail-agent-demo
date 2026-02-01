"""Interactive Chat Mode for Email Agent using ConnectOnion TUI."""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

from connectonion.tui import Chat, CommandItem

from .contacts_provider import ContactProvider
from .core import (
    do_inbox,
    do_search,
    do_today,
    do_research,
    do_voice,
    do_init_crm,
    do_contacts,
    do_show,
    do_archive,
    do_star,
    do_mark_read,
    do_calendar,
    do_free,
    do_relationships,
    do_weekly,
)

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import set_env_flag
from config import SUBPROCESS_TIMEOUT


def _get_agent():
    from agent import get_agent

    return get_agent()


COMMANDS = [
    CommandItem(main="/today - Daily briefing", prefix="📅", id="/today"),
    CommandItem(main="/inbox - Show emails", prefix="📥", id="/inbox"),
    CommandItem(main="/search - Search emails", prefix="🔍", id="/search "),
    CommandItem(main="/research - Research contact", prefix="🔬", id="/research "),
    CommandItem(main="/voice - Dictate email", prefix="🎤", id="/voice "),
    CommandItem(main="/contacts - View contacts", prefix="👥", id="/contacts"),
    CommandItem(main="/init-crm - Initialize CRM", prefix="🗄️", id="/init-crm"),
    CommandItem(main="/relationships - Contact health", prefix="💚", id="/relationships"),
    CommandItem(main="/weekly - Email analytics", prefix="📊", id="/weekly"),
    CommandItem(main="/show - View email body", prefix="📄", id="/show "),
    CommandItem(main="/archive - Archive email", prefix="📦", id="/archive "),
    CommandItem(main="/star - Star email", prefix="⭐", id="/star "),
    CommandItem(main="/calendar - View events", prefix="📆", id="/calendar"),
    CommandItem(main="/free - Find free slots", prefix="⏰", id="/free"),
    CommandItem(main="/link-gmail - Connect Gmail", prefix="🔗", id="/link-gmail"),
    CommandItem(main="/help - Show commands", prefix="❓", id="/help"),
    CommandItem(main="/quit - Exit", prefix="👋", id="/quit"),
]


WELCOME = """## Email Agent

**Features:**
- `/research` - Research contacts before emailing
- `/voice` - Dictate emails via audio
- `/relationships` - Track contact health
- `/weekly` - Email productivity analytics

**Quick Start:**
- `/inbox` - Check your emails
- `/today` - Daily briefing
- `/help` - All commands

Or just type naturally to chat with the AI agent!
"""


HELP_MESSAGE = """## Commands

### Unique Features
- `/research <email>` - Research contact intelligence
- `/voice <file>` - Dictate email via audio
- `/relationships` - Contact health dashboard
- `/weekly` - Weekly email analytics

### Email
- `/today` - Daily email briefing
- `/inbox [n]` - Show recent emails
- `/search query` - Find specific emails
- `/show <id>` - View full email body
- `/archive <id>` - Archive email
- `/star <id>` - Star email

### CRM
- `/contacts` - View your contacts
- `/init-crm` - Setup CRM database

### Calendar
- `/calendar [days]` - Upcoming events
- `/free` - Find free time slots

### System
- `/link-gmail` - Connect Gmail account
- `/quit` - Exit the app

**Tip:** Just type naturally to chat with the AI agent!
"""


def _handle_error(error: Exception) -> str:
    error_msg = str(error).lower()

    if "credential" in error_msg or "auth" in error_msg or "token" in error_msg:
        return (
            f"**Authentication error**\n\n"
            f"`{error}`\n\n"
            "**To fix:**\n"
            "1. Run: `co auth google`\n"
            "2. Grant Gmail permissions\n"
            "3. Try again"
        )
    elif "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
        return f"**Network error**\n\n`{error}`\n\n**To fix:** Check your internet connection"
    else:
        return f"**Error**\n\n`{error}`\n\nTry `/help` to see available commands"


def start_interactive():
    agent = _get_agent()

    try:
        contact_provider = ContactProvider()
        contacts = contact_provider.to_command_items()
    except Exception as e:
        logger.debug(f"Contact provider failed: {e}")
        contacts = []

    chat = Chat(
        agent=agent,
        title="Email Agent",
        triggers={
            "/": COMMANDS,
            "@": contacts,
        },
        welcome=WELCOME,
        hints=["/ commands", "@ contacts", "Enter send", "Ctrl+D quit"],
        status_segments=[
            ("📧", "Email Agent", "cyan"),
            ("🤖", f"co/{agent.llm.model}", "magenta"),
        ],
        on_error=_handle_error,
    )

    chat.command("/help", lambda _: HELP_MESSAGE)
    chat.command("/today", lambda _: do_today())

    def _inbox(text: str) -> str:
        parts = text.split()
        count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
        return do_inbox(count=count)

    chat.command("/inbox", _inbox)

    def _search(text: str) -> str:
        query = text[7:].strip()
        if not query:
            return "Please provide a search query: `/search your query`"
        return do_search(query=query)

    chat.command("/search", _search)

    def _research(text: str) -> str:
        email = text[9:].strip()
        if not email:
            return "Please provide an email: `/research alice@acme.com`"
        return do_research(email)

    chat.command("/research", _research)

    def _voice(text: str) -> str:
        args = text[6:].strip()
        if not args:
            return "Please provide an audio file: `/voice memo.mp3`"
        parts = args.split("--to")
        audio_file = parts[0].strip()
        recipient = parts[1].strip() if len(parts) > 1 else ""
        return do_voice(audio_file, recipient)

    chat.command("/voice", _voice)

    chat.command("/contacts", lambda _: do_contacts())
    chat.command("/init-crm", lambda _: do_init_crm())
    chat.command("/relationships", lambda _: do_relationships())
    chat.command("/weekly", lambda _: do_weekly())

    def _show(text: str) -> str:
        email_id = text[5:].strip()
        if not email_id:
            return "Please provide an email ID: `/show <id>`"
        return do_show(email_id)

    chat.command("/show", _show)

    def _archive(text: str) -> str:
        email_id = text[8:].strip()
        if not email_id:
            return "Please provide an email ID: `/archive <id>`"
        return do_archive(email_id)

    chat.command("/archive", _archive)

    def _star(text: str) -> str:
        email_id = text[5:].strip()
        if not email_id:
            return "Please provide an email ID: `/star <id>`"
        return do_star(email_id)

    chat.command("/star", _star)

    def _mark_read(text: str) -> str:
        email_id = text[10:].strip()
        if not email_id:
            return "Please provide an email ID: `/mark-read <id>`"
        return do_mark_read(email_id)

    chat.command("/mark-read", _mark_read)

    def _calendar(text: str) -> str:
        parts = text.split()
        days = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 7
        return do_calendar(days=days)

    chat.command("/calendar", _calendar)

    chat.command("/free", lambda _: do_free())

    def _link_gmail(_: str) -> str:
        subprocess.run(["co", "auth", "google"], timeout=SUBPROCESS_TIMEOUT)
        set_env_flag("LINKED_GMAIL", "true")
        return "Gmail connected. Restart the CLI to use it."

    chat.command("/link-gmail", _link_gmail)

    chat.run()
