# Project AT-6: Heterogeneous SoC Shared Memory Fabric Lab

## Purpose

Project AT-6 models a bounded AT-level synthetic heterogeneous SoC problem type where CPU-like, NPU-like, DMA-like, and ISP-like initiators share one memory fabric. The goal is trend comparison, bottleneck isolation, and recommendation logic for shared-memory fabric pressure.

## Methodology

- Deterministic synthetic traffic is generated for four initiator classes.
- A shared request queue and single service path approximate fabric contention at AT level.
- Policies compare round-robin, latency-priority, and token-like NPU bandwidth cap behavior.
- Metrics include p50/p95/p99 latency, per-initiator throughput, bandwidth share, queue peak, SLA violation ratio, and starvation events.
- `npu_bandwidth_share`, `dma_bandwidth_share`, and `isp_bandwidth_share` are byte-share percentages inside this synthetic run.

## Case Table

| case | policy | intent | total txns | sim ns | p99 ns | queue peak | starvation events | CPU p99 ns | ISP p99 ns | NPU bw share | DMA bw share |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `baseline_rr` | `round_robin` | balanced mixed traffic baseline with no bandwidth cap | 228 | 10045.340 | 3989.080 | 57 | 181 | 2200.440 | 2107.350 | 34.783 | 42.391 |
| `priority_latency` | `priority_latency` | protect CPU-like and ISP-like tail latency with priority | 228 | 10045.340 | 6357.320 | 46 | 103 | 76.100 | 106.160 | 34.783 | 42.391 |
| `bandwidth_cap_npu` | `latency_priority_with_npu_cap` | apply token-like NPU cap while protecting CPU-like and ISP-like flows | 226 | 15358.723 | 11420.691 | 50 | 163 | 89.813 | 124.874 | 29.213 | 45.506 |
| `dma_stress` | `round_robin` | increase DMA-like sequential burst pressure on the shared fabric | 252 | 14522.490 | 10529.850 | 124 | 231 | 5140.310 | 5090.550 | 24.806 | 58.915 |
| `mixed_stress` | `latency_priority_no_cap` | combine NPU-like and DMA-like high pressure while observing latency flows | 300 | 20831.850 | 17103.600 | 171 | 277 | 115.425 | 202.000 | 34.743 | 48.338 |

## Key Observations

- `priority_latency` changes CPU-like p99 latency from 2200.440 -> 76.100 ns and ISP-like p99 latency from 2107.350 -> 106.160 ns versus `baseline_rr`.
- `bandwidth_cap_npu` reduces NPU-like throughput from 6.371 -> 3.386 txn/us and changes CPU-like / ISP-like p99 latency to 89.813 ns / 124.874 ns, showing the cost of bandwidth partitioning.
- `dma_stress` raises DMA byte share to 58.915% and increases fabric queue peak to 124, isolating bulk-transfer pressure.
- `mixed_stress` produces 277 starvation events while CPU-like / ISP-like p99 latency is 115.425 ns / 202.000 ns, showing that latency priority can protect selected flows while shifting starvation risk toward throughput and bulk flows.

## Architecture Lessons

- Priority can protect latency-sensitive flows, but it redistributes contention rather than creating more service capacity.
- A token-like cap on an aggressive throughput initiator can improve tail latency for CPU-like and ISP-like traffic, at the cost of lower NPU-like throughput.
- Long DMA-like transfers are a distinct bottleneck source because they consume byte share and stretch non-preemptive service time.
- Mixed NPU-like plus DMA-like pressure is the highest-risk case for tail latency collapse and starvation risk; latency priority may protect CPU-like / ISP-like traffic while exposing bulk-flow risk.

## Recommendation

Use `baseline_rr` as the reference point, then compare `priority_latency` and `bandwidth_cap_npu` before accepting a latency-sensitive architecture recommendation. If `mixed_stress` still violates CPU-like or ISP-like SLA thresholds, the bounded recommendation is to add explicit bandwidth partitioning or reduce bulk-transfer pressure before claiming QoS protection.

## Claim Boundary

This lab is a bounded AT-level synthetic heterogeneous SoC shared-memory fabric exploration. It does not claim Apple Silicon simulation, real NoC behavior, cycle-accurate modeling, silicon validation, or production signoff.

- Claim boundary: `bounded_at_level_synthetic_architecture_exploration`.
- Schema version: `at6.0`.
