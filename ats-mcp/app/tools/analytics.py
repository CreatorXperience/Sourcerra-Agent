"""
TODO: BACKEND_REQUIRED — Analytics tool adapters.

These tools require backend endpoints that may not yet exist.
Once the backend exposes the corresponding APIs, remove the
TODO markers and implement the actual HTTP calls via BackendClient.

Expected endpoints:
  GET /analytics/funnel
  GET /analytics/hiring-speed
  GET /analytics/source
  GET /analytics/pipeline-health
  GET /analytics/dashboard
"""

from app.schemas.analytics import DashboardResponse, FunnelResponse, HiringSpeedResponse, PipelineHealthResponse, SourceAnalyticsResponse


async def ats_get_analytics_funnel(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Get hiring funnel conversion rates."""
    return [{"type": "text", "text": str(FunnelResponse().model_dump(mode="json"))}], False


async def ats_get_analytics_hiring_speed(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Get time-to-fill and time-to-hire metrics."""
    return [{"type": "text", "text": str(HiringSpeedResponse().model_dump(mode="json"))}], False


async def ats_get_analytics_source(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Get source effectiveness metrics."""
    return [{"type": "text", "text": str(SourceAnalyticsResponse().model_dump(mode="json"))}], False


async def ats_get_analytics_pipeline_health(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Get pipeline stage health."""
    return [{"type": "text", "text": str(PipelineHealthResponse().model_dump(mode="json"))}], False


async def ats_get_analytics_dashboard(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Get hiring dashboard composite."""
    return [{"type": "text", "text": str(DashboardResponse().model_dump(mode="json"))}], False
