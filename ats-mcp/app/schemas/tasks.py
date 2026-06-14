from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CandidateTaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class CandidateTask(BaseModel):
    id: str
    candidate_id: str
    recruiter_id: str
    company_id: str | None = None
    title: str
    description: str | None = None
    status: CandidateTaskStatus = CandidateTaskStatus.TODO
    due_date: datetime | None = None
    color: str | None = None
    label: str | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GetTasksRequest(BaseModel):
    candidate_id: str
    limit: int = 50


class ListTasksResponse(BaseModel):
    tasks: list[CandidateTask] = Field(default_factory=list)
    total: int = 0
