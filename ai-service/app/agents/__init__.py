from app.agents.candidate_matching import CandidateMatchingAgent
from app.agents.candidate_summary import CandidateSummaryAgent
from app.agents.hiring_recommendation import HiringRecommendationAgent
from app.agents.interview import InterviewAgent, InterviewQuestionAgent
from app.agents.interview_debrief import InterviewDebriefAgent
from app.agents.outreach import OutreachGenerationAgent as OutreachAgent
from app.agents.recruiter_copilot import RecruiterCopilotAgent
from app.agents.registry import AgentRegistry, get_registry
from app.agents.resume_analysis import ResumeAnalysisAgent
from app.schemas.agents import AgentConfig, AgentType


def register_default_agents(registry: AgentRegistry | None = None) -> AgentRegistry:
    reg = registry or get_registry()

    reg.register(CandidateMatchingAgent(
        AgentConfig(name="candidate-matcher", agent_type=AgentType.CANDIDATE_MATCHING),
    ))
    reg.register(ResumeAnalysisAgent(
        AgentConfig(name="resume-analyst", agent_type=AgentType.RESUME_ANALYSIS),
    ))
    reg.register(OutreachAgent(
        AgentConfig(name="outreach-specialist", agent_type=AgentType.OUTREACH),
    ))
    reg.register(InterviewAgent(
        AgentConfig(name="interview-designer", agent_type=AgentType.INTERVIEW),
    ))
    reg.register(InterviewQuestionAgent(
        AgentConfig(name="interview-question-generator", agent_type=AgentType.INTERVIEW_QUESTION),
    ))
    reg.register(CandidateSummaryAgent(
        AgentConfig(name="candidate-summarizer", agent_type=AgentType.CANDIDATE_SUMMARY),
    ))
    reg.register(InterviewDebriefAgent(
        AgentConfig(name="interview-debrief", agent_type=AgentType.GENERAL),
    ))
    reg.register(HiringRecommendationAgent(
        AgentConfig(name="hiring-recommendation", agent_type=AgentType.GENERAL),
    ))
    reg.register(RecruiterCopilotAgent(
        AgentConfig(name="recruiter-copilot", agent_type=AgentType.GENERAL),
    ))

    return reg


__all__ = [
    "AgentRegistry",
    "get_registry",
    "register_default_agents",
    "CandidateMatchingAgent",
    "CandidateSummaryAgent",
    "ResumeAnalysisAgent",
    "OutreachAgent",
    "InterviewAgent",
    "InterviewQuestionAgent",
    "InterviewDebriefAgent",
    "HiringRecommendationAgent",
    "RecruiterCopilotAgent",
]
