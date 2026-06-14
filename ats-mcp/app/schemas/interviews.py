from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InterviewEventKind(str, Enum):
    INTERVIEW = "INTERVIEW"
    BUSY = "BUSY"


class InterviewEventStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    RESCHEDULED = "RESCHEDULED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class InterviewEvent(BaseModel):
    id: str
    job_id: str | None = None
    candidate_id: str | None = None
    recruiter_id: str
    interviewer_id: str | None = None
    title: str = ""
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str = "UTC"
    status: InterviewEventStatus = InterviewEventStatus.PENDING
    kind: InterviewEventKind = InterviewEventKind.INTERVIEW
    meeting_url: str | None = None
    attendees: list[dict[str, Any]] = Field(default_factory=list)
    location: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InterviewAnalytics(BaseModel):
    total_interviews: int = 0
    time_to_schedule_hours: float | None = None
    reschedule_count: int = 0
    no_show_rate: float | None = None
    completion_rate: float | None = None


class ListInterviewsRequest(BaseModel):
    candidate_id: str | None = None
    job_id: str | None = None
    status: InterviewEventStatus | None = None
    limit: int = Field(default=50, ge=1, le=200)


class ListInterviewsResponse(BaseModel):
    interviews: list[InterviewEvent] = Field(default_factory=list)
    total: int = 0
