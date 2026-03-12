from app.models.search import SearchResultItem
from app.services.search.base import SearchProvider


class MockSearchProvider(SearchProvider):
    source_name = "mock"

    async def search(self, query: str, limit: int) -> list[SearchResultItem]:
        base_results = [
            SearchResultItem(
                title=f"{query} - Overview",
                url="https://example.com/overview",
                snippet=f"Overview results for {query}.",
                source=self.source_name,
                rank=1,
            ),
            SearchResultItem(
                title=f"{query} - Deep Dive",
                url="https://example.com/deep-dive",
                snippet=f"Detailed information about {query}.",
                source=self.source_name,
                rank=2,
            ),
            SearchResultItem(
                title=f"{query} - Comparison",
                url="https://example.com/comparison",
                snippet=f"Comparison results related to {query}.",
                source=self.source_name,
                rank=3,
            ),
        ]
        return base_results[:limit]
