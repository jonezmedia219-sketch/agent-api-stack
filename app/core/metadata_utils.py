import json
import re
from email.utils import parsedate_to_datetime
from typing import Any

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from app.core.text_utils import clean_whitespace


DATE_META_KEYS = [
    "article:published_time",
    "og:published_time",
    "publish-date",
    "pubdate",
    "date",
    "dc.date",
    "dc.date.issued",
]
AUTHOR_META_KEYS = ["author", "article:author", "parsely-author", "dc.creator"]


def _extract_meta_by_name(soup: BeautifulSoup, key: str) -> str | None:
    tag = soup.find("meta", attrs={"name": key}) or soup.find("meta", attrs={"property": key})
    if tag and tag.get("content"):
        return clean_whitespace(tag["content"])
    return None


def extract_title(soup: BeautifulSoup) -> str | None:
    og_title = _extract_meta_by_name(soup, "og:title")
    if og_title:
        return og_title
    if soup.title and soup.title.string:
        return clean_whitespace(soup.title.string)
    h1 = soup.find("h1")
    return clean_whitespace(h1.get_text(" ", strip=True)) if h1 else None


def extract_author(soup: BeautifulSoup) -> str | None:
    for key in AUTHOR_META_KEYS:
        value = _extract_meta_by_name(soup, key)
        if value:
            return value
    author_el = soup.find(attrs={"rel": "author"})
    if author_el:
        return clean_whitespace(author_el.get_text(" ", strip=True))
    return None


def extract_published_date(soup: BeautifulSoup) -> str | None:
    candidates: list[str] = []
    for key in DATE_META_KEYS:
        value = _extract_meta_by_name(soup, key)
        if value:
            candidates.append(value)
    for time_tag in soup.find_all("time"):
        if time_tag.get("datetime"):
            candidates.append(time_tag["datetime"])
        elif time_tag.get_text(strip=True):
            candidates.append(time_tag.get_text(" ", strip=True))
    for candidate in candidates:
        try:
            parsed = date_parser.parse(candidate)
            return parsed.date().isoformat()
        except (ValueError, TypeError, OverflowError):
            try:
                return parsedate_to_datetime(candidate).date().isoformat()
            except Exception:
                continue
    return None


def extract_metadata(soup: BeautifulSoup) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    description = _extract_meta_by_name(soup, "description") or _extract_meta_by_name(soup, "og:description")
    if description:
        metadata["description"] = description

    canonical = soup.find("link", attrs={"rel": re.compile("canonical", re.I)})
    if canonical and canonical.get("href"):
        metadata["canonical_url"] = clean_whitespace(canonical["href"])

    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        metadata["lang"] = html_tag["lang"]

    site_name = _extract_meta_by_name(soup, "og:site_name")
    if site_name:
        metadata["site_name"] = site_name

    json_ld = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text(strip=True)
        if not raw:
            continue
        try:
            json_ld.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    if json_ld:
        metadata["json_ld"] = json_ld

    return metadata
