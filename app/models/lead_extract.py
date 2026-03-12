from pydantic import BaseModel, HttpUrl, model_validator


class LeadExtractRequest(BaseModel):
    url: HttpUrl | None = None
    html: str | None = None
    source_url: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_source(self):
        if not self.url and not self.html:
            raise ValueError("Either url or html must be provided.")
        if self.url and self.html:
            raise ValueError("Provide either url or html, not both.")
        if self.html is not None and not self.html.strip():
            raise ValueError("HTML content cannot be empty.")
        return self


class LeadExtractData(BaseModel):
    source_url: str | None = None
    emails: list[str] = []
    phone_numbers: list[str] = []
    social_media_links: list[str] = []
    company_name: str | None = None
    contact_forms_detected: bool = False
    addresses: list[str] = []
