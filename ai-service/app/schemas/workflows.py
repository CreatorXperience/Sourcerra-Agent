from pydantic import BaseModel, Field


class CandidateMatchRequest(BaseModel):
    job_id: str
    limit: int = Field(default=10, ge=1, le=50)


class CandidateResult(BaseModel):
    candidate_id: str
    candidate_name: str
    overall_score: float | None = None
    job_fit_score: float | None = None
    skills_score: float | None = None
    experience_score: float | None = None
    ranking: int
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    explanation: str


class CandidateMatchOutput(BaseModel):
    job_id: str
    job_title: str
    top_candidates: list[CandidateResult]


class ResumeAnalysisRequest(BaseModel):
    resume_id: str
    include_raw_text: bool = False


class ResumeAnalysisResponse(BaseModel):
    resume_id: str
    skills: list[str] = []
    experience: list[dict] = []
    summary: str = ""


class InterviewGenerationRequest(BaseModel):
    job_id: str
    candidate_id: str | None = None
    question_count: int = 5


class InterviewGenerationResponse(BaseModel):
    job_id: str
    candidate_id: str | None = None
    questions: list[dict] = []
    evaluation_criteria: list[dict] = []


class OutreachGenerationRequest(BaseModel):
    candidate_id: str
    job_id: str


class OutreachGenerationOutput(BaseModel):
    candidate_id: str
    job_id: str
    candidate_name: str
    job_title: str
    subject: str
    email_body: str
    linkedin_message: str
    short_message: str


class CandidateSummaryRequest(BaseModel):
    candidate_id: str


class CandidateSummaryOutput(BaseModel):
    candidate_name: str
    overview: str
    recruiter_observations: list[str]
    open_action_items: list[str]
    recommended_next_action: str


class InterviewQuestionRequest(BaseModel):
    candidate_id: str
    job_id: str


class InterviewQuestion(BaseModel):
    question: str
    type: str
    focus_area: str
    rationale: str


class InterviewQuestionOutput(BaseModel):
    candidate_id: str
    job_id: str
    job_title: str
    technical_questions: list[InterviewQuestion] = Field(default_factory=list)
    behavioral_questions: list[InterviewQuestion] = Field(default_factory=list)
    follow_up_questions: list[InterviewQuestion] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)


class InterviewDebriefRequest(BaseModel):
    candidate_id: str
    job_id: str


class InterviewDebriefOutput(BaseModel):
    candidate_id: str
    job_id: str
    interview_summary: str
    validated_strengths: list[str] = Field(default_factory=list)
    identified_concerns: list[str] = Field(default_factory=list)
    further_evaluation_areas: list[str] = Field(default_factory=list)
    overall_assessment: str
    recommended_next_step: str


class HiringRecommendationRequest(BaseModel):
    candidate_id: str


class HiringRecommendationOutput(BaseModel):
    candidate_id: str
    candidate_name: str
    candidate_summary: str
    supporting_evidence: list[str] = Field(default_factory=list)
    caution_evidence: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recruiter_recommendation: str
    confidence_level: str


class RecruiterCopilotRequest(BaseModel):
    candidate_id: str
    job_id: str | None = None


class RecruiterCopilotSynthesis(BaseModel):
    candidate_id: str
    executive_summary: str
    key_strengths: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    recommended_next_step: str


class RecruiterCopilotOutput(BaseModel):
    candidate_id: str
    executive_summary: str
    candidate_overview: dict | None = None
    interview_assessment: dict | None = None
    hiring_recommendation: dict | None = None
    key_strengths: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    recommended_next_step: str
