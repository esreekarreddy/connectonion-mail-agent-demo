"""
Shared pytest fixtures for Gmail Agent tests.

Provides:
- Mock WebFetch responses
- Mock Gmail tool
- Mock Memory
- Mock agent session
- Realistic test data
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json


# =============================================================================
# Realistic Mock Data
# =============================================================================

MOCK_COMPANY_ANALYSIS = """
Acme Corporation is a leading provider of enterprise software solutions.
Founded in 2015, they specialize in:
- Cloud infrastructure management
- DevOps automation tools
- Enterprise security solutions

The company has approximately 200 employees and serves Fortune 500 clients.
Headquarters: San Francisco, CA
Industry: Enterprise Software / SaaS
"""

MOCK_CONTACT_INFO = {
    "emails": ["contact@acme.com", "sales@acme.com"],
    "phone": "+1-555-123-4567",
    "address": "123 Tech Street, San Francisco, CA 94105",
}

MOCK_SOCIAL_LINKS = [
    "https://linkedin.com/company/acme",
    "https://twitter.com/acme",
    "https://github.com/acme",
]

MOCK_HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head><title>Acme Corp - Enterprise Solutions</title></head>
<body>
<h1>Welcome to Acme</h1>
<p>Contact us at contact@acme.com</p>
<a href="https://linkedin.com/company/acme">LinkedIn</a>
<a href="/about">About Us</a>
<a href="/products">Products</a>
</body>
</html>
"""

MOCK_EMAIL_LIST = """
Email 1:
ID: msg_001
From: john@acme.com
Subject: Partnership Proposal
Date: 2026-01-08
Snippet: We'd like to discuss a potential partnership...

Email 2:
ID: msg_002
From: sarah@bigcorp.com
Subject: Re: Pricing Question
Date: 2026-01-07
Snippet: Thanks for the quote. We're reviewing internally...

Email 3:
ID: msg_003
From: newsletter@competitor.com
Subject: Industry News Weekly
Date: 2026-01-06
Snippet: This week in tech: AI advances continue...
"""

MOCK_EMAIL_BODY = """
Hi,

I wanted to follow up on our conversation last week about the partnership opportunity.

We've reviewed your proposal and are interested in moving forward with the integration.
Could we schedule a call this week to discuss next steps?

Best regards,
John Smith
VP of Business Development
Acme Corporation
"""

MOCK_EMAIL_METADATA = {
    "from": "john@acme.com",
    "to": "me@mycompany.com",
    "subject": "Partnership Proposal",
    "date": "2026-01-08T10:30:00Z",
}

MOCK_SENT_EMAILS = """
Sent Email 1:
To: client@example.com
Subject: Project Update
Date: 2026-01-07
Snippet: Here's the latest update on the project...

Sent Email 2:
To: partner@company.com
Subject: Meeting Follow-up
Date: 2026-01-05
Snippet: Thanks for meeting with us yesterday...
"""

MOCK_CRM_CONTACTS = json.dumps(
    [
        {"email": "john@acme.com", "name": "John Smith", "type": "partner"},
        {"email": "sarah@bigcorp.com", "name": "Sarah Jones", "type": "client"},
        {"email": "personal@gmail.com", "name": "Personal Contact", "type": "friend"},
    ]
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_webfetch():
    """Mock WebFetch tool with realistic responses."""
    mock = Mock()

    # analyze_page returns AI analysis
    mock.analyze_page.return_value = MOCK_COMPANY_ANALYSIS

    # get_contact_info returns structured contact data
    mock.get_contact_info.return_value = json.dumps(MOCK_CONTACT_INFO)

    # fetch returns raw HTML
    mock.fetch.return_value = MOCK_HTML_CONTENT

    # get_title extracts title
    mock.get_title.return_value = "Acme Corp - Enterprise Solutions"

    # get_links returns list of links
    mock.get_links.return_value = [
        "https://acme.com/about",
        "https://acme.com/products",
        "https://acme.com/contact",
    ]

    # get_emails returns list of emails
    mock.get_emails.return_value = ["contact@acme.com", "sales@acme.com"]

    # get_social_links returns social media links
    mock.get_social_links.return_value = MOCK_SOCIAL_LINKS

    return mock


@pytest.fixture
def mock_webfetch_error():
    """Mock WebFetch that raises errors for testing error handling."""
    mock = Mock()
    mock.analyze_page.side_effect = Exception("Network timeout")
    mock.fetch.side_effect = Exception("Connection refused")
    mock.get_contact_info.side_effect = Exception("Page not found")
    return mock


@pytest.fixture
def mock_gmail():
    """Mock Gmail tool with realistic responses."""
    mock = Mock()

    # read_inbox returns email list
    mock.read_inbox.return_value = MOCK_EMAIL_LIST

    # search_emails returns filtered results
    mock.search_emails.return_value = MOCK_EMAIL_LIST

    # get_email_body returns full email content
    mock.get_email_body.return_value = MOCK_EMAIL_BODY

    # get_email_metadata returns email headers
    mock.get_email_metadata.return_value = MOCK_EMAIL_METADATA

    # get_sent_emails returns sent email list
    mock.get_sent_emails.return_value = MOCK_SENT_EMAILS

    # get_unanswered_emails returns emails needing reply
    mock.get_unanswered_emails.return_value = MOCK_EMAIL_LIST

    # count_unread returns count
    mock.count_unread.return_value = 5

    return mock


@pytest.fixture
def mock_gmail_empty():
    """Mock Gmail with empty responses."""
    mock = Mock()
    mock.read_inbox.return_value = "No emails found."
    mock.search_emails.return_value = "No emails match your search."
    mock.get_sent_emails.return_value = "No sent emails found."
    mock.get_unanswered_emails.return_value = "No unanswered emails."
    return mock


@pytest.fixture
def mock_memory():
    """Mock Memory tool with realistic responses."""
    mock = Mock()

    # Storage for test
    storage = {}

    def write_memory(key, value, **kwargs):
        storage[key] = value
        return f"Saved to memory: {key}"

    def read_memory(key):
        if key in storage:
            return storage[key]
        return f"Memory not found: {key}"

    mock.write_memory.side_effect = write_memory
    mock.read_memory.side_effect = read_memory
    mock.get.side_effect = lambda k: storage.get(k)
    mock.set.side_effect = lambda k, v, **kw: storage.update({k: v})

    return mock


@pytest.fixture
def mock_memory_with_data(mock_memory):
    """Mock Memory pre-populated with test data."""
    mock_memory.read_memory.side_effect = None
    mock_memory.read_memory.return_value = MOCK_CRM_CONTACTS
    return mock_memory


@pytest.fixture
def mock_llm_do():
    """Mock llm_do function that returns Pydantic models."""

    def _mock_llm_do(prompt, output=None, model=None):
        if output is None:
            return "Generic LLM response"

        # Return a mock instance of the output class
        mock_instance = Mock(spec=output)

        # Set common fields based on class name
        class_name = output.__name__ if hasattr(output, "__name__") else str(output)

        if "ContactResearch" in class_name:
            mock_instance.company_name = "Acme Corporation"
            mock_instance.company_description = "Enterprise software company"
            mock_instance.likely_role = "Business Development"
            mock_instance.industry = "Enterprise Software"
            mock_instance.company_size_hint = "200 employees"
            mock_instance.social_links = MOCK_SOCIAL_LINKS
            mock_instance.talking_points = [
                "Their cloud platform just launched",
                "They're expanding into Europe",
                "Recent Series B funding",
            ]
            mock_instance.email_tone_suggestion = "professional"

        elif "CompanyScan" in class_name:
            mock_instance.name = "Acme Corporation"
            mock_instance.description = "Enterprise software company"
            mock_instance.products_services = ["Cloud Platform", "DevOps Tools"]
            mock_instance.contact_emails = ["contact@acme.com"]
            mock_instance.phone = "+1-555-123-4567"
            mock_instance.address = "San Francisco, CA"
            mock_instance.social_links = MOCK_SOCIAL_LINKS
            mock_instance.key_pages = ["/about", "/products", "/pricing"]

        elif "SmartReplyContext" in class_name:
            mock_instance.sender_company = "Acme Corporation"
            mock_instance.sender_likely_role = "VP Business Development"
            mock_instance.relationship_summary = "Potential partner, discussed integration"
            mock_instance.recent_topics = ["partnership", "integration", "pricing"]
            mock_instance.recommended_tone = "professional"
            mock_instance.suggested_reply = "Hi John,\n\nThank you for your follow-up..."

        elif "OutreachPrep" in class_name:
            mock_instance.company_overview = "Enterprise software company"
            mock_instance.likely_pain_points = ["Scaling infrastructure", "Security compliance"]
            mock_instance.value_proposition = "Our solution helps with X"
            mock_instance.personalized_openers = [
                "I noticed your recent product launch...",
                "Congrats on the Series B funding...",
            ]
            mock_instance.best_time_to_email = "Tuesday-Thursday, 10am-2pm"
            mock_instance.linkedin_search_tips = "Search by name + Acme Corporation"

        elif "CompetitorMention" in class_name:
            mock_instance.mention_count = 5
            mock_instance.sentiment_breakdown = {"positive": 1, "neutral": 3, "negative": 1}
            mock_instance.deals_at_risk = ["BigCorp is considering competitor"]
            mock_instance.opportunities = ["Client complained about competitor support"]
            mock_instance.summary = "Competitor mentioned in 5 emails, mixed sentiment"

        return mock_instance

    return _mock_llm_do


@pytest.fixture
def mock_agent_session():
    """Mock agent session for plugin testing."""
    return {
        "user_prompt": "",
        "messages": [],
        "trace": [],
        "pending_tool": {},
        "insights": [],
        "auto_researched": [],
    }


@pytest.fixture
def mock_agent(mock_agent_session):
    """Mock agent with session for plugin testing."""
    agent = Mock()
    agent.current_session = mock_agent_session
    return agent


@pytest.fixture
def mock_agent_with_email_trace(mock_agent):
    """Mock agent with email tool trace."""
    mock_agent.current_session["trace"] = [
        {"type": "tool_execution", "tool_name": "read_inbox", "result": MOCK_EMAIL_LIST}
    ]
    return mock_agent


# =============================================================================
# Test Data Helpers
# =============================================================================


def make_email(id: str, sender: str, subject: str, body: str = "") -> dict:
    """Create a test email dict."""
    return {
        "id": id,
        "from": sender,
        "subject": subject,
        "body": body or f"Body of {subject}",
        "date": "2026-01-08",
    }


def make_contact(email: str, name: str, type: str = "contact") -> dict:
    """Create a test contact dict."""
    return {"email": email, "name": name, "type": type}
