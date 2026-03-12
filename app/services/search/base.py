from abc import ABC, abstractmethod

from app.models.search import SearchResultItem


class SearchProvider(ABC):
    source_name: str

    @abstractmethod
    async def search(self, query: str, limit: int) -> list[SearchResultItem]:
        raise NotImplementedError
