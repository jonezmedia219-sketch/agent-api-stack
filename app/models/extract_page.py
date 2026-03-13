from pydantic import BaseModel, ConfigDict, Field


class ExtractPageRequest(BaseModel):
    url: str = Field(..., min_length=1)


class ExtractPageData(BaseModel):
    model_config = ConfigDict(extra="allow")

    url: str
    final_url: str
    title: str | None = None
    summary: str | None = None
    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    social_links: list[str] = Field(default_factory=list)
    important_links: list[str] = Field(default_factory=list)
    text_excerpt: str | None = None
