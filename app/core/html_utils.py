from bs4 import BeautifulSoup

from app.core.text_utils import clean_whitespace, dedupe_preserve_order
from app.core.url_utils import absolutize_url, is_allowed_link


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def strip_boilerplate(soup: BeautifulSoup, preserve_forms: bool = False) -> BeautifulSoup:
    removable_tags = ["script", "style", "noscript", "iframe", "svg", "footer", "nav", "aside"]
    if not preserve_forms:
        removable_tags.append("form")
    for tag_name in removable_tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    return soup


def extract_headings(soup: BeautifulSoup) -> list[dict]:
    headings = []
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            text = clean_whitespace(tag.get_text(" ", strip=True))
            if text:
                headings.append({"level": level, "text": text})
    return headings


def extract_links(soup: BeautifulSoup, base_url: str | None = None, max_links: int = 100) -> list[dict]:
    links = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href or not is_allowed_link(href):
            continue
        absolute = absolutize_url(base_url, href)
        if absolute in seen:
            continue
        seen.add(absolute)
        text = clean_whitespace(anchor.get_text(" ", strip=True))
        links.append({"text": text, "href": absolute})
        if len(links) >= max_links:
            break
    return links


def extract_visible_text(soup: BeautifulSoup) -> str:
    text_fragments = []
    for element in soup.find_all(["p", "li", "blockquote", "pre"]):
        text = clean_whitespace(element.get_text(" ", strip=True))
        if text:
            text_fragments.append(text)
    return clean_whitespace("\n\n".join(dedupe_preserve_order(text_fragments)))
