from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    app.state.payment_shadow_mode = True
    app.state.payment_hard_enforcement = False
    return TestClient(app)


@pytest.fixture()
def article_html() -> str:
    fixture_path = Path(__file__).parent / "fixtures" / "article.html"
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture()
def company_contact_html() -> str:
    fixture_path = Path(__file__).parent / "fixtures" / "company_contact.html"
    return fixture_path.read_text(encoding="utf-8")
