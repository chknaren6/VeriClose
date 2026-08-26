# ADR-002: Canonical Event Model and Immutable Lineage

## Status

Accepted.

## Context

Gateway, bank and ERP exports express the same concepts with different columns, signs and identifiers.

## Decision

Source adapters convert rows into one canonical event model while preserving raw file, sheet, row, values and mapping version. Source evidence is immutable.

## Alternatives

- Matching raw data frames directly was rejected because every new format would leak into every rule.
- Destructive cleaning was rejected because it removes audit evidence.

## Consequences

New file styles are adapter work. Storage must retain both raw and canonical layers.
