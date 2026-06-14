from app.agents import register_default_agents
from app.agents.registry import AgentRegistry, get_registry
from app.schemas.agents import AgentType


def test_agent_registry_singleton() -> None:
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2


def test_agent_registry_empty() -> None:
    registry = AgentRegistry()
    assert registry.count == 0
    assert registry.list_metadata() == []


def test_default_agents_registered() -> None:
    registry = AgentRegistry()
    register_default_agents(registry)
    assert registry.count == 9
    names = {m.name for m in registry.list_metadata()}
    assert names == {
        "candidate-matcher", "resume-analyst", "outreach-specialist",
        "interview-designer", "candidate-summarizer",
        "interview-question-generator", "interview-debrief",
        "hiring-recommendation", "recruiter-copilot",
    }


def test_agent_registry_get_by_type() -> None:
    registry = AgentRegistry()
    register_default_agents(registry)
    matching = registry.get_by_type(AgentType.CANDIDATE_MATCHING)
    assert len(matching) == 1
    assert matching[0].config.name == "candidate-matcher"
