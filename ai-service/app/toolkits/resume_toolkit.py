from typing import Any

from app.toolkits.base import BaseToolkit


class ResumeToolkit(BaseToolkit):
    @classmethod
    def tools(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_resume",
                "description": "Get resume by ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resume_id": {"type": "string"},
                    },
                    "required": ["resume_id"],
                },
            },
            {
                "name": "extract_resume_text",
                "description": "Extract full text from a resume",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resume_id": {"type": "string"},
                    },
                    "required": ["resume_id"],
                },
            },
            {
                "name": "get_resume_skills",
                "description": "Extract skills from a resume",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resume_id": {"type": "string"},
                    },
                    "required": ["resume_id"],
                },
            },
            {
                "name": "get_resume_experience",
                "description": "Extract work experience from a resume",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resume_id": {"type": "string"},
                    },
                    "required": ["resume_id"],
                },
            },
        ]
