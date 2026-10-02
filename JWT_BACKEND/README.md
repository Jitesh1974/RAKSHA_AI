# RAKSHA AI Backend

Production backend for RAKSHA AI. The Android client sends notification-derived security events to this service over HTTPS. FastAPI validates and authenticates device requests, LangGraph orchestrates the investigation workflow, threat-intelligence tools provide evidence, llama.cpp serves the Qwen GGUF model, PostgreSQL persists application data, and Neo4j stores investigation relationships.

## Repository structure

- `app/api` — versioned HTTP endpoints and authentication dependencies
- `app/agents` — LangGraph state, workflow and investigation nodes
- `app/llm` — isolated llama.cpp client
- `app/tools` — threat-intelligence and analysis tools
- `app/db` — PostgreSQL models/repositories and Neo4j integration
- `app/services` — provider control and legacy integration helpers
- `migrations` — Alembic schema migrations
- `docker` — Caddy/TLS configuration
- `models` — local deployment model mount; GGUF files are not committed
- `tests` — backend unit tests

## API

### Device bootstrap

```http
POST /api/v1/auth/device/register
```

This creates or refreshes an installation credential and returns a signed JWT access token. For a public rollout, pair this with device attestation (such as Play Integrity), rate limiting, quotas and account lifecycle controls.

### Event analysis

```http
POST /api/v1/events/analyze
Authorization: Bearer <jwt_access_token>
X-Device-ID: <device_id>
```

The endpoint is idempotent by `event_id` when an analysis result already exists, which protects against duplicate notification delivery.

### JWT configuration

Set these variables in `.env` before starting the API:

```env
JWT_SECRET_KEY=<strong-random-secret>
JWT_ALGORITHM=HS256
JWT_ISSUER=raksha-ai
JWT_AUDIENCE=raksha-ai-api
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=259200
```

When `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` is left empty, the existing `DEVICE_TOKEN_TTL_DAYS` value is used as the JWT lifetime. PostgreSQL still stores a hash of the current JWT for device revocation and token refresh, so a refreshed device token invalidates the previous token without changing the existing database schema.

### Health

- `/health/live` — process liveness
- `/health/ready` — database + LLM readiness
- `/health/llm` — provider diagnostics

## Local development

1. Copy `.env.example` to `.env.dev` and configure `DATABASE_URL` and `LLAMA_CPP_BASE_URL` for your local services.
2. For a quick dev database, run:
   `docker compose -f docker-compose.dev.yml up --build`
3. Open `http://localhost:8000/docs`.

## Production deployment

1. Copy `.env.example` to `.env` and replace every `CHANGE_ME` value.
2. Put the Qwen GGUF model at `models/qwen-model.gguf` on the deployment host.
3. Set `RAKSHA_DOMAIN` to the public API hostname and point DNS to the server.
4. Ensure the deployment host has Docker + NVIDIA Container Toolkit when using the CUDA llama.cpp service.
5. Start with `docker compose up -d --build`.
6. Verify `/health/live` and `/health/ready` over HTTPS.

See `docs/PRODUCTION_DEPLOYMENT.md` and `docs/ARCHITECTURE.md` for the deployment boundary and remaining launch controls.

## Legacy Gmail integration

The prototype included Gmail OAuth and email sync. Those endpoints are now opt-in and disabled by default because the prototype stored refresh tokens outside the application database and the sync path was not device-scoped. Keep `ENABLE_LEGACY_GOOGLE_AUTH=false` and `ENABLE_LEGACY_EMAIL_SYNC=false` for the production deployment until that flow is migrated.

## Secrets

Do not commit `.env`, API keys, OAuth client secrets, database passwords or GGUF model files. The submitted prototype archive contained a real `.env`; rotate any credentials that were present there before using them in production.
