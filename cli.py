"""
Email Agent CLI - Interactive email management from your terminal

Usage:
    python cli.py              # Interactive mode (default)
    python cli.py inbox        # Show recent emails
    python cli.py today        # Daily briefing
    python cli.py research x   # Research a contact
    python cli.py --help       # All commands
"""

from dotenv import load_dotenv

load_dotenv()

from cli.commands import app

if __name__ == "__main__":
    app()
