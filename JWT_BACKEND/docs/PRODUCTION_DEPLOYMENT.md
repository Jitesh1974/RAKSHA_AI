# RAKSHA AI Production Deployment

This repository is the backend half of the RAKSHA AI production split. The Android client communicates with only the public HTTPS API. PostgreSQL, Neo4j and llama.cpp remain on the private Docker network.

## Host requirements

- Linux host recommended for production.
- NVIDIA GPU + NVIDIA Container Toolkit for CUDA-backed llama.cpp inference.
- DNS record pointing the chosen API hostname to the host.
- Docker Engine and Compose plugin.
- Persistent disk for PostgreSQL and Neo4j volumes.

## Configure secrets

Create `.env` from `.env.example` and replace every `CHANGE_ME` value. Do not commit `.env`.

At minimum configure:

- `POSTGRES_*` and `DATABASE_URL`
- `NEO4J_AUTH`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `RAKSHA_DOMAIN`
- `LLAMA_CPP_BASE_URL=http://llm:8080/v1`
- `JWT_SECRET_KEY` set to a strong random secret
- `JWT_ALGORITHM=HS256`
- `JWT_ISSUER=raksha-ai`
- `JWT_AUDIENCE=raksha-ai-api`
- `LLAMA_CPP_MODEL` to the model identifier expected by the llama.cpp server
- `SAFE_BROWSING_API_KEY` and/or `VIRUSTOTAL_API_KEY` when those tools are enabled

The Qwen GGUF file is intentionally excluded from Git. Copy it to `models/qwen-model.gguf` on the deployment host.

## Start

```bash
export RAKSHA_DOMAIN=api.example.com
docker compose up -d --build
```

The API container runs the current Alembic migrations before starting FastAPI. Caddy publishes only ports 80/443; PostgreSQL, Neo4j and the LLM service have no host port mappings.

## Verify

```bash
curl -fsS https://api.example.com/health/live
curl -fsS https://api.example.com/health/ready
```

`/health/ready` reports database and LLM readiness. Do not expose `/docs` publicly unless it is protected at the reverse proxy or deliberately enabled for an operator environment.

## Android release configuration

Set the Android Gradle property to the same HTTPS origin:

```text
-PRAKSHA_BACKEND_URL=https://api.example.com/
```

The production build script uses `RAKSHA_BACKEND_URL` as the Gradle property name.

## Before public launch

The current device bootstrap endpoint is designed for controlled deployment and testing. Before a public rollout, add Play Integrity/device attestation, distributed rate limiting, quotas, abuse detection, user/account lifecycle, structured audit logs, secret management, backups, and monitoring/alerting.

The legacy Gmail integration is disabled by default in the production API and release Android build because the prototype stored refresh tokens outside the application database and did not use device-scoped authorization. It should be migrated before re-enabling.
