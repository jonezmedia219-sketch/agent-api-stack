import httpx

from app.config import get_settings
from app.exceptions import FetchError


async def fetch_html(url: str) -> tuple[str, str | None]:
    settings = get_settings()
    headers = {"User-Agent": settings.http_user_agent}

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";")[0].strip() or None
            body = response.text
            if len(body.encode("utf-8")) > settings.http_max_response_bytes:
                raise FetchError("Response body exceeds configured size limit.")
            return body, content_type
    except httpx.HTTPError as exc:
        raise FetchError(str(exc)) from exc
