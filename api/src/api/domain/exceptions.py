from __future__ import annotations


class EventHubError(Exception):
    """Base for all domain-level EventHub errors."""


class EventNotFoundError(EventHubError):
    """Raised when a requested event does not exist."""

    def __init__(self, event_id: int) -> None:
        super().__init__(f"Event {event_id} not found")
        self.event_id = event_id


class InvalidCredentialsError(EventHubError):
    """Raised when email/password do not match any active account."""


class UserAlreadyExistsError(EventHubError):
    """Raised on registration when the email is already taken."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Account with email {email!r} already exists")
        self.email = email


class AlreadySavedError(EventHubError):
    """Raised when the user tries to save an event they already saved."""

    def __init__(self, source: str, external_id: str) -> None:
        super().__init__(f"Event {source}/{external_id} is already in saved events")
        self.source = source
        self.external_id = external_id


class ReminderNotFoundError(EventHubError):
    """Raised when a reminder does not exist or does not belong to the caller."""

    def __init__(self, reminder_id: int) -> None:
        super().__init__(f"Reminder {reminder_id} not found")
        self.reminder_id = reminder_id
