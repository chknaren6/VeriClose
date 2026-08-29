# VeriClose benchmark report

- Status: **PASS**
- Profile: `segment5_default`
- Seeds: `42, 73, 101, 211, 307, 401, 503, 607, 709, 811`
- Generated: `2026-08-29T09:22:45.635263+00:00`

## Aggregate safety metrics

| Metric | Result | Denominator |
|---|---:|---:|
| Event accuracy | 100.00% | 3149 |
| Case accuracy | 100.00% | 250 |
| Auto-clear precision | 100.00% | 150 auto-clears |
| Exception recall | 100.00% | 100 expected exceptions |
| False-clear rate | 0.00% | 150 auto-clears |
| False-clear count | 0 | — |
| Wrong exception classification | 0 | — |

## Runtime

- End-to-end runtime p50/p95: 2613 ms / 2764 ms
- Throughput p50/p95: 120 / 123 events/s

## Per-seed results

| Seed | Events | Cases | Case accuracy | False clears | Runtime ms | Events/s |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | 315 | 25 | 100.00% | 0 | 2613 | 120 |
| 73 | 311 | 25 | 100.00% | 0 | 2573 | 120 |
| 101 | 319 | 25 | 100.00% | 0 | 2701 | 118 |
| 211 | 315 | 25 | 100.00% | 0 | 2631 | 119 |
| 307 | 314 | 25 | 100.00% | 0 | 2654 | 118 |
| 401 | 311 | 25 | 100.00% | 0 | 2579 | 120 |
| 503 | 319 | 25 | 100.00% | 0 | 2591 | 123 |
| 607 | 315 | 25 | 100.00% | 0 | 2764 | 113 |
| 709 | 315 | 25 | 100.00% | 0 | 2616 | 120 |
| 811 | 315 | 25 | 100.00% | 0 | 2605 | 120 |

## Threshold violations

- None

## Incorrect cases and events

No incorrect cases or events.
