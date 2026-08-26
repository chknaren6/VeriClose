# ADR-004: Hidden-Truth Evaluation

## Status

Accepted.

## Context

The track requires measured batch accuracy and an honest exception list.

## Decision

Synthetic generation produces source files and separate hidden labels. Runtime reconciliation cannot import or fetch those labels. Evaluation compares stored outputs with truth after the run.

## Alternatives

- Embedding expected labels in input rows was rejected because it leaks answers.
- Reporting match rate alone was rejected because it hides false-clears.

## Consequences

Evaluation code and truth storage require explicit isolation tests.
