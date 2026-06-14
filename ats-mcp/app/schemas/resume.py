from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


class ProcessingJob(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    status: ProcessingStatus
    retry_count: int = 0
    max_retries: int = 3
    failure_reason: str | None = None
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None


class GetProcessingStatusRequest(BaseModel):
    candidate_id: str


class ProcessingStatusResponse(BaseModel):
    candidate_id: str
    status: ProcessingStatus | None = None
    processing_job: ProcessingJob | None = None


class RetryProcessingRequest(BaseModel):
    candidate_id: str


class RetryProcessingResponse(BaseModel):
    candidate_id: str
    requeued: bool = False


class ResumeSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=50)


class ResumeSearchResponse(BaseModel):
    candidates: list[dict] = Field(default_factory=list)
    total: int = 0
