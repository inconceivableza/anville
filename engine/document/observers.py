"""✨ What the pathway document says about inviting observers (ADR 0005). Nothing here touches the database or a request."""

from datetime import timedelta

# ✨ Long enough for a ten-to-fifteen-minute task someone may take a while to get to (ADR 0005).
DEFAULT_LINK_LIFETIME_DAYS = 30


def link_lifetime(document):
    """✨ How long an observer's link works once issued: the document's `link_lifetime_days`, or 30 days."""
    days = document.get("observers", {}).get("link_lifetime_days", DEFAULT_LINK_LIFETIME_DAYS)
    return timedelta(days=days)
