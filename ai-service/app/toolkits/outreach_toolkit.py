from typing import Any

from app.toolkits.base import BaseToolkit


class OutreachToolkit(BaseToolkit):
    @classmethod
    def tools(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_email_templates",
                "description": "Get available email templates",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "campaign_id": {"type": "string", "description": "Filter by campaign"},
                    },
                },
            },
            {
                "name": "send_outreach_email",
                "description": "Send an outreach email to a candidate",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "candidate_id": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                        "template_id": {"type": "string", "description": "Optional template ID"},
                    },
                    "required": ["candidate_id", "subject", "body"],
                },
            },
            {
                "name": "schedule_follow_up",
                "description": "Schedule a follow-up for a candidate",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "candidate_id": {"type": "string"},
                        "days": {"type": "integer", "description": "Days until follow-up"},
                    },
                    "required": ["candidate_id", "days"],
                },
            },
        ]
