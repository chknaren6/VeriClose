# ADR-009: Single-Image Judge Deployment

## Status

Accepted.

## Context

Judges need a hosted URL and a reproducible local path. Requiring separate frontend, API, database and model credentials increases failure risk.

## Decision

Development uses separate Vite and FastAPI processes. Production builds React assets and serves them with FastAPI from one non-root container and one origin. Deterministic fallback requires no model key. Plain Docker is the baseline; Compose is an optional convenience.

## Alternatives

- Separate production frontend/API services were rejected for the hackathon because they add deployment and CORS failure modes.
- Model-required startup was rejected because it prevents offline judging.

## Consequences

The embedded demo database uses a single application worker. Later multi-user scale requires external persistence and worker infrastructure.
