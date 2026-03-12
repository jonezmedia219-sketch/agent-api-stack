from bs4 import BeautifulSoup

from app.core.contact_utils import (
    detect_contact_forms,
    extract_addresses,
    extract_emails,
    extract_phone_numbers,
    extract_social_media_links,
    pick_company_name,
)
from app.core.html_utils import extract_headings, extract_visible_text
from app.core.metadata_utils import extract_metadata, extract_title
from app.models.lead_extract import LeadExtractData


def extract_lead_data(*, original_soup: BeautifulSoup, content_soup: BeautifulSoup, source_url: str | None = None) -> LeadExtractData:
    full_text = extract_visible_text(original_soup)
    metadata = extract_metadata(original_soup)
    headings = [heading["text"] for heading in extract_headings(content_soup)]
    company_name = pick_company_name(
        title=extract_title(original_soup),
        site_name=metadata.get("site_name"),
        headings=headings,
    )

    return LeadExtractData(
        source_url=source_url,
        emails=extract_emails(full_text),
        phone_numbers=extract_phone_numbers(full_text),
        social_media_links=extract_social_media_links(original_soup, base_url=source_url),
        company_name=company_name,
        contact_forms_detected=detect_contact_forms(original_soup),
        addresses=extract_addresses(full_text),
    )
