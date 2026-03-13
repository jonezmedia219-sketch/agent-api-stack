from urllib.parse import urlparse

from app.core.contact_utils import extract_social_media_links, pick_company_name
from app.core.html_utils import extract_headings, extract_links, extract_visible_text, parse_html, strip_boilerplate
from app.core.metadata_utils import extract_metadata, extract_title
from app.core.text_utils import clean_whitespace, dedupe_preserve_order, naive_summary
from app.core.url_utils import normalize_url
from app.models.company_enrich import CompanyEnrichData, CompanyEnrichSignals
from app.services.extract_page.service import ExtractPageError, fetch_page
from app.services.lead_extract.service import extract_leads_from_html
from app.services.structured_web.service import extract_from_html

_PAGE_PATTERNS = {
    "contact": ("contact", "contact-us", "get-in-touch", "support"),
    "about": ("about", "about-us", "our-story", "company"),
    "careers": ("careers", "career", "jobs", "join-us", "hiring"),
    "pricing": ("pricing", "plans", "plan", "subscriptions"),
}

_SIGNAL_PATTERNS = {
    "has_api_docs": ("api", "docs", "developers", "developer", "reference"),
    "has_blog": ("blog", "news", "resources", "articles"),
    "has_login": ("login", "log in", "signin", "sign in"),
    "has_signup": ("signup", "sign up", "register", "get started", "start free", "try for free"),
}

_INDUSTRY_KEYWORDS = {
    "saas": ("saas", "software", "platform", "automation", "api", "developer", "developers", "workflow"),
    "marketing": ("marketing", "growth", "seo", "advertising", "campaign", "lead generation"),
    "finance": ("fintech", "finance", "financial", "payments", "banking", "accounting"),
    "healthcare": ("healthcare", "health care", "medical", "patient", "clinic", "telehealth"),
    "ecommerce": ("ecommerce", "e-commerce", "online store", "shop", "retail", "checkout"),
    "recruiting": ("recruiting", "recruitment", "talent", "staffing", "hiring"),
    "education": ("education", "learning", "course", "courses", "training", "students"),
    "real_estate": ("real estate", "property", "properties", "brokerage", "homes"),
    "agency": ("agency", "studio", "creative", "branding", "design services"),
}

_MAX_DEEP_PAGES = 4
_ALLOWED_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}


class CompanyEnrichError(Exception):
    def __init__(self, *, code: str, message: str, status_code: int, retryable: bool):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(message)


def _normalize_domain(domain: str) -> tuple[str, str]:
    candidate = clean_whitespace(domain).lower()
    if not candidate:
        raise CompanyEnrichError(code="INVALID_INPUT", message="A valid domain is required.", status_code=400, retryable=False)

    if "://" in candidate:
        parsed = urlparse(candidate)
        hostname = parsed.netloc
    else:
        parsed = urlparse(f"https://{candidate}")
        hostname = parsed.netloc

    hostname = hostname.strip().lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]

    if not hostname or "." not in hostname or any(ch.isspace() for ch in hostname):
        raise CompanyEnrichError(code="INVALID_INPUT", message="A valid domain is required.", status_code=400, retryable=False)

    normalized_url = normalize_url(f"https://{hostname}")
    return hostname, normalized_url


def _pick_summary(*, metadata: dict, main_text: str) -> str | None:
    description = metadata.get("description")
    if description:
        return clean_whitespace(str(description))[:320]
    summary = naive_summary(main_text, max_sentences=2)
    return summary[:320] if summary else None


def _page_matches(link: dict, patterns: tuple[str, ...]) -> bool:
    href = str(link.get("href", "")).lower()
    text = clean_whitespace(str(link.get("text", ""))).lower()
    return any(token in href or token in text for token in patterns)


def _pick_named_page(links: list[dict], key: str) -> str | None:
    patterns = _PAGE_PATTERNS[key]
    for link in links:
        if _page_matches(link, patterns):
            href = str(link.get("href", "")).strip()
            if href:
                return href
    return None


def _infer_industry(*, title: str | None, metadata: dict, main_text: str) -> str | None:
    haystack = " ".join(filter(None, [title, metadata.get("description"), metadata.get("site_name"), main_text[:2000]])).lower()
    for industry, keywords in _INDUSTRY_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return industry
    return None


def _normalize_netloc(netloc: str) -> str:
    normalized = netloc.lower().strip()
    if normalized.startswith("www."):
        normalized = normalized[4:]
    return normalized


def _same_domain_links(links: list[dict], hostname: str) -> list[str]:
    results: list[str] = []
    for link in links:
        href = str(link.get("href", "")).strip()
        if not href:
            continue
        if _normalize_netloc(urlparse(href).netloc) == hostname:
            results.append(href)
    return dedupe_preserve_order(results)


def _detect_site_signals(links: list[dict]) -> dict[str, bool]:
    detected: dict[str, bool] = {}
    for signal_name, patterns in _SIGNAL_PATTERNS.items():
        detected[signal_name] = any(_page_matches(link, patterns) for link in links)
    return detected


def _merge_optional_text(*values: str | None) -> str | None:
    for value in values:
        if value:
            cleaned = clean_whitespace(value)
            if cleaned:
                return cleaned
    return None


def _merge_page_value(primary: str | None, secondary: str | None) -> str | None:
    return primary or secondary


def _normalize_address(value: str) -> str | None:
    cleaned = clean_whitespace(value)
    if not cleaned:
        return None
    if "\n\n" in cleaned:
        parts = [part.strip() for part in cleaned.split("\n\n") if part.strip()]
        if parts:
            cleaned = parts[-1]
    return cleaned


async def _fetch_company_page(url: str) -> tuple[str, str]:
    try:
        html, content_type, final_url = await fetch_page(url)
    except ExtractPageError as exc:
        raise CompanyEnrichError(code=exc.code, message=exc.message, status_code=exc.status_code, retryable=exc.retryable) from exc

    if content_type and content_type not in _ALLOWED_CONTENT_TYPES:
        raise CompanyEnrichError(code="UNSUPPORTED_CONTENT_TYPE", message="Only HTML pages are supported.", status_code=415, retryable=False)

    return html, final_url


def _analyze_page(*, html: str, source_url: str, hostname: str) -> dict:
    structured = extract_from_html(html, source_url=source_url)
    lead_data = extract_leads_from_html(html, source_url=source_url)

    raw_soup = parse_html(html)
    soup = strip_boilerplate(parse_html(html), preserve_forms=True)
    metadata = extract_metadata(soup)
    headings = [heading["text"] for heading in extract_headings(soup)]
    links = extract_links(raw_soup, base_url=source_url, max_links=50)

    company_name = lead_data.company_name or pick_company_name(
        title=extract_title(soup),
        site_name=metadata.get("site_name"),
        headings=headings,
    )

    contact_page = _pick_named_page(links, "contact")
    about_page = _pick_named_page(links, "about")
    careers_page = _pick_named_page(links, "careers")
    pricing_page = _pick_named_page(links, "pricing")
    important_links = dedupe_preserve_order(
        [
            *(page for page in [contact_page, about_page, careers_page, pricing_page] if page),
            *_same_domain_links(links, hostname),
        ]
    )[:10]

    return {
        "source_url": normalize_url(source_url),
        "structured": structured,
        "lead_data": lead_data,
        "company_name": company_name,
        "contact_page": contact_page,
        "about_page": about_page,
        "careers_page": careers_page,
        "pricing_page": pricing_page,
        "important_links": important_links,
        "site_signals": _detect_site_signals(links),
        "social_links": extract_social_media_links(raw_soup, base_url=source_url) or lead_data.social_media_links,
    }


def _build_company_enrich_data(*, domain: str, normalized_url: str, analyses: list[dict]) -> CompanyEnrichData:
    primary = analyses[0]
    all_structured = [analysis["structured"] for analysis in analyses]
    all_lead_data = [analysis["lead_data"] for analysis in analyses]

    emails = dedupe_preserve_order([item for lead in all_lead_data for item in lead.emails])
    phone_numbers = dedupe_preserve_order([item for lead in all_lead_data for item in lead.phone_numbers])
    social_links = dedupe_preserve_order([item for analysis in analyses for item in analysis["social_links"]])
    addresses = dedupe_preserve_order(
        [normalized for lead in all_lead_data for item in lead.addresses if (normalized := _normalize_address(item))]
    )
    important_links = dedupe_preserve_order([item for analysis in analyses for item in analysis["important_links"]])[:10]
    pages_analyzed = dedupe_preserve_order([analysis["source_url"] for analysis in analyses])

    contact_page = None
    about_page = None
    careers_page = None
    pricing_page = None
    for analysis in analyses:
        contact_page = _merge_page_value(contact_page, analysis["contact_page"])
        about_page = _merge_page_value(about_page, analysis["about_page"])
        careers_page = _merge_page_value(careers_page, analysis["careers_page"])
        pricing_page = _merge_page_value(pricing_page, analysis["pricing_page"])

    signal_values = {
        "has_contact_page": contact_page is not None,
        "has_about_page": about_page is not None,
        "has_careers_page": careers_page is not None,
        "has_pricing_page": pricing_page is not None,
        "has_api_docs": any(analysis["site_signals"]["has_api_docs"] for analysis in analyses),
        "has_blog": any(analysis["site_signals"]["has_blog"] for analysis in analyses),
        "has_login": any(analysis["site_signals"]["has_login"] for analysis in analyses),
        "has_signup": any(analysis["site_signals"]["has_signup"] for analysis in analyses),
    }

    return CompanyEnrichData(
        domain=domain,
        normalized_url=normalized_url,
        company_name=_merge_optional_text(*(analysis["company_name"] for analysis in analyses)),
        summary=_merge_optional_text(*(_pick_summary(metadata=structured.metadata, main_text=structured.main_text) for structured in all_structured)),
        industry=_merge_optional_text(*(_infer_industry(title=structured.title, metadata=structured.metadata, main_text=structured.main_text) for structured in all_structured)),
        emails=emails,
        phone_numbers=phone_numbers,
        social_links=social_links,
        contact_page=contact_page,
        about_page=about_page,
        careers_page=careers_page,
        pricing_page=pricing_page,
        important_links=important_links,
        addresses=addresses,
        signals=CompanyEnrichSignals(**signal_values),
        pages_analyzed=pages_analyzed,
    )


async def enrich_company_from_domain(domain: str) -> CompanyEnrichData:
    hostname, normalized_url = _normalize_domain(domain)
    html, final_url = await _fetch_company_page(normalized_url)
    homepage_analysis = _analyze_page(html=html, source_url=final_url, hostname=hostname)
    return _build_company_enrich_data(domain=hostname, normalized_url=normalize_url(final_url), analyses=[homepage_analysis])


async def enrich_company_from_domain_deep(domain: str) -> CompanyEnrichData:
    hostname, normalized_url = _normalize_domain(domain)
    html, final_url = await _fetch_company_page(normalized_url)
    homepage_analysis = _analyze_page(html=html, source_url=final_url, hostname=hostname)

    candidate_pages = dedupe_preserve_order(
        [
            page
            for page in [
                homepage_analysis["contact_page"],
                homepage_analysis["about_page"],
                homepage_analysis["careers_page"],
                homepage_analysis["pricing_page"],
            ]
            if page and _normalize_netloc(urlparse(page).netloc) == hostname
        ]
    )[:_MAX_DEEP_PAGES]

    analyses = [homepage_analysis]
    for page_url in candidate_pages:
        if normalize_url(page_url) == homepage_analysis["source_url"]:
            continue
        page_html, fetched_final_url = await _fetch_company_page(page_url)
        if _normalize_netloc(urlparse(fetched_final_url).netloc) != hostname:
            continue
        analyses.append(_analyze_page(html=page_html, source_url=fetched_final_url, hostname=hostname))

    return _build_company_enrich_data(domain=hostname, normalized_url=normalize_url(final_url), analyses=analyses)
