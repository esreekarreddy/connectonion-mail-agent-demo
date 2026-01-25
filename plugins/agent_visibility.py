"""Agent visibility plugin - shows workflow summaries after tasks."""

from connectonion import on_complete
from rich.console import Console
from rich.panel import Panel
from time import time

console = Console()


def show_workflow_summary(agent):
    """Display workflow summary after agent completes a task.

    Shows:
    - Total tool calls
    - Agent delegations (if any)
    - Total time
    - LLM reasoning steps
    """
    session = agent.current_session

    # Extract stats from session
    tool_calls = session.get("tool_call_count", 0)
    delegations = session.get("delegation_count", 0)
    start_time = session.get("start_time", 0)
    end_time = session.get("end_time", time())

    # Calculate duration
    if start_time and end_time:
        duration_ms = int((end_time - start_time) * 1000)
    else:
        duration_ms = 0

    # Build summary
    summary = []
    if tool_calls > 0:
        summary.append(f"🔧 {tool_calls} tool calls")
    if delegations > 0:
        summary.append(f"🤖 {delegations} agent delegations")
    if duration_ms > 0:
        summary.append(f"⏱️ {duration_ms}ms")

    if summary:
        console.print()
        console.print(Panel(" • ".join(summary), title="📊 Workflow Summary", border_style="cyan"))


# Export as plugin
agent_visibility_plugin = [on_complete(show_workflow_summary)]
