from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CandidateStage(str, Enum):
    APPLIED = "APPLIED"
    SCREENED = "SCREENED"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW = "INTERVIEW"
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED"
    OFFER = "OFFER"
    HIRED = "HIRED"
    REJECTED = "REJECTED"


class CandidateSource(str, Enum):
    CAREER_PAGE = "CAREER_PAGE"
    LINKEDIN = "LINKEDIN"
    INDEED = "INDEED"
    REFERRAL = "REFERRAL"
    AGENCY = "AGENCY"
    IMPORTED = "IMPORTED"
    MANUAL = "MANUAL"


class AiStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


class RecommendationValue(str, Enum):
    STRONG_YES = "strong_yes"
    YES = "yes"
    MAYBE = "maybe"
    NO = "no"


class Candidate(BaseModel):
    id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    skills: list[str] = Field(default_factory=list)
    seniority: str | None = None
    last_role: str | None = None
    years_of_experience: int | None = None
    education: str | None = None
    stage: CandidateStage | None = None
    source: CandidateSource | None = None
    overall_score: float | None = None
    job_fit_score: float | None = None
    skills_score: float | None = None
    experience_score: float | None = None
    top_skills_match: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendation: RecommendationValue | None = None
    summary: str | None = None
    resume_url: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    assigned_to_id: str | None = None
    job_id: str | None = None
    company_id: str | None = None
    ai_status: AiStatus | None = None
    is_top_candidate: bool = False
    applied_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GetCandidateRequest(BaseModel):
    candidate_id: str


class ListCandidatesRequest(BaseModel):
    search: str | None = None
    stage: CandidateStage | None = None
    job_id: str | None = None
    recommendation: RecommendationValue | None = None
    limit: int = Field(default=50, ge=1, le=200)


class ListCandidatesResponse(BaseModel):
    candidates: list[Candidate] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
