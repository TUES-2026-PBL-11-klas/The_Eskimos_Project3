"""Custom exception hierarchy for the ingestion service.

A single base (`EventHubError`) lets callers catch everything from this service with one
`except`, while the subclasses let the pipeline/orchestrator react per failure kind
(e.g. drop one invalid event but keep the batch running).
"""

from __future__ import annotations


class EventHubError(Exception):
    """Base for all ingestion errors."""


class ScrapingError(EventHubError):
    """A source failed to fetch or parse."""


class InvalidEventDataError(EventHubError):
    """An event failed validation and is dropped."""
