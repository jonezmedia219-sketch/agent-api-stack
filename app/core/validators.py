from urllib.parse import urlparse

from app.exceptions import ValidationError


ALLOWED_SCHEMES = {"http", "https"}


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        raise ValidationError("A valid http or https URL is required.")
    return url


def validate_html_length(html: str, max_chars: int) -> str:
    if not html or not html.strip():
        raise ValidationError("HTML content cannot be empty.")
    if len(html) > max_chars:
        raise ValidationError(f"HTML content exceeds max length of {max_chars} characters.")
    return html
