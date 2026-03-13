from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryStoreRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    scope: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    scope: str | None = None


class MemoryDeleteRequest(BaseModel):
    memory_id: str = Field(..., min_length=1)


class MemoryRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    memory_id: str
    agent_id: str
    scope: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class MemorySearchResult(BaseModel):
    memory_id: str
    content: str
    scope: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float
    created_at: str


class MemorySearchData(BaseModel):
    results: list[MemorySearchResult] = Field(default_factory=list)


class MemoryDeleteData(BaseModel):
    deleted: bool
    memory_id: str
