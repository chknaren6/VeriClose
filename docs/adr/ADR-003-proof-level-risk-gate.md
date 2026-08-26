# ADR-003: Strict Proof Levels and Risk Gate

## Status

Accepted.

## Context

A similarity score cannot distinguish accounting proof from a plausible guess.

## Decision

Rules emit match proposals. A separate risk gate assigns `PROVED`, `SUPPORTED`, `AMBIGUOUS`, `CONTRADICTED` or `INVALID_INPUT`. Auto-clear requires unique `PROVED` status and policy permission.

## Alternatives

- One confidence threshold was rejected because fuzzy evidence can appear highly confident while remaining non-unique.

## Consequences

Coverage may be lower, but false-clears become explicit and testable.
