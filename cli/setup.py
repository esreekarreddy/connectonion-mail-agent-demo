"""Setup and auth checks for Email Agent CLI."""

import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


def check_setup(skip_init: bool = False) -> bool:
    """Check auth and CRM setup. Returns True if ready to proceed."""
    has_llm_key = any(
        [
            os.getenv("OPENAI_API_KEY"),
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("GEMINI_API_KEY"),
            os.getenv("OPENONION_API_KEY"),
        ]
    )
    has_google_token = os.getenv("GOOGLE_ACCESS_TOKEN")

    if not has_llm_key or not has_google_token:
        console.print(
            Panel(
                "[bold red]Authentication Required[/bold red]\n\n"
                "You need to authenticate first.\n"
                "This will open a browser to grant permissions.",
                title="[bold]Setup Required[/bold]",
                border_style="red",
                padding=(1, 2),
            )
        )

        from connectonion import pick, Shell, Agent

        choice = pick(
            "Run authentication now?", ["Yes, run authentication", "No, I'll do it manually"]
        )

        if "Yes" in choice:
            console.print("\n[dim]Running authentication...[/dim]\n")
            shell = Shell()
            auth_agent = Agent("auth-helper", tools=[shell], log=False)
            auth_agent.input("Run these commands: co auth, then co auth google")
            _set_env_flag("LINKED_GMAIL", "true")
            console.print("\n[green]Please restart the CLI.[/green]\n")
        else:
            console.print(
                Panel(
                    "[bold yellow]Manual Setup Required[/bold yellow]\n\n"
                    "[bold]Please run these commands:[/bold]\n\n"
                    "1. [cyan]co auth[/cyan]          (authenticate LLM provider)\n"
                    "2. [cyan]co auth google[/cyan]   (authenticate Google Gmail)\n\n"
                    "Then restart this CLI.",
                    border_style="yellow",
                    padding=(1, 2),
                )
            )
        return False

    if not skip_init:
        contacts_path = Path("data/contacts.csv")
        needs_init = not contacts_path.exists() or contacts_path.stat().st_size < 100

        if needs_init:
            console.print(
                Panel(
                    "[bold yellow]CRM Not Initialized[/bold yellow]\n\n"
                    "Initialize the CRM to:\n"
                    "  - Extract contacts from emails\n"
                    "  - Categorize people, services, notifications\n"
                    "  - Set up your contact database\n\n"
                    "[dim]Takes 2-3 minutes, only needs to run once.[/dim]",
                    title="[bold]First Time Setup[/bold]",
                    border_style="yellow",
                    padding=(1, 2),
                )
            )

            from connectonion import pick

            choice = pick(
                "Initialize CRM now?",
                ["Yes, initialize now", "Skip, I'll do it later with /init-crm"],
            )

            if "Yes" in choice:
                console.print("\n[dim]Starting CRM initialization...[/dim]\n")
                from .core import do_init_crm

                with console.status("[bold blue]Processing...[/bold blue]"):
                    result = do_init_crm()
                console.print(
                    Panel(
                        Markdown(result),
                        title="[bold green]Done[/bold green]",
                        border_style="green",
                    )
                )

    return True


def _set_env_flag(key: str, value: str):
    env_path = Path(".env")
    lines = []
    if env_path.exists():
        lines = env_path.read_text().splitlines()

    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            found = True
            break

    if not found:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n")
