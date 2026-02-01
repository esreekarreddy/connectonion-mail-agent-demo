# Changelog

All notable changes to the Email Agent project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **tests/test_config.py** - Comprehensive test suite for config.py (74 tests)
  - Tests all default configuration values
  - Tests all 18 environment variable overrides
  - Tests type consistency and value relationships
  - Tests edge cases and collection contents

- **tests/test_utils.py** - Comprehensive test suite for utils.py (100+ tests)
  - Tests email validation (valid, invalid, edge cases)
  - Tests personal email detection
  - Tests SSRF domain safety validation
  - Tests domain extraction
  - Tests memory line parsing
  - Tests retry with backoff behavior
  - Tests set_env_flag functionality
  - Integration tests combining multiple functions

- **agent.py: reset_agent()** - Testing utility function to reset singleton for test isolation

- **Docstrings** - Added comprehensive docstrings to helper functions:
  - agent.py: `_build_tools()`, `_build_plugins()`, `get_agent()`, `_get_init_crm_agent()`
  - cli/core.py: `_get_agent()`, `_get_gmail()`, `_get_calendar()`

- **config.py** - Centralized configuration module with 30+ constants
  - LLM models: `DEFAULT_MODEL`, `FAST_MODEL`
  - Agent settings: `MAX_ITERATIONS_MAIN`, `MAX_ITERATIONS_CRM`
  - Security: `BLOCKED_DOMAIN_PATTERNS` for SSRF protection
  - Content limits: `MAX_PAGE_CONTENT_LENGTH`, `MAX_EMAIL_PREVIEW_LENGTH`, `MAX_BODY_PREVIEW_LENGTH`
  - Relationship thresholds: `RELATIONSHIP_CRITICAL_DAYS`, `RELATIONSHIP_WARNING_DAYS`
  - CRM defaults: `DEFAULT_CRM_MAX_EMAILS`, `DEFAULT_CRM_TOP_N`
  - Gmail: `DEFAULT_GMAIL_SEARCH_LIMIT`
  - Display: `MAX_TOPICS_DISPLAY`
  - Timeouts: `SUBPROCESS_TIMEOUT`, `LLM_RETRY_ATTEMPTS`, `LLM_RETRY_DELAY`
  - File limits: `MAX_AUDIO_FILE_SIZE_MB`, `SUPPORTED_AUDIO_FORMATS`
  - Paths: `DATA_DIR`, `MEMORY_FILE`, `CONTACTS_FILE`, `ENV_FILE`
  - Cache: `INSIGHTS_CACHE_TTL_SECONDS`
  - All configurable via environment variables

- **utils.py** - Shared utilities module
  - `is_valid_email()` - RFC 5322 email validation
  - `is_personal_email()` - Check against personal domain list
  - `is_safe_domain()` - SSRF protection (blocks internal IPs, localhost, private ranges)
  - `extract_domain()` - Safe domain extraction from email
  - `set_env_flag()` - Thread-safe .env writing with fcntl file locking
  - `retry_with_backoff()` - Exponential backoff retry for LLM calls
  - `safe_truncate()` - Safe text truncation with configurable suffix
  - `parse_memory_line()` - Robust memory parsing (handles `|` in notes)

- **EXECUTION_FLOW.md** - Comprehensive technical architecture documentation (800+ lines)

### Changed
- **agent.py**
  - Implemented memory-first pattern in `research_contact()` - checks cache before expensive API calls
  - Implemented memory-first pattern in `init_crm_database()` - skips if CRM already initialized
  - Added SSRF protection with `is_safe_domain()` validation before web fetches
  - Added audio file size validation (`MAX_AUDIO_FILE_SIZE_BYTES`)
  - Replaced hardcoded model names with config constants
  - Replaced hardcoded iterations with config constants
  - Added logging for silent exception handlers
  - Wrapped all `llm_do` calls with `retry_with_backoff()`
  - Using `safe_truncate()` for page content

- **cli/interactive.py**
  - Replaced duplicate `_set_env_flag()` with shared `set_env_flag()` from utils
  - Added subprocess timeout for `co auth google` command
  - Added logging for exception handlers

- **cli/setup.py**
  - Replaced duplicate `_set_env_flag()` with shared `set_env_flag()` from utils

- **cli/core.py**
  - Using `parse_memory_line()` for robust memory parsing
  - Using config constants for relationship thresholds
  - Using `FAST_MODEL` instead of hardcoded model string
  - Using `DEFAULT_GMAIL_SEARCH_LIMIT` instead of hardcoded 50
  - Wrapped `llm_do` calls with `retry_with_backoff()`
  - Added logging for all silent exception handlers

- **cli/commands.py**
  - Using `DEFAULT_CRM_MAX_EMAILS` and `DEFAULT_CRM_TOP_N` from config

- **cli/contacts_provider.py**
  - Using `CONTACTS_FILE` from config instead of hardcoded path

- **plugins/email_insights.py**
  - Complete rewrite with TTL-based caching
  - Using config constants for cache TTL and model
  - Using `retry_with_backoff()` for LLM calls
  - Using `MAX_TOPICS_DISPLAY` instead of hardcoded 3
  - Added proper logging instead of silent failures

- **plugins/approval_workflow.py**
  - Using `safe_truncate()` with `MAX_BODY_PREVIEW_LENGTH` from config

- **prompts/agent.md**
  - Added explicit Memory-First Pattern section
  - Reordered efficiency rules: Memory #1, Research #2

### Security
- **SSRF Protection** - Added domain validation to prevent Server-Side Request Forgery attacks
  - Blocks internal IPs (127.x, 10.x, 172.16-31.x, 192.168.x)
  - Blocks localhost and private domains (.local, .internal, .corp, .lan)
  - Blocks AWS metadata endpoint (169.254.x)

- **Thread-Safe .env Writing** - Using fcntl file locking to prevent race conditions

- **Input Validation** - Added RFC 5322 email validation

### Fixed
- Fixed wrong model name `co/claude-sonnet-4-5` -> `co/claude-opus-4-5`
- Fixed fragile memory parsing that broke with `|` characters in notes
- Fixed silent exception handlers that made debugging impossible
- Fixed code duplication across CLI modules
- Fixed hardcoded values scattered across codebase

### Performance
- Memory-first pattern reduces redundant API calls
- Email insights caching with configurable TTL
- Exponential backoff retry prevents wasted retries

## [0.1.0] - 2026-01-25

### Added
- Initial release with ConnectOnion framework integration
- Contact Intelligence feature - research contacts via web scraping
- Voice Email feature - dictate emails via audio transcription
- Relationship Health Dashboard
- Weekly Email Analytics
- Gmail and Calendar integration
- Interactive TUI with rich formatting
- Plugin system (approval workflow, email insights, agent visibility)
