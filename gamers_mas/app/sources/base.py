from abc import ABC, abstractmethod


class DealSource(ABC):
    """Base interface for all deal sources."""

    source_name: str

    @abstractmethod
    def search_deals(self, title: str, **filters) -> list[dict]:
        """Return deals for the requested title."""
        raise NotImplementedError