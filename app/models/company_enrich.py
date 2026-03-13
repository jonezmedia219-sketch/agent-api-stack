from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanyEnrichRequest(BaseModel):
    domain: str = Field(..., min_length=1)


class CompanyEnrichBatchRequest(BaseModel):
    domains: list[str] = Field(..., min_length=1, max_length=10)

    @field_validator("domains")
    @classmethod
    def validate_domains(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("At least one domain is required.")
        if len(value) > 10:
            raise ValueError("A maximum of 10 domains is allowed per request.")
        return value


class CompanyEnrichSignals(BaseModel):
    has_contact_page: bool = False
    has_about_page: bool = False
    has_careers_page: bool = False
    has_pricing_page: bool = False
    has_api_docs: bool = False
    has_blog: bool = False
    has_login: bool = False
    has_signup: bool = False


class CompanyEnrichData(BaseModel):
    model_config = ConfigDict(extra="allow")

    domain: str
    normalized_url: str
    company_name: str | None = None
    summary: str | None = None
    industry: str | None = None
    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    social_links: list[str] = Field(default_factory=list)
    contact_page: str | None = None
    about_page: str | None = None
    careers_page: str | None = None
    pricing_page: str | None = None
    important_links: list[str] = Field(default_factory=list)
    addresses: list[str] = Field(default_factory=list)
    signals: CompanyEnrichSignals = Field(default_factory=CompanyEnrichSignals)
    pages_analyzed: list[str] = Field(default_factory=list)


class CompanyEnrichBatchItemError(BaseModel):
    code: str
    message: str
    retryable: bool


class CompanyEnrichBatchItem(BaseModel):
    domain: str
    ok: bool
    data: CompanyEnrichData | None = None
    error: CompanyEnrichBatchItemError | None = None


class CompanyEnrichBatchData(BaseModel):
    results: list[CompanyEnrichBatchItem] = Field(default_factory=list)
    count: int
    success_count: int
    error_count: int
