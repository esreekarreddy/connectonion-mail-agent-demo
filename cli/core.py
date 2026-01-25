"""Core CLI functions for Email Agent."""

from rich.console import Console

console = Console()


def _get_agent():
    from agent import get_agent

    return get_agent()


def _get_gmail():
    from agent import gmail

    return gmail


def _get_calendar():
    from agent import calendar

    return calendar


def do_inbox(count: int = 10, unread: bool = False) -> str:
    gmail = _get_gmail()
    if not gmail:
        return "Gmail not connected. Run 'co auth google' first."
    return gmail.read_inbox(last=count, unread=unread)


def do_search(query: str, count: int = 10) -> str:
    gmail = _get_gmail()
    if not gmail:
        return "Gmail not connected. Run 'co auth google' first."
    return gmail.search_emails(query=query, max_results=count)


def do_today() -> str:
    agent = _get_agent()
    return agent.input("What's on my plate today? Show unread emails and calendar events.")


def do_chat(message: str) -> str:
    agent = _get_agent()
    return agent.input(message)


def do_research(email: str) -> str:
    """Research a contact before emailing them using web scraping and AI analysis."""
    from agent import research_contact

    return research_contact(email)


def do_voice(audio_file: str, recipient: str = "") -> str:
    """Convert voice memo to email draft using transcription and AI."""
    from agent import voice_to_email

    return voice_to_email(audio_file, recipient_hint=recipient)


def do_init_crm(max_emails: int = 500, top_n: int = 10) -> str:
    from agent import init_crm_database

    return init_crm_database(max_emails=max_emails, top_n=top_n)


def do_contacts() -> str:
    from agent import memory

    result = memory.read_memory("crm:all_contacts")
    if not result or "not found" in str(result).lower():
        return "No contacts found. Run /init-crm first."
    return result


def do_show(email_id: str) -> str:
    gmail = _get_gmail()
    if not gmail:
        return "Gmail not connected."
    return gmail.get_email_body(email_id)


def do_archive(email_id: str) -> str:
    gmail = _get_gmail()
    if not gmail:
        return "Gmail not connected."
    return gmail.archive_email(email_id)


def do_star(email_id: str) -> str:
    gmail = _get_gmail()
    if not gmail:
        return "Gmail not connected."
    return gmail.star_email(email_id)


def do_mark_read(email_id: str) -> str:
    gmail = _get_gmail()
    if not gmail:
        return "Gmail not connected."
    return gmail.mark_read(email_id)


def do_calendar(days: int = 7) -> str:
    cal = _get_calendar()
    if not cal:
        return "Calendar not connected."
    return cal.list_events(days_ahead=days)


def do_free(date: str = "", duration: int = 30) -> str:
    cal = _get_calendar()
    if not cal:
        return "Calendar not connected."
    if not date:
        from datetime import datetime

        date = datetime.now().strftime("%Y-%m-%d")
    return cal.find_free_slots(date=date, duration_minutes=duration)


def do_relationships() -> str:
    """Analyze contact engagement and show health dashboard."""
    from datetime import datetime, timedelta
    import re
    from agent import memory, gmail, has_gmail

    try:
        memory_content = memory.list_memories()
    except Exception:
        memory_content = ""

    contacts = {}
    for line in str(memory_content).split("\n"):
        if "contact:" in line.lower():
            parts = line.split("|")
            if len(parts) >= 2:
                email_part = parts[0].lower().replace("contact:", "").strip()
                if "@" in email_part:
                    date_str = parts[1].strip()
                    try:
                        last_contact = datetime.fromisoformat(date_str)
                        contacts[email_part] = last_contact
                    except Exception:
                        pass

    if not contacts and has_gmail:
        try:
            recent = gmail.search_emails("in:sent OR in:inbox", max_results=50)
            for line in str(recent).split("\n"):
                if "from:" in line.lower() or "to:" in line.lower():
                    emails = re.findall(r"[\w\.-]+@[\w\.-]+", line)
                    for email in emails:
                        if email not in contacts:
                            contacts[email] = datetime.now() - timedelta(days=5)
        except Exception:
            pass

    if not contacts:
        return (
            "No contacts found. Send some emails first or run /init-crm to build contact database."
        )

    now = datetime.now()
    critical = []
    warning = []
    healthy = []

    for email, last_contact in contacts.items():
        days_ago = (now - last_contact).days
        if days_ago > 14:
            critical.append((email, days_ago))
        elif days_ago > 7:
            warning.append((email, days_ago))
        else:
            healthy.append((email, days_ago))

    # Return markdown instead of Rich table for TUI compatibility
    lines = ["## Relationship Health Dashboard\n"]

    if critical:
        lines.append("### Critical (>14 days)")
        for email, days in sorted(critical, key=lambda x: x[1], reverse=True):
            lines.append(f"- {email} ({days} days ago)")

    if warning:
        lines.append("\n### Warning (7-14 days)")
        for email, days in sorted(warning, key=lambda x: x[1], reverse=True):
            lines.append(f"- {email} ({days} days ago)")

    if healthy:
        lines.append("\n### Healthy (<7 days)")
        for email, days in sorted(healthy, key=lambda x: x[1]):
            lines.append(f"- {email} ({days} days ago)")

    lines.append(
        f"\n**Summary:** {len(critical)} critical, {len(warning)} warning, {len(healthy)} healthy"
    )

    return "\n".join(lines)


def do_weekly() -> str:
    """Generate weekly email analytics with AI-powered recommendations."""
    from datetime import datetime, timedelta
    import re
    from agent import gmail, has_gmail
    from connectonion import llm_do

    if not has_gmail:
        return "Gmail not connected. Run 'co auth google' first."

    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y/%m/%d")

    try:
        received = gmail.search_emails(query=f"after:{week_ago} -in:sent", max_results=100)
        sent = gmail.search_emails(query=f"after:{week_ago} in:sent", max_results=100)
        unread = gmail.search_emails(query="is:unread", max_results=50)

        # Count non-empty lines that look like email entries (contain @ or start with digit)
        def count_emails(output: str) -> int:
            lines = str(output).split("\n")
            return len(
                [
                    l
                    for l in lines
                    if l.strip() and ("@" in l or (l.strip() and l.strip()[0].isdigit()))
                ]
            )

        received_count = count_emails(received)
        sent_count = count_emails(sent)
        unread_count = count_emails(unread)

        stats = f"Last 7 days: {received_count} received, {sent_count} sent, {unread_count} unread"

        try:
            recommendation = llm_do(
                f"Email productivity analysis: {stats}. Provide a brief actionable recommendation (1 sentence).",
                model="co/gemini-2.5-flash",
            )
        except Exception:
            recommendation = (
                "Check your inbox regularly and respond to urgent emails within 24 hours."
            )

        # Return markdown for TUI compatibility
        return f"""## Weekly Email Analytics

| Metric | Value |
|--------|-------|
| Received | {received_count} |
| Sent | {sent_count} |
| Unread | {unread_count} |

**Recommendation:** {recommendation}
"""

    except Exception as e:
        return f"Error generating analytics: {e}"
