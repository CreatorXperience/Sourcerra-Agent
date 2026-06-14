from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    CANDIDATE_MATCHING = "candidate_matching"
    RESUME_ANALYSIS = "resume_analysis"
    OUTREACH = "outreach"
    INTERVIEW = "interview"
    INTERVIEW_QUESTION = "interview_question"
    CANDIDATE_SUMMARY = "candidate_summary"
    GENERAL = "general"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    COMPLETED = "completed"


class AgentConfig(BaseModel):
    name: str
    agent_type: AgentType
    model: str = ""
    instructions: str = ""
    max_iterations: int = 10
    enable_handoffs: bool = True
    enable_guardrails: bool = True


class AgentRunRequest(BaseModel):
    agent_name: str
    task: str
    context: dict = {}
    thread_id: str | None = None


class AgentRunResponse(BaseModel):
    run_id: str
    agent_name: str
    status: AgentStatus
    output: str | None = None
    error: str | None = None
    tool_calls: int = 0
    total_duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentMetadata(BaseModel):
    name: str
    type: AgentType
    status: AgentStatus
    model: str
    description: str = ""
