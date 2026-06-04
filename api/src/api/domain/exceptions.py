from __future__ import annotations


class EventHubError(Exception):
    """Base for all domain-level EventHub errors."""


class EventNotFoundError(EventHubError):
    """Raised when a requested event does not exist."""

    def __init__(self, event_id: int) -> None:
        super().__init__(f"Event {event_id} not found")
        self.event_id = event_id
