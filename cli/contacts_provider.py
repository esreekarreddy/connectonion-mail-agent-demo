"""Contact provider for @ autocomplete in Input.

Provides fuzzy search across contacts with rich metadata display.
"""

import csv
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CONTACTS_FILE

from connectonion.tui import CommandItem
from connectonion.tui.fuzzy import fuzzy_match


class HealthScore(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    HEALTHY = "healthy"
    UNKNOWN = ""


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = ""


class ContactProvider:
    """Autocomplete provider for email contacts.

    Reads contacts from data/contacts.csv and provides fuzzy search
    with rich metadata display (name, email, company, relationship).

    Usage:
        from cli.contacts_provider import ContactProvider

        provider = ContactProvider()
        results = provider.search("dav")  # Fuzzy matches "Davis", "David", etc.
    """

    def __init__(self, contacts_file: str = CONTACTS_FILE):
        self.contacts_file = Path(contacts_file)
        self._contacts: Optional[list[dict]] = None

    def _load_contacts(self) -> list[dict]:
        """Load contacts from CSV file."""
        if self._contacts is not None:
            return self._contacts

        self._contacts = []
        if not self.contacts_file.exists():
            return self._contacts

        with open(self.contacts_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get("email", "").strip()
                name = row.get("name", "").strip()
                company = row.get("company", "").strip()
                relationship = row.get("relationship", "").strip()
                priority_str = row.get("priority", "").strip().lower()
                priority = (
                    Priority(priority_str)
                    if priority_str in [e.value for e in Priority]
                    else Priority.UNKNOWN
                )
                contact_type = row.get("type", "").strip()
                health_score_str = row.get("health_score", "").strip().lower()
                health_score = (
                    HealthScore(health_score_str)
                    if health_score_str in [e.value for e in HealthScore]
                    else HealthScore.UNKNOWN
                )
                last_contact = row.get("last_contact", "").strip()

                if email:
                    self._contacts.append(
                        {
                            "email": email,
                            "name": name,
                            "company": company,
                            "relationship": relationship,
                            "priority": priority,
                            "type": contact_type,
                            "health_score": health_score,
                            "last_contact": last_contact,
                        }
                    )

        return self._contacts

    def _get_icon(self, contact: dict) -> str:
        """Get icon based on contact type and health score."""
        contact_type = contact.get("type", "").upper()
        health = contact.get("health_score", HealthScore.UNKNOWN)

        # Health-based icons for people
        if contact_type == "PERSON":
            if health == HealthScore.CRITICAL:
                return "🔴"  # Red - needs attention
            elif health == HealthScore.WARNING:
                return "🟡"  # Yellow - follow up soon
            elif health == HealthScore.HEALTHY:
                return "🟢"  # Green - good
            return "👤"  # Default person
        elif contact_type == "SERVICE":
            return "🔧"
        elif contact_type == "NOTIFICATION":
            return "🔔"
        return "📧"

    def _build_subtitle(self, contact: dict) -> str:
        """Build subtitle from company, relationship, and last contact."""
        parts = []
        if contact.get("company"):
            parts.append(contact["company"])
        if contact.get("relationship"):
            parts.append(contact["relationship"])
        if contact.get("last_contact"):
            parts.append(f"Last: {contact['last_contact']}")
        return " · ".join(parts)

    def search(self, query: str) -> list[dict]:
        """Search contacts with fuzzy matching.

        Returns list of dicts with match info.
        """
        contacts = self._load_contacts()
        results = []

        for contact in contacts:
            email = contact["email"]
            name = contact["name"]

            # Match against both name and email
            search_text = f"{name} {email}" if name else email
            matched, score, positions = fuzzy_match(query, search_text)

            if matched:
                # Priority contacts get a boost
                if contact.get("priority") == Priority.HIGH:
                    score += 50

                # Critical health contacts get a boost (need attention)
                if contact.get("health_score") == HealthScore.CRITICAL:
                    score += 30

                results.append(
                    {
                        "contact": contact,
                        "score": score,
                        "positions": positions,
                    }
                )

        # Sort by score (highest first)
        return sorted(results, key=lambda x: -x["score"])

    def to_command_items(self) -> list[CommandItem]:
        """Convert contacts to CommandItem format for Chat autocomplete.

        Returns list of CommandItem for use with Chat triggers.
        """
        contacts = self._load_contacts()
        items = []

        for contact in contacts:
            email = contact["email"]
            name = contact.get("name", "")
            company = contact.get("company", "")
            relationship = contact.get("relationship", "")

            # Display: name - email (or just email if no name)
            if name:
                display = f"{name} - {email}"
                if company:
                    display += f" ({company})"
            else:
                display = email

            # Add relationship hint
            if relationship:
                display += f" [{relationship}]"

            items.append(
                CommandItem(
                    main=display,
                    prefix=self._get_icon(contact),
                    id=f"@{email}",
                )
            )

        return items

    def get_by_email(self, email: str) -> Optional[dict]:
        """Get contact by email address."""
        contacts = self._load_contacts()
        for contact in contacts:
            if contact["email"].lower() == email.lower():
                return contact
        return None

    def get_high_priority(self) -> list[dict]:
        """Get all high priority contacts."""
        contacts = self._load_contacts()
        return [c for c in contacts if c.get("priority") == Priority.HIGH]

    def get_needs_attention(self) -> list[dict]:
        """Get contacts that need attention (critical/warning health)."""
        contacts = self._load_contacts()
        return [
            c
            for c in contacts
            if c.get("health_score") in (HealthScore.CRITICAL, HealthScore.WARNING)
        ]
