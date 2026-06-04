"""Generic repository interface (Generics + Dependency Inversion).

Higher layers depend on this abstraction, not on the SQLAlchemy implementation.
Subclasses extend with domain-specific query and write methods as needed:
``EventRepository`` is read-only by construction; user repositories add write
operations in later phases.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class AsyncRepository(ABC, Generic[T]):
    @abstractmethod
    async def get(self, entity_id: int) -> T | None: ...
