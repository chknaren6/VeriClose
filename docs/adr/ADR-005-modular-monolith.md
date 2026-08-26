# ADR-005: Modular Monolith

## Status

Accepted.

## Context

The MVP needs clear boundaries and one-command deployment, not distributed operations.

## Decision

Use one repository and one production application image with domain, ports, adapters, application services, API and UI modules. Reconciliation runs in-process behind an application-service boundary.

## Alternatives

- Microservices and a worker queue were rejected until measured scale requires them.
- A single unstructured application module was rejected because it would block adapter and workflow expansion.

## Consequences

Module boundaries are enforced through imports and tests rather than network calls.
