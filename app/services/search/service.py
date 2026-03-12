from app.exceptions import ValidationError
from app.models.search import SearchResponseData, SearchResultItem
from app.services.search.registry import get_provider, list_providers


async def search(query: str, limit: int = 10, source: str | None = None) -> SearchResponseData:
    query = query.strip()
    if not query:
        raise ValidationError("Query parameter 'q' is required.")
    if limit < 1 or limit > 25:
        raise ValidationError("Query parameter 'limit' must be between 1 and 25.")

    sources = [source] if source else list_providers()
    results: list[SearchResultItem] = []

    for provider_source in sources:
        provider = get_provider(provider_source)
        provider_results = await provider.search(query, limit)
        results.extend(provider_results)

    normalized_results = []
    for index, item in enumerate(results[:limit], start=1):
        normalized_results.append(
            SearchResultItem(
                title=item.title,
                url=item.url,
                snippet=item.snippet,
                source=item.source,
                rank=index,
            )
        )

    return SearchResponseData(
        query=query,
        results=normalized_results,
        sources=sources,
        count=len(normalized_results),
    )
