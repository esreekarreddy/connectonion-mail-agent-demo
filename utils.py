"""Shared utilities for Email Agent.

Common functions used across multiple modules.
"""

import logging
import os
import re
import time
import fcntl
from pathlib import Path
from typing import Optional, Callable, TypeVar, Any

from config import (
    BLOCKED_DOMAIN_PATTERNS,
    PERSONAL_EMAIL_DOMAINS,
    LLM_RETRY_ATTEMPTS,
    LLM_RETRY_DELAY,
    ENV_FILE,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def is_valid_email(email: str) -> bool:
    """Validate email format using RFC 5322 simplified pattern."""
    if not email or "@" not in email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_personal_email(email: str) -> bool:
    """Check if email is from a personal domain."""
    if "@" not in email:
        return False
    domain = email.split("@")[1].lower()
    return domain in PERSONAL_EMAIL_DOMAINS


def is_safe_domain(domain: str) -> bool:
    """Check if domain is safe to fetch (SSRF protection).

    Blocks internal IPs, localhost, and private network ranges.
    """
    domain_lower = domain.lower().strip()

    for pattern in BLOCKED_DOMAIN_PATTERNS:
        if re.search(pattern, domain_lower):
            logger.warning(f"Blocked unsafe domain: {domain}")
            return False

    return True


def extract_domain(email: str) -> Optional[str]:
    """Extract domain from email address."""
    if "@" not in email:
        return None
    return email.split("@")[1].lower()


def set_env_flag(key: str, value: str) -> bool:
    """Thread-safe environment flag setter with file locking.

    Uses fcntl for file locking to prevent race conditions.
    Returns True on success, False on failure.
    """
    env_path = Path(ENV_FILE)

    try:
        env_path.touch(exist_ok=True)

        with open(env_path, "r+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                lines = f.read().splitlines()

                found = False
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}"
                        found = True
                        break

                if not found:
                    lines.append(f"{key}={value}")

                f.seek(0)
                f.truncate()
                f.write("\n".join(lines) + "\n")
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        return True
    except (IOError, OSError) as e:
        logger.error(f"Failed to set env flag {key}: {e}")
        return False


def retry_with_backoff(
    func: Callable[..., T],
    *args: Any,
    max_attempts: int = LLM_RETRY_ATTEMPTS,
    base_delay: float = LLM_RETRY_DELAY,
    **kwargs: Any,
) -> T:
    """Execute function with exponential backoff retry.

    Args:
        func: Function to execute
        *args: Positional arguments for func
        max_attempts: Maximum retry attempts
        base_delay: Base delay between retries (doubles each attempt)
        **kwargs: Keyword arguments for func

    Returns:
        Result of successful function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_attempts - 1:
                delay = base_delay * (2**attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_attempts} attempts failed: {e}")

    raise last_exception


def safe_truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Safely truncate text to max_length, adding suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def parse_memory_line(line: str) -> Optional[tuple]:
    """Parse a memory line safely, handling edge cases.

    Returns (key, date, notes) tuple or None if parsing fails.
    Uses a more robust parsing approach than simple split.
    """
    if not line or "contact:" not in line.lower():
        return None

    parts = line.split("|", maxsplit=2)
    if len(parts) < 2:
        return None

    key = parts[0].strip()
    date_str = parts[1].strip() if len(parts) > 1 else None
    notes = parts[2].strip() if len(parts) > 2 else None

    return (key, date_str, notes)
