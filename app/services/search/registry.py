from app.exceptions import ValidationError
from app.services.search.adapters.mock_provider import MockSearchProvider
from app.services.search.base import SearchProvider


_PROVIDER_REGISTRY: dict[str, type[SearchProvider]] = {
    "mock": MockSearchProvider,
}


def get_provider(source: str) -> SearchProvider:
    provider_cls = _PROVIDER_REGISTRY.get(source.lower())
    if not provider_cls:
        raise ValidationError(f"Unsupported search source: {source}")
    return provider_cls()


def list_providers() -> list[str]:
    return sorted(_PROVIDER_REGISTRY.keys())
