"""Approval workflow plugin - requires confirmation before sending emails."""

import sys
from pathlib import Path

from connectonion import before_each_tool
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MAX_BODY_PREVIEW_LENGTH
from utils import safe_truncate

console = Console()


def require_send_approval(agent):
    """Handler that requires user confirmation before sending emails.

    Per ConnectOnion docs, event handlers receive only 'agent' parameter.
    Access pending tool via agent.current_session.get("pending_tool").
    """
    pending = agent.current_session.get("pending_tool", {})
    tool_name = pending.get("name", "")
    args = pending.get("args", {})

    if tool_name in ["send_email", "reply_to_email", "Gmail.send_email", "Gmail.reply_to_email"]:
        # Format email preview
        to = args.get("to", "Unknown")
        subject = args.get("subject", "No subject")
        body = args.get("body", args.get("message", ""))

        # Truncate body for preview
        body_preview = safe_truncate(body, MAX_BODY_PREVIEW_LENGTH)

        # Show preview panel
        console.print()
        console.print(
            Panel(
                f"**To:** {to}\n**Subject:** {subject}\n\n{body_preview}",
                title=f"📧 Confirm {tool_name}",
                border_style="yellow",
            )
        )

        # Ask for confirmation
        confirmed = Confirm.ask("Send this email?", default=False)

        if not confirmed:
            raise RuntimeError("Email cancelled by user")


# Export as plugin
approval_workflow = [before_each_tool(require_send_approval)]
