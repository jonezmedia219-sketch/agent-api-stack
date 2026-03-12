from app.config import get_settings
from app.core.http_client import fetch_html
from app.core.validators import validate_html_length, validate_url
from app.models.lead_extract import LeadExtractData
from app.services.structured_web.cleaner import prepare_soups
from app.services.lead_extract.extractor import extract_lead_data


async def extract_leads_from_url(url: str) -> LeadExtractData:
    settings = get_settings()
    validated_url = validate_url(url)
    html, _content_type = await fetch_html(validated_url)
    validate_html_length(html, settings.structured_web_max_html_chars)
    original_soup, content_soup = prepare_soups(html)
    return extract_lead_data(original_soup=original_soup, content_soup=content_soup, source_url=validated_url)


def extract_leads_from_html(html: str, source_url: str | None = None) -> LeadExtractData:
    settings = get_settings()
    validate_html_length(html, settings.structured_web_max_html_chars)
    if source_url:
        validate_url(source_url)
    original_soup, content_soup = prepare_soups(html)
    return extract_lead_data(original_soup=original_soup, content_soup=content_soup, source_url=source_url)
