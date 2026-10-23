"""Message type passed from worker threads to the overlay."""

from typing import NamedTuple, Optional

KIND_TEXT = "text"
KIND_MSG = "msg"


class Message(NamedTuple):
    kind: str                       # KIND_TEXT or KIND_MSG
    text: str
    finished: Optional[bool] = None  # only meaningful for KIND_TEXT


def status(text: str) -> Message:
    """A status/error message shown in the overlay."""
    return Message(KIND_MSG, text)


def caption(text: str, finished: bool) -> Message:
    """Recognized speech (partial or finished)."""
    return Message(KIND_TEXT, text, finished)
