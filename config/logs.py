import logging
import re

# ✨ An observer's link, as far as the token or secret that it carries.
OBSERVER_LINK = re.compile(r"(/observe/)[^/\s?#]+")


def redact_observer_links(text):
    return OBSERVER_LINK.sub(r"\1[redacted]", text)


class RedactObserverLinks(logging.Filter):
    """✨ Takes the token or secret out of any observer's link a log record names.

    Whoever holds an observer's link can answer as that observer, so it must not be readable in a log.
    Django names the address of a failed request in what it logs. This rewrites the message and its
    arguments, and lets every record through.
    """

    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = redact_observer_links(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                redact_observer_links(arg) if isinstance(arg, str) else arg for arg in record.args
            )
        return True
