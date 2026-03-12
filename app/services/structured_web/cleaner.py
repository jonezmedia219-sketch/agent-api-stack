from readability import Document

from app.core.html_utils import parse_html, strip_boilerplate


def prepare_soups(html: str):
    original_soup = parse_html(html)
    readable_html = Document(html).summary(html_partial=True)
    content_soup = parse_html(readable_html)
    return strip_boilerplate(original_soup, preserve_forms=True), strip_boilerplate(content_soup)
