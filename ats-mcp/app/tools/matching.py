"""
TODO: BACKEND_REQUIRED — Candidate matching tool adapters.

This tool requires backend endpoints that may not yet exist.
However, the backend already produces overallScore/jobFitScore/skillsScore/
experienceScore on each candidate record, so a basic implementation can
use ats_list_candidates + sort by overall_score without a dedicated endpoint.

Expected endpoint (future):
  POST /ai/match — dedicated matching endpoint
"""

from app.schemas.matching import MatchCandidatesResponse


async def ats_match_candidates_to_job(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Match candidates to a job using scores.
    
    The backend already produces overallScore, jobFitScore, skillsScore,
    and experienceScore on candidate records. Once the backend exposes a
    dedicated matching endpoint, replace this stub with a real implementation.
    A basic v1 can use ats_list_candidates filtered by job_id + sort by score.
    """
    return [{"type": "text", "text": str(MatchCandidatesResponse(job_id=arguments.get("job_id", "")))}], False
