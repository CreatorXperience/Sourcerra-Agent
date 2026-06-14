from datetime import datetime

from pydantic import BaseModel, Field


class EmailActivity(BaseModel):
    id: str
    candidate_id: str
    recruiter_id: str
    subject: str
    body: str
    sent_at: datetime | None = None
    created_at: datetime | None = None


class ListEmailHistoryRequest(BaseModel):
    candidate_id: str
    limit: int = 50


class ListEmailHistoryResponse(BaseModel):
    emails: list[EmailActivity] = Field(default_factory=list)
    total: int = 0


class SendEmailRequest(BaseModel):
    candidate_id: str
    subject: str
    body: str


class SendEmailResponse(BaseModel):
    email_id: str
    sent: bool = False
