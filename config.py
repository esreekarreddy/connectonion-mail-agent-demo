"""Centralized configuration for Email Agent.

All hardcoded values, thresholds, and constants should be defined here.
Environment variables can override defaults.
"""

import os
from typing import List, Set

# =============================================================================
# LLM MODELS
# =============================================================================

DEFAULT_MODEL = os.getenv("EMAIL_AGENT_MODEL", "co/claude-opus-4-5")
FAST_MODEL = os.getenv("EMAIL_AGENT_FAST_MODEL", "co/gemini-2.5-flash")

# =============================================================================
# AGENT CONFIGURATION
# =============================================================================

MAX_ITERATIONS_MAIN = int(os.getenv("EMAIL_AGENT_MAX_ITERATIONS", "20"))
MAX_ITERATIONS_CRM = int(os.getenv("EMAIL_AGENT_CRM_MAX_ITERATIONS", "30"))

# =============================================================================
# PERSONAL EMAIL DOMAINS (Skip web research for these)
# =============================================================================

PERSONAL_EMAIL_DOMAINS: Set[str] = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "icloud.com",
    "aol.com",
    "protonmail.com",
    "proton.me",
    "mail.com",
    "zoho.com",
    "yandex.com",
    "gmx.com",
    "fastmail.com",
    "tutanota.com",
    "hey.com",
}

# =============================================================================
# SECURITY: SSRF PROTECTION
# =============================================================================

BLOCKED_DOMAIN_PATTERNS: List[str] = [
    r"^127\.",
    r"^10\.",
    r"^172\.(1[6-9]|2[0-9]|3[01])\.",
    r"^192\.168\.",
    r"^169\.254\.",
    r"^0\.",
    r"^::1$",
    r"^fd[0-9a-f]{2}:",
    r"^fe80:",
    r"localhost",
    r"\.internal$",
    r"\.local$",
    r"\.localdomain$",
    r"\.corp$",
    r"\.lan$",
]

# =============================================================================
# CONTENT LIMITS
# =============================================================================

MAX_PAGE_CONTENT_LENGTH = int(os.getenv("EMAIL_AGENT_MAX_PAGE_CONTENT", "4000"))
MAX_EMAIL_PREVIEW_LENGTH = int(os.getenv("EMAIL_AGENT_MAX_EMAIL_PREVIEW", "2000"))
MAX_BODY_PREVIEW_LENGTH = int(os.getenv("EMAIL_AGENT_MAX_BODY_PREVIEW", "200"))
MIN_VALID_PAGE_CONTENT = 100
MIN_VALID_CACHE_LENGTH = 50

# =============================================================================
# RELATIONSHIP THRESHOLDS (days)
# =============================================================================

RELATIONSHIP_CRITICAL_DAYS = int(os.getenv("EMAIL_AGENT_CRITICAL_DAYS", "14"))
RELATIONSHIP_WARNING_DAYS = int(os.getenv("EMAIL_AGENT_WARNING_DAYS", "7"))
RELATIONSHIP_FALLBACK_DAYS = 5

# =============================================================================
# CRM DEFAULTS
# =============================================================================

DEFAULT_CRM_MAX_EMAILS = int(os.getenv("EMAIL_AGENT_CRM_MAX_EMAILS", "500"))
DEFAULT_CRM_TOP_N = int(os.getenv("EMAIL_AGENT_CRM_TOP_N", "10"))

# =============================================================================
# GMAIL SEARCH DEFAULTS
# =============================================================================

DEFAULT_GMAIL_SEARCH_LIMIT = int(os.getenv("EMAIL_AGENT_GMAIL_SEARCH_LIMIT", "50"))

# =============================================================================
# DISPLAY LIMITS
# =============================================================================

MAX_TOPICS_DISPLAY = int(os.getenv("EMAIL_AGENT_MAX_TOPICS_DISPLAY", "3"))

# =============================================================================
# TIMEOUTS (seconds)
# =============================================================================

SUBPROCESS_TIMEOUT = int(os.getenv("EMAIL_AGENT_SUBPROCESS_TIMEOUT", "120"))
LLM_RETRY_ATTEMPTS = int(os.getenv("EMAIL_AGENT_LLM_RETRIES", "3"))
LLM_RETRY_DELAY = float(os.getenv("EMAIL_AGENT_LLM_RETRY_DELAY", "1.0"))

# =============================================================================
# FILE LIMITS
# =============================================================================

MAX_AUDIO_FILE_SIZE_MB = int(os.getenv("EMAIL_AGENT_MAX_AUDIO_MB", "25"))
MAX_AUDIO_FILE_SIZE_BYTES = MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024

SUPPORTED_AUDIO_FORMATS = {".wav", ".mp3", ".aiff", ".aac", ".ogg", ".flac", ".m4a"}

# =============================================================================
# PATHS
# =============================================================================

DATA_DIR = "data"
MEMORY_FILE = os.path.join(DATA_DIR, "memory.md")
CONTACTS_FILE = os.path.join(DATA_DIR, "contacts.csv")
ENV_FILE = ".env"

# =============================================================================
# CACHE SETTINGS
# =============================================================================

INSIGHTS_CACHE_TTL_SECONDS = int(os.getenv("EMAIL_AGENT_INSIGHTS_CACHE_TTL", "300"))
