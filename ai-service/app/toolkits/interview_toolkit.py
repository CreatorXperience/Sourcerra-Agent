from typing import Any

from app.toolkits.base import BaseToolkit


class InterviewToolkit(BaseToolkit):
    @classmethod
    def tools(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_interview_templates",
                "description": "Get available interview templates",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string", "description": "Filter by job"},
                    },
                },
            },
            {
                "name": "generate_interview_questions",
                "description": "Generate interview questions for a job",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string"},
                        "candidate_id": {"type": "string", "description": "Optional candidate for personalization"},
                        "count": {"type": "integer", "description": "Number of questions"},
                    },
                    "required": ["job_id"],
                },
            },
            {
                "name": "schedule_interview",
                "description": "Schedule an interview",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "application_id": {"type": "string"},
                        "candidate_id": {"type": "string"},
                        "job_id": {"type": "string"},
                        "proposed_times": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["application_id", "candidate_id", "job_id"],
                },
            },
        ]
