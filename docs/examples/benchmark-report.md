# VeriClose benchmark report

- Status: **PASS**
- Profile: `segment5_default`
- Seeds: `42, 73, 101, 211, 307`
- Generated: `2026-09-04T16:18:16.674455+00:00`

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

- End-to-end runtime p50/p95: 3750 ms / 3794 ms
- Throughput p50/p95: 84 / 86 events/s

## Per-seed results

| Seed | Events | Cases | Case accuracy | False clears | Runtime ms | Events/s |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | 315 | 25 | 100.00% | 0 | 3794 | 83 |
| 73 | 311 | 25 | 100.00% | 0 | 3665 | 84 |
| 101 | 319 | 25 | 100.00% | 0 | 3778 | 84 |
| 211 | 315 | 25 | 100.00% | 0 | 3629 | 86 |
| 307 | 314 | 25 | 100.00% | 0 | 3750 | 83 |

## Threshold violations

- None

## Incorrect cases and events

No incorrect cases or events.
