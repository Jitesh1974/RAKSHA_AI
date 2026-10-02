# RAKSHA AI Production Architecture

```text
Android
  |
  | HTTPS + device credential
  v
Caddy / TLS
  |
  v
FastAPI /api/v1
  |
  +--> PostgreSQL  (devices, events, analysis results)
  |
  +--> LangGraph investigation workflow
  |      |
  |      +--> message agent
  |      +--> URL agent
  |      +--> attachment agent
  |      +--> email agent
  |      +--> aggregator
  |      +--> risk engine
  |      +--> explanation agent
  |
  +--> Threat intelligence tools
  |      +--> Safe Browsing
  |      +--> VirusTotal
  |      +--> URL expansion / hashes / similarity
  |
  +--> llama.cpp HTTP service
  |      |
  |      +--> Qwen GGUF model
  |
  +--> Neo4j
         |
         +--> event / sender / URL relationships
```

## Mobile boundary

The Android application owns notification capture, normalization, local retention, UI rendering and user-facing alert delivery. It never embeds the Qwen model or database credentials.

## Backend boundary

FastAPI owns authentication, event validation, orchestration and persistence. LangGraph owns investigation flow. llama.cpp is an independent inference service. PostgreSQL is the system of record for structured application data; Neo4j stores relationships used for investigation and graph analytics.

## Network boundary

Only Caddy publishes ports 80/443. PostgreSQL, Neo4j and llama.cpp remain on the private Docker bridge network. The Android release client must use the public HTTPS API origin.
