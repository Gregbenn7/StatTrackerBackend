"""Base repository interface."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository interface for data access."""
    
    @abstractmethod
    def get(self, id: int) -> Optional[T]:
        """Get an entity by ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Get all entities."""
        pass

