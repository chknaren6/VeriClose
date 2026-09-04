# VeriClose benchmark report

- Status: **PASS**
- Profile: `segment5_default`
- Seeds: `42, 73, 101, 211, 307`
- Generated: `2026-09-04T18:38:30.392644+00:00`

## Aggregate safety metrics

| Metric | Result | Denominator |
|---|---:|---:|
| Event accuracy | 100.00% | 1574 |
| Case accuracy | 100.00% | 125 |
| Auto-clear precision | 100.00% | 75 auto-clears |
| Exception recall | 100.00% | 50 expected exceptions |
| False-clear rate | 0.00% | 75 auto-clears |
| False-clear count | 0 | — |
| Wrong exception classification | 0 | — |

## Runtime

- End-to-end runtime p50/p95: 3656 ms / 4132 ms
- Throughput p50/p95: 87 / 100 events/s

## Per-seed results

| Seed | Events | Cases | Case accuracy | False clears | Runtime ms | Events/s |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | 315 | 25 | 100.00% | 0 | 3161 | 99 |
| 73 | 311 | 25 | 100.00% | 0 | 3103 | 100 |
| 101 | 319 | 25 | 100.00% | 0 | 3656 | 87 |
| 211 | 315 | 25 | 100.00% | 0 | 4132 | 76 |
| 307 | 314 | 25 | 100.00% | 0 | 3933 | 79 |

## Threshold violations

- None

## Incorrect cases and events

No incorrect cases or events.
