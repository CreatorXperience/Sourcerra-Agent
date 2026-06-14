from app.tools.analytics import (
    ats_get_analytics_dashboard,
    ats_get_analytics_funnel,
    ats_get_analytics_hiring_speed,
    ats_get_analytics_pipeline_health,
    ats_get_analytics_source,
)
from app.tools.candidates import ats_get_candidate, ats_list_candidates
from app.tools.comments import ats_get_candidate_comments
from app.tools.interviews import (
    ats_cancel_interview,
    ats_complete_interview,
    ats_get_interview,
    ats_list_interviews,
    ats_reschedule_interview,
    ats_schedule_interview,
)
from app.tools.jobs import ats_get_job, ats_list_jobs
from app.tools.matching import ats_match_candidates_to_job
from app.tools.outreach import ats_get_email_history, ats_send_email
from app.tools.registry import ToolRegistry, get_registry
from app.tools.resume import ats_get_resume_processing_status, ats_retry_resume_processing
from app.tools.tasks import ats_get_candidate_tasks


def register_all_tools(registry: ToolRegistry | None = None) -> ToolRegistry:
    reg = registry or get_registry()

    # ===== PHASE 1: IMPLEMENTED =====
    # These tools have full BackendClient integration.

    reg.register(
        name="ats_get_candidate",
        description="Retrieve a candidate's full profile by their unique identifier, including scores, skills, stage, and linked URLs",
        handler=ats_get_candidate,
        input_schema={
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": "string",
                    "description": "Unique identifier of the candidate",
                },
            },
            "required": ["candidate_id"],
        },
    )

    reg.register(
        name="ats_list_candidates",
        description="List candidates with optional filters for stage, job, recommendation, and text search. No pagination — returns first page only",
        handler=ats_list_candidates,
        input_schema={
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Text search across candidate name, email, and location",
                },
                "stage": {
                    "type": "string",
                    "description": "Filter by pipeline stage: APPLIED, SCREENED, SHORTLISTED, INTERVIEW, INTERVIEW_COMPLETED, OFFER, HIRED, REJECTED",
                },
                "job_id": {
                    "type": "string",
                    "description": "Filter by job identifier",
                },
                "recommendation": {
                    "type": "string",
                    "description": "Filter by recommendation: strong_yes, yes, maybe, no",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of candidates to return (default 50, max 200)",
                    "default": 50,
                },
            },
        },
    )

    reg.register(
        name="ats_get_job",
        description="Retrieve a job's full details including requirements and candidate count",
        handler=ats_get_job,
        input_schema={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Unique identifier of the job",
                },
            },
            "required": ["job_id"],
        },
    )

    reg.register(
        name="ats_list_jobs",
        description="List all jobs for the current company. No pagination or filters supported",
        handler=ats_list_jobs,
        input_schema={
            "type": "object",
            "properties": {},
        },
    )

    reg.register(
        name="ats_get_candidate_comments",
        description="Retrieve all comments for a given candidate",
        handler=ats_get_candidate_comments,
        input_schema={
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": "string",
                    "description": "Unique identifier of the candidate",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum comments to return",
                    "default": 50,
                },
            },
            "required": ["candidate_id"],
        },
    )

    reg.register(
        name="ats_get_candidate_tasks",
        description="Retrieve all tasks for a given candidate",
        handler=ats_get_candidate_tasks,
        input_schema={
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": "string",
                    "description": "Unique identifier of the candidate",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum tasks to return",
                    "default": 50,
                },
            },
            "required": ["candidate_id"],
        },
    )

    # ===== PHASE 2: BACKEND_REQUIRED =====
    # These tools have interface definitions and response schemas but
    # require backend endpoints. They return structured "not implemented"
    # responses until the backend is ready.

    reg.register(
        name="ats_list_interviews",
        description="[BACKEND REQUIRED] List interviews with optional filters for candidate, job, and status",
        handler=ats_list_interviews,
        input_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "Filter by candidate"},
                "job_id": {"type": "string", "description": "Filter by job"},
                "status": {"type": "string", "description": "Filter by status: DRAFT, PENDING, CONFIRMED, RESCHEDULED, CANCELLED, COMPLETED, NO_SHOW"},
                "limit": {"type": "integer", "description": "Max results", "default": 50},
            },
        },
    )

    reg.register(
        name="ats_get_interview",
        description="[BACKEND REQUIRED] Get interview details by ID",
        handler=ats_get_interview,
        input_schema={
            "type": "object",
            "properties": {
                "interview_id": {"type": "string", "description": "Unique interview identifier"},
            },
            "required": ["interview_id"],
        },
    )

    reg.register(
        name="ats_schedule_interview",
        description="[BACKEND REQUIRED] Schedule a new interview with calendar sync and notifications",
        handler=ats_schedule_interview,
        input_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "Candidate identifier"},
                "job_id": {"type": "string", "description": "Job identifier"},
                "recruiter_id": {"type": "string", "description": "Recruiter conducting the interview"},
                "start_time": {"type": "string", "description": "ISO 8601 start time"},
                "end_time": {"type": "string", "description": "ISO 8601 end time"},
                "title": {"type": "string", "description": "Interview title"},
            },
            "required": ["candidate_id", "job_id", "recruiter_id", "start_time", "end_time"],
        },
    )

    reg.register(
        name="ats_reschedule_interview",
        description="[BACKEND REQUIRED] Reschedule an existing interview",
        handler=ats_reschedule_interview,
        input_schema={
            "type": "object",
            "properties": {
                "interview_id": {"type": "string", "description": "Interview identifier"},
                "start_time": {"type": "string", "description": "New ISO 8601 start time"},
                "end_time": {"type": "string", "description": "New ISO 8601 end time"},
            },
            "required": ["interview_id", "start_time", "end_time"],
        },
    )

    reg.register(
        name="ats_cancel_interview",
        description="[BACKEND REQUIRED] Cancel an interview and sync to calendar",
        handler=ats_cancel_interview,
        input_schema={
            "type": "object",
            "properties": {
                "interview_id": {"type": "string", "description": "Interview identifier"},
            },
            "required": ["interview_id"],
        },
    )

    reg.register(
        name="ats_complete_interview",
        description="[BACKEND REQUIRED] Mark interview as completed and advance candidate stage",
        handler=ats_complete_interview,
        input_schema={
            "type": "object",
            "properties": {
                "interview_id": {"type": "string", "description": "Interview identifier"},
            },
            "required": ["interview_id"],
        },
    )

    reg.register(
        name="ats_get_email_history",
        description="[BACKEND REQUIRED] Get email history for a candidate",
        handler=ats_get_email_history,
        input_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "Candidate identifier"},
                "limit": {"type": "integer", "description": "Max emails", "default": 50},
            },
            "required": ["candidate_id"],
        },
    )

    reg.register(
        name="ats_send_email",
        description="[BACKEND REQUIRED] Send an email to a candidate via connected Gmail",
        handler=ats_send_email,
        input_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "Candidate identifier"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body"},
            },
            "required": ["candidate_id", "subject", "body"],
        },
    )

    reg.register(
        name="ats_get_resume_processing_status",
        description="[BACKEND REQUIRED] Get AI processing status for a candidate's resume",
        handler=ats_get_resume_processing_status,
        input_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "Candidate identifier"},
            },
            "required": ["candidate_id"],
        },
    )

    reg.register(
        name="ats_retry_resume_processing",
        description="[BACKEND REQUIRED] Retry failed resume processing for a candidate",
        handler=ats_retry_resume_processing,
        input_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "Candidate identifier"},
            },
            "required": ["candidate_id"],
        },
    )

    reg.register(
        name="ats_match_candidates_to_job",
        description="[BACKEND REQUIRED] Match candidates to a job using existing scores (overallScore, jobFitScore, skillsScore, experienceScore). The backend already produces these scores — v1 can use ats_list_candidates + sort by score",
        handler=ats_match_candidates_to_job,
        input_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job identifier"},
                "limit": {"type": "integer", "description": "Max candidates to return", "default": 10},
            },
            "required": ["job_id"],
        },
    )

    reg.register(
        name="ats_get_analytics_funnel",
        description="[BACKEND REQUIRED] Get hiring funnel conversion rates",
        handler=ats_get_analytics_funnel,
        input_schema={
            "type": "object",
            "properties": {},
        },
    )

    reg.register(
        name="ats_get_analytics_hiring_speed",
        description="[BACKEND REQUIRED] Get time-to-fill and time-to-hire metrics",
        handler=ats_get_analytics_hiring_speed,
        input_schema={
            "type": "object",
            "properties": {},
        },
    )

    reg.register(
        name="ats_get_analytics_source",
        description="[BACKEND REQUIRED] Get candidate source effectiveness",
        handler=ats_get_analytics_source,
        input_schema={
            "type": "object",
            "properties": {},
        },
    )

    reg.register(
        name="ats_get_analytics_pipeline_health",
        description="[BACKEND REQUIRED] Get pipeline stage health with aging metrics",
        handler=ats_get_analytics_pipeline_health,
        input_schema={
            "type": "object",
            "properties": {},
        },
    )

    reg.register(
        name="ats_get_analytics_dashboard",
        description="[BACKEND REQUIRED] Get composite hiring dashboard with key metrics",
        handler=ats_get_analytics_dashboard,
        input_schema={
            "type": "object",
            "properties": {},
        },
    )

    return reg
