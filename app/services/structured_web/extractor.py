from bs4 import BeautifulSoup

from app.config import get_settings
from app.core.html_utils import extract_headings, extract_links, extract_visible_text
from app.core.metadata_utils import extract_author, extract_metadata, extract_published_date, extract_title
from app.core.text_utils import naive_summary
from app.models.structured_web import StructuredWebData
from app.services.structured_web.detectors import detect_content_type


def extract_structured_web_data(
    *,
    original_soup: BeautifulSoup,
    content_soup: BeautifulSoup,
    source_url: str | None = None,
    fetched_content_type: str | None = None,
) -> StructuredWebData:
    settings = get_settings()
    main_text = extract_visible_text(content_soup)
    return StructuredWebData(
        url=source_url,
        content_type=detect_content_type(original_soup, fetched_content_type),
        title=extract_title(original_soup),
        author=extract_author(original_soup),
        published_date=extract_published_date(original_soup),
        summary=naive_summary(main_text),
        main_text=main_text,
        headings=extract_headings(content_soup),
        links=extract_links(original_soup, base_url=source_url, max_links=settings.structured_web_max_links),
        metadata=extract_metadata(original_soup),
    )
