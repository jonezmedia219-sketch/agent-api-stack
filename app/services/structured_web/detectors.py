from bs4 import BeautifulSoup


def detect_content_type(soup: BeautifulSoup, fetched_content_type: str | None = None) -> str:
    if fetched_content_type and "html" not in fetched_content_type:
        return fetched_content_type

    article_markers = [
        soup.find("article"),
        soup.find("meta", attrs={"property": "og:type", "content": "article"}),
        soup.find("time"),
    ]
    if any(article_markers):
        return "article"

    if soup.find("main") or soup.find("section"):
        return "webpage"

    return "unknown"
