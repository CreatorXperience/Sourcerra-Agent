import time
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends

from app.config.settings import Settings, get_settings
from app.schemas.health import ComponentStatus, DependencyHealth, HealthCheckResponse
from app.services.cache import get_cache_service

router = APIRouter()

_start_time: float = time.time()


async def _check_openrouter(settings: Settings) -> DependencyHealth:
    start = time.time()
    if not settings.OPENROUTER_API_KEY and not settings.OPENAI_API_KEY:
        return DependencyHealth(
            name="llm_provider",
            status=ComponentStatus.UNHEALTHY,
            detail="No API key configured",
        )
    latency_ms = round((time.time() - start) * 1000, 2)
    return DependencyHealth(
        name="llm_provider",
        status=ComponentStatus.HEALTHY,
        latency_ms=latency_ms,
    )


async def _check_cache() -> DependencyHealth:
    start = time.time()
    cache = get_cache_service()
    healthy = await cache.health()
    latency_ms = round((time.time() - start) * 1000, 2)
    return DependencyHealth(
        name="cache",
        status=ComponentStatus.HEALTHY if healthy else ComponentStatus.UNHEALTHY,
        detail="Redis available" if healthy else "Redis not connected",
        latency_ms=latency_ms,
    )


async def _check_store(path: str, name: str) -> DependencyHealth:
    start = time.time()
    p = Path(path)
    healthy = p.exists()
    latency_ms = round((time.time() - start) * 1000, 2)
    return DependencyHealth(
        name=name,
        status=ComponentStatus.HEALTHY if healthy else ComponentStatus.DEGRADED,
        detail=f"Path: {path}",
        latency_ms=latency_ms,
    )


@router.get("/live", response_model=HealthCheckResponse)
async def liveness() -> HealthCheckResponse:
    return HealthCheckResponse(
        status=ComponentStatus.HEALTHY,
        uptime_seconds=time.time() - _start_time,
        version="0.1.0",
    )


@router.get("", response_model=HealthCheckResponse)
async def health(
    settings: Settings = Depends(get_settings),
) -> HealthCheckResponse:
    deps = await _collect_deps(settings)
    overall = (
        ComponentStatus.HEALTHY
        if all(d.status == ComponentStatus.HEALTHY for d in deps)
        else (
            ComponentStatus.DEGRADED
            if any(d.status == ComponentStatus.DEGRADED for d in deps)
            else ComponentStatus.UNHEALTHY
        )
    )
    return HealthCheckResponse(
        status=overall,
        uptime_seconds=time.time() - _start_time,
        version="0.1.0",
        dependencies=deps,
    )


@router.get("/ready", response_model=HealthCheckResponse)
async def readiness(
    settings: Settings = Depends(get_settings),
) -> HealthCheckResponse:
    deps = await _collect_deps(settings)
    overall = (
        ComponentStatus.HEALTHY
        if all(d.status == ComponentStatus.HEALTHY for d in deps)
        else ComponentStatus.UNHEALTHY
    )
    return HealthCheckResponse(
        status=overall,
        uptime_seconds=time.time() - _start_time,
        version="0.1.0",
        dependencies=deps,
    )


async def _check_mcp(settings: Settings) -> DependencyHealth:
    start = time.time()
    if not settings.MCP_SERVER_URLS:
        return DependencyHealth(
            name="mcp",
            status=ComponentStatus.DEGRADED,
            detail="No MCP servers configured",
        )
    url = settings.MCP_SERVER_URLS[0].rstrip("/") + "/health"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            healthy = resp.status_code == 200
    except Exception:
        healthy = False
    latency_ms = round((time.time() - start) * 1000, 2)
    return DependencyHealth(
        name="mcp",
        status=ComponentStatus.HEALTHY if healthy else ComponentStatus.DEGRADED,
        detail=f"URL: {url}" if healthy else f"MCP unreachable at {url}",
        latency_ms=latency_ms,
    )


async def _collect_deps(settings: Settings) -> list[DependencyHealth]:
    deps: list[DependencyHealth] = []
    deps.append(await _check_openrouter(settings))
    deps.append(await _check_cache())
    deps.append(
        await _check_store(settings.EVALUATION_STORE_PATH, "evaluation_store")
    )
    deps.append(
        await _check_store(settings.PROMPT_STORE_PATH, "prompt_store")
    )
    deps.append(await _check_mcp(settings))
    return deps
