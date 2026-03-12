from app.core.http_client import fetch_html
from app.core.validators import validate_html_length, validate_url
from app.models.structured_web import StructuredWebData
from app.services.structured_web.cleaner import prepare_soups
from app.services.structured_web.extractor import extract_structured_web_data
from app.config import get_settings


async def extract_from_url(url: str) -> StructuredWebData:
    settings = get_settings()
    validated_url = validate_url(url)
    html, content_type = await fetch_html(validated_url)
    validate_html_length(html, settings.structured_web_max_html_chars)
    original_soup, content_soup = prepare_soups(html)
    return extract_structured_web_data(
        original_soup=original_soup,
        content_soup=content_soup,
        source_url=validated_url,
        fetched_content_type=content_type,
    )


def extract_from_html(html: str, source_url: str | None = None) -> StructuredWebData:
    settings = get_settings()
    validate_html_length(html, settings.structured_web_max_html_chars)
    if source_url:
        validate_url(source_url)
    original_soup, content_soup = prepare_soups(html)
    return extract_structured_web_data(original_soup=original_soup, content_soup=content_soup, source_url=source_url)
