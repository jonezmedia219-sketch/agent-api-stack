import httpx

from app.config import get_settings
from app.core.contact_utils import extract_emails, extract_phone_numbers, extract_social_media_links
from app.core.html_utils import extract_links, extract_visible_text, parse_html, strip_boilerplate
from app.core.metadata_utils import extract_metadata, extract_title
from app.core.text_utils import clean_whitespace, naive_summary
from app.core.url_utils import normalize_url
from app.core.validators import validate_html_length, validate_url
from app.models.extract_page import ExtractPageData

_ALLOWED_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}
_IMPORTANT_LINK_TOKENS = ("contact", "about", "pricing", "team", "careers")


class ExtractPageError(Exception):
    def __init__(self, *, code: str, message: str, status_code: int, retryable: bool):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(message)


async def fetch_page(url: str) -> tuple[str, str | None, str]:
    settings = get_settings()
    headers = {"User-Agent": settings.http_user_agent}

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";")[0].strip() or None
            if content_type and content_type not in _ALLOWED_CONTENT_TYPES:
                raise ExtractPageError(
                    code="UNSUPPORTED_CONTENT_TYPE",
                    message="Only HTML pages are supported.",
                    status_code=415,
                    retryable=False,
                )
            body = response.text
            if len(body.encode("utf-8")) > settings.http_max_response_bytes:
                raise ExtractPageError(
                    code="UPSTREAM_ERROR",
                    message="Response body exceeds configured size limit.",
                    status_code=502,
                    retryable=True,
                )
            return body, content_type, str(response.url)
    except ExtractPageError:
        raise
    except httpx.TimeoutException as exc:
        raise ExtractPageError(code="TIMEOUT", message="Upstream request timed out.", status_code=504, retryable=True) from exc
    except httpx.HTTPStatusError as exc:
        raise ExtractPageError(code="UPSTREAM_ERROR", message="Upstream server returned an error.", status_code=502, retryable=True) from exc
    except httpx.HTTPError as exc:
        raise ExtractPageError(code="FETCH_FAILED", message="Unable to fetch the requested URL.", status_code=502, retryable=True) from exc


def _pick_summary(*, metadata: dict, visible_text: str) -> str | None:
    description = metadata.get("description")
    if description:
        return clean_whitespace(str(description))

    paragraphs = [chunk.strip() for chunk in visible_text.split("\n\n") if chunk.strip()]
    if paragraphs:
        return clean_whitespace(paragraphs[0])[:320]

    summary = naive_summary(visible_text, max_sentences=2)
    return summary[:320] if summary else None


def _pick_important_links(links: list[dict]) -> list[str]:
    matches: list[str] = []
    for link in links:
        href = str(link.get("href", "")).strip()
        text = str(link.get("text", "")).strip().lower()
        lower_href = href.lower()
        if any(token in text or token in lower_href for token in _IMPORTANT_LINK_TOKENS):
            matches.append(href)
    seen = []
    for item in matches:
        if item and item not in seen:
            seen.append(item)
    return seen[:10]


def _build_excerpt(text: str) -> str | None:
    cleaned = clean_whitespace(text)
    if not cleaned:
        return None
    return cleaned[:500]


async def extract_page_from_url(url: str) -> ExtractPageData:
    try:
        validated_url = validate_url(url)
    except Exception as exc:
        raise ExtractPageError(code="INVALID_INPUT", message="A valid URL is required.", status_code=400, retryable=False) from exc

    html, _content_type, final_url = await fetch_page(validated_url)
    settings = get_settings()
    validate_html_length(html, settings.structured_web_max_html_chars)

    original_soup = strip_boilerplate(parse_html(html), preserve_forms=True)
    visible_text = extract_visible_text(original_soup)
    metadata = extract_metadata(original_soup)
    links = extract_links(original_soup, base_url=final_url, max_links=settings.structured_web_max_links)

    return ExtractPageData(
        url=normalize_url(validated_url),
        final_url=normalize_url(final_url),
        title=extract_title(original_soup),
        summary=_pick_summary(metadata=metadata, visible_text=visible_text),
        emails=extract_emails(visible_text),
        phone_numbers=extract_phone_numbers(visible_text),
        social_links=extract_social_media_links(original_soup, base_url=final_url),
        important_links=_pick_important_links(links),
        text_excerpt=_build_excerpt(visible_text),
    )
