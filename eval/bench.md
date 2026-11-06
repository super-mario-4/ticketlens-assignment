# Speed benchmark

- Date: 2026-11-06 20:13 UTC
- Model: `qwen3.6:35b-a3b`; 3 parallel requests
- Stored classifications measured: 205
- First and last: 18:02:57 and 20:13:12 UTC
- Throughput counts working time only (0.33 h): gaps over 120 s are left out

| Metric | Measured |
| --- | --- |
| Latency p50 | 17.0 s |
| Latency p95 | 25.4 s |
| Latency max | 30.9 s |
| Throughput | 621 tickets per hour |
| Time for 1,000 tickets | 97 min |
| Mean input tokens | 587 |
| Mean output tokens | 77 |
| Tokens for 1,000 tickets | 587k in, 77k out |

## Tickets by status

| Status | Reason | Tickets |
| --- | --- | --- |
| classified | - | 202 |
| pending | - | 1689 |
| needs_review | no_content | 82 |
| needs_review | injection_suspected | 21 |
| processing | - | 3 |
| needs_review | unclear | 3 |

Mean `classified_at - ingested_at` over 202 tickets: 16176 s. A CSV import queues everything at once, so this measures the backlog, not the target of one minute at the normal rate.

