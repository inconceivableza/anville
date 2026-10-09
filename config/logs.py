# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

import logging
import re

# ✨ A link that admits whoever holds it, as far as the token or secret that it carries: an observer's
# (ticket 13b) or a coach's (ticket 13c).
LINK_WITH_SECRET = re.compile(r"(/(?:observe|coaching)/)[^/\s?#]+")


def redact_links(text):
    return LINK_WITH_SECRET.sub(r"\1[redacted]", text)


class RedactLinks(logging.Filter):
    """✨ Takes the token or secret out of any observer's or coach's link a log record names.

    Whoever holds such a link can answer as that observer, or as the coach, so it must not be readable
    in a log. Django names the address of a failed request in what it logs. This rewrites the message
    and its arguments, and lets every record through.
    """

    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = redact_links(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(redact_links(arg) if isinstance(arg, str) else arg for arg in record.args)
        return True
