from urllib.parse import urljoin, urlparse


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    return parsed._replace(scheme=scheme, netloc=netloc, path=path, fragment="").geturl()


def absolutize_url(base_url: str | None, href: str) -> str:
    return urljoin(base_url or "", href)


def is_allowed_link(href: str) -> bool:
    href = href.strip().lower()
    return not (
        href.startswith("javascript:")
        or href.startswith("mailto:")
        or href.startswith("tel:")
        or href.startswith("#")
    )
