from datetime import datetime

from pydantic import BaseModel, Field


class Comment(BaseModel):
    id: str
    content: str
    author_id: str
    candidate_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GetCommentsRequest(BaseModel):
    candidate_id: str
    limit: int = 50


class ListCommentsResponse(BaseModel):
    comments: list[Comment] = Field(default_factory=list)
    total: int = 0
