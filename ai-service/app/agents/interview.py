from pathlib import Path
from typing import Any

from agents import Agent as OpenAIAgent
from agents import OpenAIProvider, RunConfig, Runner
from openai import AsyncOpenAI

from app.agents.base import BaseAgent
from app.config.logging import get_logger
from app.config.settings import get_settings
from app.schemas.agents import AgentRunResponse, AgentStatus
from app.schemas.workflows import InterviewQuestionOutput

logger = get_logger(__name__)


class InterviewAgent(BaseAgent):
    async def run(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AgentRunResponse:
        return AgentRunResponse(
            run_id="",
            agent_name=self.config.name,
            status=AgentStatus.COMPLETED,
            output="Interview generation not yet implemented",
        )


class InterviewQuestionAgent(BaseAgent):
    async def run(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AgentRunResponse:
        settings = get_settings()
        prompt_path = Path(__file__).parent.parent / "prompts" / "interview.md"
        instructions = prompt_path.read_text()

        openai_client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
        provider = OpenAIProvider(openai_client=openai_client)
        run_config = RunConfig(
            model_provider=provider,
            model=settings.AGENT_DEFAULT_MODEL or settings.OPENROUTER_DEFAULT_MODEL,
            tracing_disabled=True,
        )

        openai_agent = OpenAIAgent(
            name="InterviewQuestionAgent",
            instructions=instructions,
            output_type=InterviewQuestionOutput,
        )

        logger.info("agent_execution_started", agent=self.config.name)

        result = await Runner.run(openai_agent, input=task, run_config=run_config)
        output: InterviewQuestionOutput = result.final_output

        logger.info("agent_execution_completed", agent=self.config.name)

        return AgentRunResponse(
            run_id="",
            agent_name=self.config.name,
            status=AgentStatus.COMPLETED,
            output=output.model_dump_json(),
        )
