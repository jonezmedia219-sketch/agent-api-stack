import re
from typing import Iterable

from bs4 import BeautifulSoup

from app.core.text_utils import clean_whitespace, dedupe_preserve_order
from app.core.url_utils import absolutize_url

EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,2}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}\b")
ADDRESS_PATTERN = re.compile(
    r"\b\d{1,6}\s+[A-Za-z0-9.\-\s]+,\s*[A-Za-z.\-\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b"
)
SOCIAL_DOMAINS = (
    "linkedin.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "tiktok.com",
    "github.com",
)


def extract_emails(text: str) -> list[str]:
    return dedupe_preserve_order(EMAIL_PATTERN.findall(text))


def extract_phone_numbers(text: str) -> list[str]:
    return dedupe_preserve_order([clean_whitespace(match) for match in PHONE_PATTERN.findall(text)])


def extract_addresses(text: str) -> list[str]:
    return dedupe_preserve_order([clean_whitespace(match) for match in ADDRESS_PATTERN.findall(text)])


def extract_social_media_links(soup: BeautifulSoup, base_url: str | None = None) -> list[str]:
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href:
            continue
        absolute = absolutize_url(base_url, href)
        lower = absolute.lower()
        if any(domain in lower for domain in SOCIAL_DOMAINS):
            links.append(absolute)
    return dedupe_preserve_order(links)


def detect_contact_forms(soup: BeautifulSoup) -> bool:
    for form in soup.find_all("form"):
        inputs = [field.get("name", "").lower() for field in form.find_all(["input", "textarea", "select"])]
        if any(name in {"email", "message", "name", "phone"} for name in inputs):
            return True
        form_text = clean_whitespace(form.get_text(" ", strip=True)).lower()
        if any(token in form_text for token in ["contact", "message", "email", "submit"]):
            return True
    return False


def pick_company_name(*, title: str | None = None, site_name: str | None = None, headings: Iterable[str] | None = None) -> str | None:
    for candidate in [site_name, title, *(headings or [])]:
        if candidate:
            cleaned = clean_whitespace(candidate)
            if cleaned:
                return cleaned
    return None
