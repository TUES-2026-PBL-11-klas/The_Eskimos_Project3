"""Generic repository interface (Generics + Dependency Inversion).

Higher layers (the pipeline, the orchestrator) depend on this abstraction, not on the
concrete SQLAlchemy implementation — so persistence can be swapped or faked in tests.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    async def add(self, entity: T) -> T: ...

    @abstractmethod
    async def upsert(self, entity: T) -> T: ...

    @abstractmethod
    async def get(self, entity_id: int) -> T | None: ...

    @abstractmethod
    async def find_duplicate(self, entity: T) -> T | None: ...
