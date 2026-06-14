from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    candidate_id: str
    candidate_name: str | None = None
    job_id: str
    overall_score: float | None = None
    job_fit_score: float | None = None
    skills_score: float | None = None
    experience_score: float | None = None
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class MatchCandidatesRequest(BaseModel):
    job_id: str
    limit: int = Field(default=10, ge=1, le=50)


class MatchCandidatesResponse(BaseModel):
    job_id: str
    matches: list[MatchResult] = Field(default_factory=list)
    total: int = 0
