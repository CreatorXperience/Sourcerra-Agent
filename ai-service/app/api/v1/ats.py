from fastapi import APIRouter, Request

from app.schemas.agents import AgentRunResponse, AgentStatus
from app.schemas.workflows import (
    CandidateMatchRequest,
    CandidateSummaryRequest,
    HiringRecommendationRequest,
    InterviewDebriefRequest,
    InterviewGenerationRequest,
    InterviewQuestionRequest,
    OutreachGenerationRequest,
    RecruiterCopilotRequest,
    ResumeAnalysisRequest,
)
from app.workflows.candidate_summary import CandidateSummaryWorkflow
from app.workflows.hiring_recommendation import HiringRecommendationWorkflow
from app.workflows.interview_debrief import InterviewDebriefWorkflow
from app.workflows.interview_questions import InterviewQuestionWorkflow
from app.workflows.match_candidates import MatchCandidatesWorkflow
from app.workflows.outreach import OutreachGenerationWorkflow
from app.workflows.recruiter_copilot import RecruiterCopilotWorkflow

router = APIRouter()


@router.post("/candidate-match", response_model=AgentRunResponse)
async def candidate_match(
    request: CandidateMatchRequest,
    fastapi_request: Request,
) -> AgentRunResponse:
    mcp_manager = getattr(fastapi_request.app.state, "mcp_manager", None)
    workflow = MatchCandidatesWorkflow()
    return await workflow.execute(
        job_id=request.job_id,
        limit=request.limit,
        mcp_manager=mcp_manager,
    )


@router.post("/resume-analysis", response_model=AgentRunResponse)
async def resume_analysis(
    request: ResumeAnalysisRequest,
) -> AgentRunResponse:
    from app.agents.registry import get_registry
    agent = get_registry().get("resume-analyst")
    if not agent:
        return AgentRunResponse(
            run_id="", agent_name="resume-analysis", status=AgentStatus.ERROR,
            error="Resume analyst agent not found",
        )
    return await agent.run("Analyze resume", request.model_dump())


@router.post("/generate-outreach", response_model=AgentRunResponse)
async def generate_outreach(
    request: OutreachGenerationRequest,
    fastapi_request: Request,
) -> AgentRunResponse:
    mcp_manager = getattr(fastapi_request.app.state, "mcp_manager", None)
    workflow = OutreachGenerationWorkflow()
    return await workflow.execute(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        mcp_manager=mcp_manager,
    )


@router.post("/generate-interview", response_model=AgentRunResponse)
async def generate_interview(
    request: InterviewGenerationRequest,
) -> AgentRunResponse:
    from app.agents.registry import get_registry
    agent = get_registry().get("interview-designer")
    if not agent:
        return AgentRunResponse(
            run_id="", agent_name="interview", status=AgentStatus.ERROR,
            error="Interview agent not found",
        )
    return await agent.run("Generate interview plan", request.model_dump())


@router.post("/candidate-summary", response_model=AgentRunResponse)
async def candidate_summary(
    request: CandidateSummaryRequest,
    fastapi_request: Request,
) -> AgentRunResponse:
    mcp_manager = getattr(fastapi_request.app.state, "mcp_manager", None)
    workflow = CandidateSummaryWorkflow()
    return await workflow.execute(
        candidate_id=request.candidate_id,
        mcp_manager=mcp_manager,
    )


@router.post("/generate-interview-questions", response_model=AgentRunResponse)
async def generate_interview_questions(
    request: InterviewQuestionRequest,
    fastapi_request: Request,
) -> AgentRunResponse:
    mcp_manager = getattr(fastapi_request.app.state, "mcp_manager", None)
    workflow = InterviewQuestionWorkflow()
    return await workflow.execute(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        mcp_manager=mcp_manager,
    )


@router.post("/interview-debrief", response_model=AgentRunResponse)
async def interview_debrief(
    request: InterviewDebriefRequest,
    fastapi_request: Request,
) -> AgentRunResponse:
    mcp_manager = getattr(fastapi_request.app.state, "mcp_manager", None)
    workflow = InterviewDebriefWorkflow()
    return await workflow.execute(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        mcp_manager=mcp_manager,
    )


@router.post("/hiring-recommendation", response_model=AgentRunResponse)
async def hiring_recommendation(
    request: HiringRecommendationRequest,
    fastapi_request: Request,
) -> AgentRunResponse:
    mcp_manager = getattr(fastapi_request.app.state, "mcp_manager", None)
    workflow = HiringRecommendationWorkflow()
    return await workflow.execute(
        candidate_id=request.candidate_id,
        mcp_manager=mcp_manager,
    )


@router.post("/recruiter-copilot", response_model=AgentRunResponse)
async def recruiter_copilot(
    request: RecruiterCopilotRequest,
    fastapi_request: Request,
) -> AgentRunResponse:
    mcp_manager = getattr(fastapi_request.app.state, "mcp_manager", None)
    workflow = RecruiterCopilotWorkflow()
    return await workflow.execute(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        mcp_manager=mcp_manager,
    )
