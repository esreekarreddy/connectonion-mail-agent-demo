# Complete Execution Flow Analysis - mailAgent

> **Command:** `python cli.py interactive`  
> **Purpose:** Detailed trace of every file, function, plugin, and model call

---

## 📋 Document Metadata

- **Version:** 1.0
- **Last Updated:** February 2026
- **Framework:** ConnectOnion v0.6.4
- **Project:** mailAgent (Enhanced Gmail Agent)

---

## 🎯 Intended Audience

This document is designed for:

- **New developers** joining the project who need to understand the architecture
- **Code reviewers** and interviewers evaluating the implementation
- **Future maintainers** who need to modify or extend features
- **Anyone learning** ConnectOnion framework patterns and best practices
- **Technical stakeholders** who want to understand system behavior

---

## ⚠️ Disclaimer

> **Note:** This document describes the intended architecture and execution flow based on the current implementation. While every effort has been made to ensure accuracy, some implementation details may vary slightly from the actual codebase due to:
> - Runtime conditional logic (e.g., authentication state, feature flags)
> - Dynamic model selection based on context
> - Future code changes that may shift line numbers or function signatures
>
> For the most current implementation details, always refer to the actual source code.

---

## 🚀 PART 1: INITIALIZATION FLOW

### Step 1: Command Entry
```bash
python cli.py interactive
```

### Step 2: File Loading Order

```
1. cli.py (entry point)
   ↓
2. Loads dotenv (environment variables from .env)
   ↓
3. Imports from cli.commands (app instance)
   ↓
4. cli/__init__.py (exports app)
   ↓
5. cli/commands.py (Typer app definition)
   ↓
6. When 'interactive' command called:
      → Imports from cli.interactive
      → Calls check_setup() from cli/setup.py
```

### Step 3: cli.py Execution (Lines 1-20)

```python
# cli.py
from dotenv import load_dotenv
load_dotenv()  # ← Loads .env file (GOOGLE_ACCESS_TOKEN, OPENONION_API_KEY, etc.)

from cli.commands import app  # ← Imports Typer app

if __name__ == "__main__":
    app()  # ← Typer takes over
```

**What happens:**
- `.env` loaded into environment
- `LINKED_GMAIL=true`, `GOOGLE_ACCESS_TOKEN`, etc. now available
- Typer CLI framework initializes

---

## 📋 PART 2: TYPER COMMAND ROUTING

### Step 4: cli/commands.py - Interactive Command (Lines 155-161)

```python
@app.command()
def interactive():
    """Start interactive chat mode."""
    from .interactive import start_interactive  # ← Lazy import
    
    check_setup()  # ← Validates auth first
    start_interactive()  # ← Launches TUI
```

### Step 5: check_setup() - Auth Validation

**File:** `cli/setup.py` (imports in commands.py line 25)

```python
def check_setup():
    # 1. Checks for OPENAI_API_KEY or OPENONION_API_KEY
    # 2. Checks LINKED_GMAIL or GOOGLE_ACCESS_TOKEN
    # 3. If missing, shows Rich error panel with instructions
    # 4. If present, returns silently
```

**Failure path:** Shows authentication error, exits  
**Success path:** Continues to TUI

---

## 🖥️ PART 3: TUI INITIALIZATION

### Step 6: cli/interactive.py - start_interactive() (Lines 141-256)

```python
def start_interactive():
    agent = _get_agent()  # ← CREATES AGENT (CRITICAL!)
    
    # Load contacts for @ autocomplete
    try:
        contact_provider = ContactProvider()  # ← cli/contacts_provider.py
        contacts = contact_provider.to_command_items()
    except Exception:
        contacts = []
    
    # Initialize ConnectOnion Chat TUI
    chat = Chat(
        agent=agent,  # ← The main agent instance
        title="Email Agent",
        triggers={
            "/": COMMANDS,  # ← Slash command autocomplete
            "@": contacts,  # ← Contact mention autocomplete
        },
        welcome=WELCOME,
        hints=["/ commands", "@ contacts", "Enter send", "Ctrl+D quit"],
        status_segments=[
            ("📧", "Email Agent", "cyan"),
            ("🤖", f"co/{agent.llm.model}", "magenta"),  # Shows model name
        ],
        on_error=_handle_error,
    )
    
    # Register all slash commands
    chat.command("/help", lambda _: HELP_MESSAGE)
    chat.command("/today", lambda _: do_today())
    chat.command("/inbox", _inbox)
    chat.command("/search", _search)
    chat.command("/research", _research)
    chat.command("/voice", _voice)
    chat.command("/contacts", lambda _: do_contacts())
    chat.command("/init-crm", lambda _: do_init_crm())
    chat.command("/relationships", lambda _: do_relationships())
    chat.command("/weekly", lambda _: do_weekly())
    # ... more commands
    
    chat.run()  # ← TUI event loop starts
```

---

## 🤖 PART 4: AGENT CREATION (THE HEART)

### Step 7: _get_agent() → agent.py get_agent() (Lines 255-269)

```python
def _get_agent():
    from agent import get_agent  # ← Imports from agent.py
    return get_agent()
```

### Step 8: agent.py - Agent Initialization (Lines 255-299)

```python
def get_agent():
    global _agent
    with _lock:  # ← Thread-safe singleton
        if _agent is None:
            from connectonion import Agent
            
            _agent = Agent(
                name="email-agent",
                system_prompt="prompts/agent.md",  # ← LOADS PROMPT
                tools=_build_tools(),              # ← BUILDS TOOLS
                plugins=_build_plugins(),          # ← BUILDS PLUGINS
                model="co/claude-opus-4-5",       # ← MODEL SET
                max_iterations=20,
            )
        return _agent
```

**FILES LOADED HERE:**
1. `prompts/agent.md` - System prompt (311 lines of instructions)
2. `_build_tools()` - All tools
3. `_build_plugins()` - All plugins

---

## 🔧 PART 5: TOOL BUILDING

### Step 9: _build_tools() (Lines 232-238)

```python
def _build_tools():
    tools = [memory, shell, todo, web, research_contact, voice_to_email]
    
    if gmail:  # ← Check if LINKED_GMAIL=true
        tools.insert(0, gmail)  # ← Gmail tool first
    if calendar:
        tools.insert(1 if gmail else 0, calendar)
    
    return tools
```

**Tools Created (in order):**

| Tool | Source | Purpose |
|------|--------|---------|
| `gmail` | `from connectonion import Gmail` | Gmail API wrapper |
| `calendar` | `from connectonion import GoogleCalendar` | Calendar API |
| `memory` | `Memory(memory_file="data/memory.md")` | Persistent storage |
| `shell` | `Shell()` | System commands |
| `todo` | `TodoList()` | Task tracking |
| `web` | `WebFetch()` | Web scraping |
| `research_contact` | Function (lines 52-109) | Contact intelligence |
| `voice_to_email` | Function (lines 127-224) | Voice transcription |
| `init_crm_database` | Function (lines 292-298) | CRM setup |

---

## 🔌 PART 6: PLUGIN BUILDING (PIPELINE)

### Step 10: _build_plugins() (Lines 241-252)

```python
def _build_plugins():
    from plugins import (
        approval_workflow,      # ← plugins/approval_workflow.py
        email_insights_plugin,  # ← plugins/email_insights.py
        agent_visibility_plugin # ← plugins/agent_visibility.py
    )
    
    plugins = [re_act]  # ← Built-in from connectonion.useful_plugins
    plugins.extend([
        approval_workflow,      # BEFORE each tool (approval)
        email_insights_plugin,  # AFTER tools (insights)
        agent_visibility_plugin # ON complete (summary)
    ])
    
    if gmail:
        plugins.append(gmail_plugin)      # ← Built-in
    if calendar:
        plugins.append(calendar_plugin)   # ← Built-in
    
    return plugins
```

### Plugin Execution Pipeline:

```
User Input
    ↓
┌─────────────────────────────────────────────────────────┐
│  PLUGIN: re_act (built-in)                              │
│  - Planning: "Will search for emails..."                 │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  PLUGIN: approval_workflow (before_each_tool)           │
│  - Checks if tool is send_email/reply_to_email          │
│  - If yes: Shows Rich panel preview                     │
│  - Asks: "Send this email? [y/N]"                       │
│  - If no: Raises RuntimeError (cancels)                 │
└─────────────────────────────────────────────────────────┘
    ↓
Tool Execution (e.g., gmail.read_inbox)
    ↓
┌─────────────────────────────────────────────────────────┐
│  PLUGIN: email_insights_plugin (after_tools)            │
│  - Analyzes last_result with llm_do()                   │
│  - Model: co/gemini-2.5-flash                           │
│  - Output: Priority emoji, sentiment, topics            │
│  - Shows: "🔴 URGENT | 😟 Negative | Topics: X, Y"       │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  PLUGIN: agent_visibility_plugin (on_complete)          │
│  - Shows: "🔧 5 tool calls • ⏱️ 2340ms"                  │
└─────────────────────────────────────────────────────────┘
    ↓
Response to User
```

---

## 📝 PART 7: SYSTEM PROMPT LOADING

### Step 11: prompts/agent.md (311 lines)

**Loaded at:** Agent initialization  
**Used by:** Main agent  
**Key sections:**

1. **CRITICAL RULE** (Line 7-9):
   ```
   RULE: NEVER ask questions before using tools. 
   ALWAYS use tools first to gather information, then propose.
   ```

2. **Tool Groups** (Lines 82-189):
   - Context First tools
   - Reading Emails tools
   - Calendar & Scheduling
   - Memory
   - Email Management
   - CRM & Contacts
   - Shell Commands

3. **Unique Capabilities** (Lines 45-78):
   - Contact Intelligence
   - Voice Email

---

## 🎮 PART 8: USER INPUT FLOW

### Scenario: User types `/today` in TUI

```
User types: /today
    ↓
TUI (connectonion.tui.Chat) matches "/" trigger
    ↓
Calls registered handler: chat.command("/today", lambda _: do_today())
    ↓
do_today() in cli/core.py (line 40-42)
```

### Step 12: cli/core.py - do_today() (Lines 40-42)

```python
def do_today() -> str:
    agent = _get_agent()
    return agent.input("What's on my plate today? Show unread emails and calendar events.")
```

**What happens:**
1. Gets agent instance (singleton)
2. Calls `agent.input()` with natural language
3. Agent processes using system prompt from prompts/agent.md

### Agent Processing Flow:

```
Agent receives: "What's on my plate today?"
    ↓
System prompt guides behavior (proactive, tools-first)
    ↓
Agent decides to call multiple tools:
    1. run("date") - Get current date
    2. get_today_events() - Calendar events
    3. count_unread() - Unread email count
    4. read_inbox(last=5, unread=True) - Recent unread
    ↓
Plugin Pipeline executes for each tool:
    - approval_workflow: Checks if send/reply (no, just reading)
    - email_insights: Analyzes email results
    ↓
Agent synthesizes all tool results
    ↓
Returns formatted response
    ↓
TUI displays to user
```

---

## 📊 PART 9: FEATURE-SPECIFIC FLOWS

### FEATURE 1: `/relationships` (Relationship Health)

**Flow:**
```
User: /relationships
    ↓
chat.command("/relationships", lambda _: do_relationships())
    ↓
cli/core.py do_relationships() (lines 125-203)
    ↓
1. memory.list_memories() - Gets all memory keys
2. Parses contact: entries with dates
3. If no contacts in memory:
   → gmail.search_emails("in:sent OR in:inbox", 50)
   → Extracts email addresses
   → Defaults to "5 days ago"
    ↓
4. Calculates days since last contact
5. Categorizes:
   - Critical: >14 days
   - Warning: 7-14 days
   - Healthy: <7 days
    ↓
6. Returns markdown table
    ↓
TUI displays
```

**Model used:** None (pure Python logic)  
**Data source:** `data/memory.md` or Gmail API

---

### FEATURE 2: `/weekly` (Weekly Analytics)

**Flow:**
```
User: /weekly
    ↓
do_weekly() in cli/core.py (lines 206-263)
    ↓
1. Calculate week_ago date
2. Gmail API calls:
   - search_emails(after:week_ago -in:sent)  # Received
   - search_emails(after:week_ago in:sent)   # Sent
   - search_emails(is:unread)                 # Unread
    ↓
3. count_emails() - Line-based counting heuristic
    ↓
4. llm_do() for AI recommendation
   Model: co/gemini-2.5-flash
   Prompt: "Email productivity analysis: {stats}. Provide brief actionable recommendation."
    ↓
5. Returns markdown with stats + AI recommendation
    ↓
TUI displays
```

**Models used:**
- `co/gemini-2.5-flash` - For AI recommendation

---

### FEATURE 3: `/research <email>` (Contact Intelligence)

**Flow:**
```
User: /research alice@stripe.com
    ↓
do_research() in cli/core.py (line 50-54)
    ↓
research_contact() in agent.py (lines 52-109)
    ↓
1. Extract domain: stripe.com
2. Check if personal (gmail, yahoo, etc.)
   → If personal: return early
    ↓
3. web.fetch(f"https://{domain}")
   → Fetches company homepage HTML
    ↓
4. web.get_social_links(url)
   → Extracts LinkedIn, Twitter, etc.
    ↓
5. llm_do() with Pydantic structured output
   Model: co/claude-opus-4-5 (inherited from agent)
   Output: ContactIntel Pydantic model
   - company: str
   - role_guess: Optional[str]
   - industry: str
   - talking_points: List[str]
   - tone_suggestion: str
   - recent_news: Optional[str]
    ↓
6. Formats result as markdown
    ↓
7. memory.write_memory(f"contact:{email}", result)
   → Saves to data/memory.md
    ↓
8. Returns formatted intelligence
    ↓
TUI displays
```

**Models used:**
- `co/claude-opus-4-5` - For company analysis (structured output)

**APIs used:**
- `WebFetch().fetch()` - Website scraping
- `WebFetch().get_social_links()` - Social link extraction
- `Memory.write_memory()` - Persistent storage

---

### FEATURE 4: `/voice <file>` (Voice Email)

**Flow:**
```
User: /voice memo.mp3 --to bob@acme.com
    ↓
do_voice() in cli/core.py (lines 57-61)
    ↓
voice_to_email() in agent.py (lines 127-224)
    ↓
1. Validate file exists
2. Validate format (WAV, MP3, AIFF, AAC, OGG, FLAC, M4A)
    ↓
3. transcribe(audio=file, prompt="Email dictation...")
   → Model: Gemini (built into connectonion.transcribe)
   → Returns: Text transcription
    ↓
4. llm_do() - Extract intent
   Model: co/claude-opus-4-5
   Output: EmailIntent Pydantic model
   - recipient: Optional[str]
   - subject_hint: str
   - key_points: List[str]
   - tone: str
   - action: str
    ↓
5. If recipient is corporate email:
   → Calls research_contact(recipient)
   → Gets company intelligence
    ↓
6. llm_do() - Draft email
   Model: co/claude-opus-4-5
   Output: EmailDraft Pydantic model
   - to: str
   - subject: str
   - body: str
   - needs_research: bool
    ↓
7. Formats result with:
   - Transcription
   - Draft email
   - Action options (send/edit/research/cancel)
    ↓
8. memory.write_memory("voice_email:latest", result)
    ↓
9. Returns formatted result
    ↓
TUI displays
```

**Models used:**
- `Gemini` (via transcribe()) - Audio transcription
- `co/claude-opus-4-5` - Intent extraction
- `co/claude-opus-4-5` - Email drafting

**Note:** If user then says "send", the approval_workflow plugin intercepts and confirms.

---

### FEATURE 5: `/init-crm` (CRM Initialization)

**Flow:**
```
User: /init-crm
    ↓
do_init_crm() in cli/core.py (lines 64-67)
    ↓
init_crm_database() in agent.py (lines 292-298)
    ↓
1. Check if Gmail connected
    ↓
2. _get_init_crm_agent() (lines 272-289)
   → Creates SUB-AGENT with:
      - name="crm-init"
      - system_prompt="prompts/crm_init.md"
      - max_iterations=30 (more than main agent)
      - model="co/claude-opus-4-5"
      - log=False
    ↓
3. Sub-agent executes:
   agent.input("Initialize CRM: Extract top 10 contacts from 500 emails")
    ↓
4. Sub-agent calls tools:
   - gmail.get_all_contacts(max_emails=500)
   - Analyzes each contact with web research
   - Categorizes by relationship type
   - write_memory("crm:all_contacts", summary)
   - write_memory("contact:email@example.com", details)
    ↓
5. Returns summary
    ↓
TUI displays: "CRM initialized. Use /contacts to view."
```

**Models used:**
- `co/claude-opus-4-5` (sub-agent) - Contact analysis

**Why sub-agent:**
- Complex task needs more iterations (30 vs 20)
- Specialized prompt for CRM extraction
- Don't clutter main agent logs

---

### FEATURE 6: `/contacts` (View Contacts)

**Flow:**
```
User: /contacts
    ↓
do_contacts() in cli/core.py (lines 70-76)
    ↓
1. memory.read_memory("crm:all_contacts")
    ↓
2. If not found:
   → Return "No contacts found. Run /init-crm first."
    ↓
3. Returns saved contact list
    ↓
TUI displays
```

**Data source:** `data/memory.md` (written by /init-crm)

---

### FEATURE 7: `/calendar` (Calendar Events)

**Flow:**
```
User: /calendar
    ↓
do_calendar() in cli/core.py (lines 107-111)
    ↓
1. Check if calendar connected
    ↓
2. calendar.list_events(days_ahead=7)
   → Google Calendar API call
    ↓
3. Returns formatted events
    ↓
TUI displays
```

**Tool used:** `GoogleCalendar.list_events()` from connectonion

---

### FEATURE 8: `/free` (Find Free Slots)

**Flow:**
```
User: /free
    ↓
do_free() in cli/core.py (lines 114-122)
    ↓
1. Check if calendar connected
    ↓
2. If no date provided:
   → date = datetime.now().strftime("%Y-%m-%d")
    ↓
3. calendar.find_free_slots(date=date, duration_minutes=30)
   → Google Calendar API call
    ↓
4. Returns available time slots
    ↓
TUI displays
```

**Tool used:** `GoogleCalendar.find_free_slots()` from connectonion

---

### FEATURE 9: Email Operations (inbox, search, show, archive, star)

**Flow (all similar):**
```
User: /inbox 20
    ↓
do_inbox(count=20) in cli/core.py (lines 26-30)
    ↓
1. Check if Gmail connected
    ↓
2. gmail.read_inbox(last=20, unread=False)
   → Gmail API call
    ↓
3. Plugin: email_insights analyzes result
   → If contains "read" or "inbox" in tool name
   → Calls llm_do() with co/gemini-2.5-flash
   → Adds priority/sentiment annotations
    ↓
4. Returns formatted emails
    ↓
TUI displays
```

**Tools used:**
- `Gmail.read_inbox()`
- `Gmail.search_emails()`
- `Gmail.get_email_body()`
- `Gmail.archive_email()`
- `Gmail.star_email()`
- `Gmail.mark_read()`

**Plugins invoked:**
- `email_insights` (after_tools) - Only for read operations

---

## 🤖 PART 10: MODEL USAGE SUMMARY

| Feature | Model | Purpose |
|---------|-------|---------|
| **Main Agent** | `co/claude-opus-4-5` | General reasoning, tool selection |
| **Email Insights** | `co/gemini-2.5-flash` | Priority/sentiment analysis (fast) |
| **Weekly Analytics** | `co/gemini-2.5-flash` | Recommendation generation |
| **Contact Research** | `co/claude-opus-4-5` | Company analysis (structured output) |
| **Voice Intent** | `co/claude-opus-4-5` | Extract intent from transcription |
| **Voice Drafting** | `co/claude-opus-4-5` | Draft email from voice memo |
| **CRM Init** | `co/claude-opus-4-5` | Contact categorization (sub-agent) |
| **Transcription** | `Gemini` (built-in) | Audio to text (via transcribe()) |

---

## 📁 PART 11: COMPLETE FILE LOAD ORDER

### When you run `python cli.py interactive`:

```
1. Python interpreter starts
   ↓
2. cli.py loads
   - dotenv.load_dotenv() → .env file
   - Imports cli.commands.app
   ↓
3. cli/__init__.py loads
   - Exports app
   ↓
4. cli/commands.py loads
   - Imports typer, rich
   - Imports all do_* functions from cli/core
   - Imports check_setup from cli/setup
   - Defines all @app.command() decorators
   ↓
5. cli/core.py loads
   - Imports agent.py components
   ↓
6. agent.py loads (CRITICAL)
   - Imports from connectonion:
     * Agent, Memory, WebFetch, Shell, TodoList
     * llm_do, transcribe
     * re_act, gmail_plugin, calendar_plugin
   - Creates global instances:
     * memory = Memory(memory_file="data/memory.md")
     * web = WebFetch()
     * shell = Shell()
     * todo = TodoList()
   - Checks .env for LINKED_GMAIL
   - Conditionally imports Gmail, GoogleCalendar
   - Defines Pydantic models: ContactIntel, EmailIntent, EmailDraft
   - Defines functions: research_contact(), voice_to_email()
   - Defines get_agent(), _get_init_crm_agent()
   ↓
7. plugins load (when get_agent() called)
   - plugins/approval_workflow.py
   - plugins/email_insights.py
   - plugins/agent_visibility.py
   ↓
8. prompts/agent.md loads
   - System prompt for main agent
   ↓
9. cli/interactive.py loads (when interactive command called)
   - Imports Chat, CommandItem from connectonion.tui
   - Imports ContactProvider from cli/contacts_provider
   - Imports all do_* functions from cli/core
   ↓
10. cli/contacts_provider.py loads
    - Reads data/contacts.csv
    - Provides fuzzy search for @ autocomplete
    ↓
11. cli/setup.py loads
    - Validates OPENAI_API_KEY or OPENONION_API_KEY
    - Validates LINKED_GMAIL or GOOGLE_ACCESS_TOKEN
    ↓
12. TUI initializes (connectonion.tui.Chat)
    - Creates terminal UI
    - Sets up autocomplete triggers (/ and @)
    - Registers all command handlers
    ↓
13. chat.run() starts
    - Event loop begins
    - Waits for user input
```

---

## 🔄 PART 12: PLUGIN PIPELINE DETAIL

### Event Execution Order:

```python
# For EVERY user input:

1. after_user_input
   └─ Can modify messages before LLM sees them
   
2. before_llm
   └─ Can log or modify before LLM call
   
3. LLM Call (to model, e.g., co/claude-opus-4-5)
   └─ Returns tool decisions
   
4. after_llm
   └─ Can see what tools LLM decided to call
   
5. before_tools
   └─ Fires ONCE before all tools in batch
   
6. LOOP: For EACH tool:
    
    a. before_each_tool
       └─ approval_workflow runs here
       └─ Can cancel execution by raising exception
    
    b. Tool Execution (e.g., gmail.read_inbox)
       └─ Actual API call to Gmail
    
    c. after_each_tool
       └─ Logging only! (Don't add messages here)
       └─ Breaks Claude's message ordering if you do

7. after_tools
   └─ email_insights runs here
   └─ SAFE to add messages/reflections
   
8. (Loop back to 2 if more LLM calls needed)
   
9. on_error (only if error occurred)
   └─ Handle exceptions
   
10. on_complete
    └─ agent_visibility runs here
    └─ Show summary: "🔧 5 tool calls • ⏱️ 2340ms"
```

### Your 3 Custom Plugins:

```python
# 1. approval_workflow (before_each_tool)
def require_send_approval(agent):
    pending = agent.current_session.get("pending_tool", {})
    if pending.get("name") in ["send_email", "reply_to_email", ...]:
        # Show Rich panel with email preview
        # Ask Confirm.ask("Send this email?", default=False)
        # If not confirmed: raise RuntimeError("Email cancelled")

# 2. email_insights (after_tools)
def add_email_insights(agent):
    last_tool = agent.current_session.get("last_tool", {})
    if "read" in last_tool.get("name", "").lower():
        # llm_do() with co/gemini-2.5-flash
        # Analyze priority, sentiment, topics
        # Display with emojis: 🔴 URGENT | 😟 Negative

# 3. agent_visibility (on_complete)
def show_workflow_summary(agent):
    # Count tool_calls, delegations, duration
    # Show: "🔧 5 tool calls • ⏱️ 2340ms"
```

---

## 💾 PART 13: DATA FLOW

### Persistent Storage:

| File | Purpose | Written By | Read By |
|------|---------|------------|---------|
| `.env` | API keys, tokens | `co auth` | All modules |
| `data/memory.md` | Contact intel, drafts | `memory.write_memory()` | `memory.read_memory()` |
| `data/contacts.csv` | CRM contact database | CRM init sub-agent | ContactProvider (@ autocomplete) |
| `data/emails.csv` | Cached emails | Gmail API | (Not directly used) |

### Memory Keys Used:

```
contact:{email}          → Contact intelligence results
crm:all_contacts         → List of all contacts
crm:needs_reply          → Unanswered emails
voice_email:latest       → Latest voice email draft
voice_email:draft        → Draft content for sending
```

---

## 🎯 PART 14: COMBINATION SCENARIOS

### Scenario A: Natural Language Chat

**User types:** "What's my schedule today?"

```
Flow:
1. TUI receives text (no / prefix)
2. Goes to default agent.input()
3. Agent sees system prompt
4. Decides to call:
   - run("date")
   - get_today_events()
   - count_unread()
   - read_inbox(last=5)
5. Plugins execute for each tool
6. Agent synthesizes response
7. TUI displays natural language answer
```

### Scenario B: Research → Draft Email

**User:**
1. `/research ceo@stripe.com`
2. `/today` (sees they need to email)
3. "Draft an email to the Stripe CEO about partnership"

```
Flow:
1. research_contact() saves to memory as "contact:ceo@stripe.com"
2. Agent reads memory for contact context
3. Uses research data to personalize draft
4. approval_workflow will intercept when sending
```

### Scenario C: Voice → Edit → Send

**User:**
1. `/voice memo.mp3 --to bob@acme.com`
2. Agent transcribes and drafts
3. User says: "Change the subject to 'Q4 Update'"
4. User says: "Send it"

```
Flow:
1. transcribe() → Gemini → Text
2. llm_do() → Extract intent → EmailIntent
3. research_contact() → If corporate domain
4. llm_do() → Draft email → EmailDraft
5. User edits (natural language chat)
6. When send triggered:
   approval_workflow intercepts
   Shows Rich preview panel
   Asks for confirmation
7. If confirmed: Gmail.send_email() executes
```

---

## ⚡ PART 15: PERFORMANCE NOTES

### Thread Safety:
- `get_agent()` uses `threading.Lock()` for singleton
- Safe for multiple threads to call
- Agent itself is single-threaded per session

### API Calls:
- Gmail API: Called directly (real-time)
- Calendar API: Called directly (real-time)
- WebFetch: HTTP requests (synchronous)
- LLM calls: Via connectonion (co/ prefix uses managed keys)

### Caching:
- Memory tool: Writes to disk (data/memory.md)
- Contacts CSV: Read once at TUI startup
- No in-memory caching beyond agent session

---

## 📚 SUMMARY

### Entry Point to Display:

```
python cli.py interactive
    ↓
cli.py (load .env)
    ↓
cli/commands.py (Typer routing)
    ↓
interactive command
    ↓
check_setup() (auth validation)
    ↓
start_interactive()
    ↓
_get_agent() → agent.py
    ↓
Build tools + plugins + load prompt
    ↓
Chat TUI initializes
    ↓
User types command
    ↓
Handler calls cli/core.py function
    ↓
Function calls agent.input() OR direct Gmail API
    ↓
Plugins execute in pipeline
    ↓
Result displayed in TUI
```

### Key Takeaways:

1. **cli.py is just entry** - delegates to Typer
2. **commands.py routes** - defines all CLI commands
3. **interactive.py runs TUI** - uses connectonion.tui.Chat
4. **core.py does work** - all business logic functions
5. **agent.py creates agent** - singleton with tools + plugins
6. **plugins intercept** - before/after tool execution
7. **prompts guide behavior** - system prompt = agent personality
8. **data/ stores state** - memory, contacts, emails

---

**End of Execution Flow Analysis**
