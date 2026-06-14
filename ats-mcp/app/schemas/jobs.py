from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class JobRequirement(BaseModel):
    label: str
    field_type: str = ""
    required: bool = False
    options: list[str] = Field(default_factory=list)
    order: int = 0


class Job(BaseModel):
    id: str
    title: str
    description: str | None = None
    company_id: str
    automation_status: bool = False
    requirements: list[JobRequirement] = Field(default_factory=list)
    candidate_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GetJobRequest(BaseModel):
    job_id: str


class ListJobsRequest(BaseModel):
    pass


class ListJobsResponse(BaseModel):
    jobs: list[Job] = Field(default_factory=list)
    total: int = 0
