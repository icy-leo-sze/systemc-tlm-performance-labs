# Project AT-7: GPU-like Throughput Engine and Memory Saturation Lab

## Purpose

Project AT-7 builds a bounded AT-level synthetic GPU-like throughput problem type. It generates many throughput-oriented memory requests from logical lanes, then observes outstanding-depth sensitivity, bandwidth saturation, latency hiding approximation, queue buildup, burstiness, and recommendation logic.

## Methodology

- Each case uses deterministic logical lanes with fixed request counts, burst length, compute gap, per-lane outstanding limit, and global outstanding limit.
- A shared memory request queue and single service path approximate a bounded AT-level bandwidth wall.
- Queue capacity, service bandwidth, and outstanding limits create backpressure / stall episodes when injection pressure exceeds the service path.
- Latency hiding is approximated by a synthetic rule: deeper outstanding windows hide more service latency until queue saturation exposes stall time.
- Metrics include latency percentiles, throughput, effective bandwidth, memory utilization, queue depth, outstanding depth, stall ratio, hidden latency, exposed stall, saturation flag, and knee-point hint.

## Case Table

| case | lanes | out/lane | global out | burst | throughput req/us | bandwidth B/ns | util | p95 latency ns | p99 latency ns | queue peak | avg outstanding | stall ratio | saturation | knee hint |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `low_occupancy` | 2 | 2 | 4 | 1 | 22.629 | 2.897 | 0.282 | 25.070 | 25.070 | 1 | 0.416 | 0.635 | `NO` | `below_knee_underfilled` |
| `balanced_occupancy` | 4 | 4 | 16 | 2 | 55.573 | 7.113 | 0.692 | 97.240 | 98.680 | 7 | 3.057 | 0.665 | `NO` | `approaching_knee` |
| `high_occupancy` | 8 | 6 | 32 | 2 | 73.007 | 9.345 | 0.909 | 398.760 | 399.120 | 31 | 21.210 | 0.669 | `YES` | `past_knee_bandwidth_wall` |
| `bandwidth_saturation` | 12 | 8 | 64 | 3 | 80.321 | 10.281 | 1.000 | 798.960 | 800.220 | 63 | 53.047 | 0.821 | `YES` | `past_knee_bandwidth_wall` |
| `bursty_stress` | 8 | 8 | 48 | 8 | 80.330 | 10.282 | 1.000 | 511.980 | 512.700 | 40 | 34.139 | 0.805 | `YES` | `past_knee_bandwidth_wall` |
| `throttled_occupancy` | 8 | 4 | 20 | 2 | 60.921 | 7.798 | 0.758 | 250.440 | 251.160 | 19 | 11.711 | 0.666 | `NO` | `approaching_knee` |

## Key Observations

- `low_occupancy` keeps memory utilization at 0.282 with p99 latency 25.070 ns, showing controlled tail behavior when the service path is not filled.
- Moving from `low_occupancy` to `balanced_occupancy` raises throughput 22.629 -> 55.573 req/us while keeping p99 latency at 98.680 ns, which is the useful latency-hiding region for this bounded model.
- `high_occupancy` increases average outstanding depth to 21.210 and reaches utilization 0.909, but p95 queue delay rises to 386.580 ns, indicating the knee region.
- `bandwidth_saturation` changes throughput from 73.007 -> 80.321 req/us versus `high_occupancy`, while p99 latency changes from 399.120 -> 800.220 ns; the additional pressure mostly becomes queue buildup rather than new throughput.
- `bursty_stress` reaches queue peak 40 and p99 latency 512.700 ns, showing how burstiness can expose tail latency even when the same service path is used.
- `throttled_occupancy` reduces p99 latency to 251.160 ns with throughput 60.921 req/us, giving a bounded reference point for throttle-based recommendation logic.

## Architecture Lessons

- Increasing outstanding depth helps hide memory latency while the memory service path still has headroom.
- After the bandwidth wall, extra lanes or outstanding requests mainly increase queue delay, p95/p99 latency, and exposed stall time.
- Burst length is a separate pressure knob: it can create high peak queue depth even when average request count is fixed.
- Throttling outstanding depth or injection rate can be a reasonable bounded architecture tradeoff when tail latency matters more than peak synthetic throughput.

## Recommendation

Use `balanced_occupancy` as the preferred operating point for this bounded exploration. If the design target prioritizes maximum throughput, compare it against `high_occupancy` and stop increasing outstanding depth once `knee_point_hint` reports a bandwidth wall. If p95/p99 latency or queue peak is the acceptance risk, use the `throttled_occupancy` profile as the safer recommendation baseline.

## Claim Boundary

This lab is a bounded AT-level synthetic GPU-like throughput and memory saturation exploration. It does not claim NVIDIA GPU simulation, real GPU behavior, CUDA execution modeling, real HBM-controller behavior, cycle-accurate modeling, silicon validation, or production signoff.

- Claim boundary: `bounded_at_level_synthetic_gpu_like_throughput_exploration`.
- Schema version: `at7.0`.
