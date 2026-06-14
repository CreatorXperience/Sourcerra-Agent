from typing import Any

from app.toolkits.base import BaseToolkit


class ATSToolkit(BaseToolkit):
    @classmethod
    def tools(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "search_candidates",
                "description": "Search for candidates by query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Max results"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_candidate",
                "description": "Get candidate details by ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "candidate_id": {"type": "string"},
                    },
                    "required": ["candidate_id"],
                },
            },
            {
                "name": "get_job",
                "description": "Get job details by ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string"},
                    },
                    "required": ["job_id"],
                },
            },
            {
                "name": "list_jobs",
                "description": "List all jobs, optionally filtered by status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "Filter by status"},
                    },
                },
            },
        ]
