from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class StructuredWebExtractRequest(BaseModel):
    url: HttpUrl


class StructuredWebExtractHTMLRequest(BaseModel):
    html: str = Field(..., min_length=1)
    source_url: HttpUrl | None = None

    @field_validator("html")
    @classmethod
    def strip_html(cls, value: str) -> str:
        return value.strip()


class HeadingItem(BaseModel):
    level: int
    text: str


class LinkItem(BaseModel):
    text: str = ""
    href: str


class StructuredWebData(BaseModel):
    model_config = ConfigDict(extra="allow")

    url: str | None = None
    content_type: str
    title: str | None = None
    author: str | None = None
    published_date: str | None = None
    summary: str | None = None
    main_text: str
    headings: list[HeadingItem] = Field(default_factory=list)
    links: list[LinkItem] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
