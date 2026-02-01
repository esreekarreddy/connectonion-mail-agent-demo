"""Typer CLI commands for Email Agent."""

import sys
import typer
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DEFAULT_CRM_MAX_EMAILS, DEFAULT_CRM_TOP_N

from .core import (
    do_inbox,
    do_search,
    do_today,
    do_chat,
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
from .setup import check_setup

app = typer.Typer(
    name="email-agent",
    help="AI-powered email assistant with contact intelligence.",
    add_completion=False,
)

console = Console()


def _print(result: str):
    console.print(Markdown(result))


@app.command()
def inbox(
    count: int = typer.Option(10, "--count", "-n", help="Number of emails"),
    unread: bool = typer.Option(False, "--unread", "-u", help="Only unread"),
):
    check_setup()
    _print(do_inbox(count=count, unread=unread))


@app.command()
def search(
    query: str = typer.Argument(..., help="Gmail search query"),
    count: int = typer.Option(10, "--count", "-n", help="Max results"),
):
    check_setup()
    _print(do_search(query=query, count=count))


@app.command()
def today():
    check_setup()
    _print(do_today())


@app.command()
def chat(message: str = typer.Argument(..., help="Message for the agent")):
    check_setup()
    _print(do_chat(message))


@app.command()
def research(email: str = typer.Argument(..., help="Email to research")):
    """Research a contact before emailing them."""
    check_setup()
    _print(do_research(email))


@app.command()
def voice(
    audio_file: str = typer.Argument(..., help="Path to audio file (MP3, WAV, etc.)"),
    recipient: str = typer.Option("", "--to", "-t", help="Recipient email hint"),
):
    """Dictate an email via voice memo."""
    check_setup()
    _print(do_voice(audio_file, recipient=recipient))


@app.command("init-crm")
def init_crm(
    max_emails: int = typer.Option(DEFAULT_CRM_MAX_EMAILS, help="Emails to scan"),
    top_n: int = typer.Option(DEFAULT_CRM_TOP_N, help="Top contacts to analyze"),
):
    check_setup()
    _print(do_init_crm(max_emails=max_emails, top_n=top_n))


@app.command()
def contacts():
    check_setup()
    _print(do_contacts())


@app.command()
def show(email_id: str = typer.Argument(..., help="Email ID")):
    check_setup()
    _print(do_show(email_id))


@app.command()
def archive(email_id: str = typer.Argument(..., help="Email ID")):
    check_setup()
    _print(do_archive(email_id))


@app.command()
def star(email_id: str = typer.Argument(..., help="Email ID")):
    check_setup()
    _print(do_star(email_id))


@app.command("mark-read")
def mark_read(email_id: str = typer.Argument(..., help="Email ID")):
    check_setup()
    _print(do_mark_read(email_id))


@app.command()
def calendar(days: int = typer.Option(7, help="Days ahead")):
    check_setup()
    _print(do_calendar(days=days))


@app.command()
def free(
    date: str = typer.Option("", help="Date (YYYY-MM-DD)"),
    duration: int = typer.Option(30, help="Duration in minutes"),
):
    check_setup()
    _print(do_free(date=date, duration=duration))


@app.command()
def relationships():
    """Show relationship health dashboard."""
    check_setup()
    _print(do_relationships())


@app.command()
def weekly():
    """Weekly email analytics with AI recommendations."""
    check_setup()
    _print(do_weekly())


@app.command()
def interactive():
    """Start interactive chat mode."""
    from .interactive import start_interactive

    check_setup()
    start_interactive()


if __name__ == "__main__":
    app()
