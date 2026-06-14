# Deployment Guide

## Architecture

```
                         ┌─────────────┐
                         │   Redis      │
                         │  (Cache)     │
                         └──────┬──────┘
                                │
┌──────────┐    ┌───────────────▼──────────────┐    ┌───────────┐
│  Client  │───▶│     AI Service (FastAPI)      │───▶│  MCP      │
│  (HTTP)  │    │  ┌─────────────────────────┐  │    │  Servers  │
└──────────┘    │  │ OpenAI Agents SDK Agents │  │    └───────────┘
                │  │ Workflows                │  │
                │  │ Evaluation + Tracing     │  │    ┌───────────┐
                │  │ Prompt Registry          │  │───▶│  Backend  │
                │  │ Metrics + Logging        │  │    │  API      │
                │  └─────────────────────────┘  │    └───────────┘
                └────────────────────────────────┘
```

## Local Development

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (optional, for Redis)

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd ai-service

# Create environment file
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -e ".[dev]"

# Run the service
uvicorn app.main:app --reload --port 8000
```

### Docker Compose (Local)

```bash
# Start with Redis
docker compose up -d

# Start with Redis + PostgreSQL
docker compose --profile with-db up -d

# View logs
docker compose logs -f ai-service
```

## Docker Deployment

### Build

```bash
# Build the production image
docker build -t sourcerra-ai:latest .

# Build with specific version
docker build -t sourcerra-ai:v1.0.0 .
```

### Run

```bash
# Production compose
docker compose -f docker-compose.prod.yml up -d

# Check health
curl http://localhost:8000/api/v1/health/live
```

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | OpenRouter API key (or `OPENAI_API_KEY`) |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Sourcerra AI Service` | Service name |
| `ENVIRONMENT` | `development` | Runtime environment |
| `DEBUG` | `false` | Debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PORT` | `8000` | HTTP port |

### LLM Provider

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | `` | OpenAI API key (alternative) |
| `OPENROUTER_API_KEY` | `` | OpenRouter API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter endpoint |
| `OPENROUTER_DEFAULT_MODEL` | `openai/gpt-4o` | Default model |
| `OPENROUTER_FALLBACK_MODEL` | `openai/gpt-4o-mini` | Fallback model |

### Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `EVALUATION_STORE_PATH` | `data/evaluation` | Evaluation data directory |
| `PROMPT_STORE_PATH` | `data/evaluation` | Prompt registry data directory |

### Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `` | Redis connection URL |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `` | API key for authentication |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `false` | Enable rate limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Max requests per minute |

### Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_ENABLED` | `false` | Enable OpenTelemetry |
| `OTEL_SERVICE_NAME` | `sourcerra-ai` | OpenTelemetry service name |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | OTLP endpoint |

## Cloud Deployments

### AWS ECS

```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag sourcerra-ai:latest <account>.dkr.ecr.us-east-1.amazonaws.com/sourcerra-ai:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/sourcerra-ai:latest

# Deploy via ECS
aws ecs update-service --cluster sourcerra --service ai-service --force-new-deployment
```

### DigitalOcean Apps

1. Connect GitHub repository
2. Select `Dockerfile` as build method
3. Set environment variables
4. Configure HTTP port 8000
5. Add Redis as a managed database

### Railway

1. Connect GitHub repository
2. Add environment variables
3. Deploy with `docker build -t ${{ RAILWAY_SERVICE }} .`

### Render

1. Create Web Service
2. Select "Docker" runtime
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Redis as a sidecar

### Fly.io

```bash
fly launch
fly secrets set OPENROUTER_API_KEY=sk-or-v1-...
fly deploy
```

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-service
  template:
    metadata:
      labels:
        app: ai-service
    spec:
      containers:
      - name: ai-service
        image: ghcr.io/sourcerra/ai-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-service-secrets
              key: openrouter-api-key
        - name: REDIS_URL
          value: redis://redis-service:6379
        livenessProbe:
          httpGet:
            path: /api/v1/health/live
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "2"
---
apiVersion: v1
kind: Service
metadata:
  name: ai-service
spec:
  selector:
    app: ai-service
  ports:
  - port: 8000
    targetPort: 8000
```

## Health Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Full health check with dependency status |
| `GET /api/v1/health/live` | Liveness probe (always returns 200) |
| `GET /api/v1/health/ready` | Readiness probe (checks all dependencies) |

## Monitoring

### Metrics

`GET /api/v1/metrics` — Prometheus metrics endpoint exposing:

- `workflow_executions_total` — Workflow execution count by workflow and status
- `workflow_execution_duration_seconds` — Workflow latency histogram
- `agent_executions_total` — Agent execution count
- `agent_execution_duration_seconds` — Agent latency histogram
- `llm_calls_total` — LLM call count by model and provider
- `llm_token_usage_total` — Token usage by model and type
- `error_rate_total` — Error count by workflow and error type
- `active_workflows` — Current active workflows

### Logging

All logs are structured JSON with these correlation IDs:

- `request_id` — Per-request UUID
- `workflow` — Workflow name
- `candidate_id` — Candidate identifier
- `duration_ms` — Execution duration
- `status` — Execution status

## Rollback Procedure

### Docker Compose

```bash
# Rollback to previous version
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
# Rollback to previous revision
kubectl rollout undo deployment/ai-service

# Rollback to specific revision
kubectl rollout undo deployment/ai-service --to-revision=2
```

## Backup Strategy

### Data to Backup

- `data/evaluation/feedback.json` — User feedback records
- `data/evaluation/traces.json` — Workflow execution traces
- `data/evaluation/prompt_registry.json` — Prompt version registry
- `data/evaluation/experiments.json` — Experiment configurations

### Backup Commands

```bash
# Backup evaluation data
tar -czf evaluation-backup-$(date +%Y%m%d).tar.gz data/evaluation/

# Restore
tar -xzf evaluation-backup-YYYYMMDD.tar.gz
```

## CI/CD Pipeline

### Pull Request

1. Ruff linting + formatting check
2. MyPy type checking
3. Pytest with coverage (fail below 80%)
4. Artifact: coverage report

### Main Branch Push

1. All PR checks pass
2. Trivy security scan (filesystem)
3. Docker build + push to GHCR
4. Image tags: `latest`, `sha-<commit>`
5. Trivy security scan (image)

### Manual Deploy

1. Trigger `workflow_dispatch` on `deploy.yml`
2. Select environment (staging/production)
3. Optionally run database migrations
4. Health check verification
5. Automatic rollback on failure

## Security

- Docker image runs as non-root user (`app`)
- Secrets via environment variables (never logged)
- Security headers on all responses
- Optional API key authentication
- Rate limiting support
- CORS configurable via environment
- All inputs validated via Pydantic schemas
