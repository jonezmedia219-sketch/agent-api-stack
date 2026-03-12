from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str = ""
    source: str
    rank: int


class SearchResponseData(BaseModel):
    query: str
    results: list[SearchResultItem] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    count: int = 0
