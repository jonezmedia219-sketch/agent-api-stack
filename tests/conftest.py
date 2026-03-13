from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.rate_limit import RateLimitMiddleware


def _reset_rate_limit_buckets() -> None:
    current = getattr(app, "middleware_stack", None)
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, RateLimitMiddleware):
            current._buckets.clear()
            return
        current = getattr(current, "app", None)


@pytest.fixture()
def client() -> TestClient:
    app.state.payment_shadow_mode = True
    app.state.payment_hard_enforcement = False
    app.state.payment_verifier = "stub"
    client = TestClient(app)
    _reset_rate_limit_buckets()
    return client


@pytest.fixture()
def article_html() -> str:
    fixture_path = Path(__file__).parent / "fixtures" / "article.html"
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture()
def company_contact_html() -> str:
    fixture_path = Path(__file__).parent / "fixtures" / "company_contact.html"
    return fixture_path.read_text(encoding="utf-8")
