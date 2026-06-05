# SystemC/TLM Architecture Performance Labs

Target audience: SoC Architecture Engineer, Performance Modeling Engineer, ESL
Engineer, and Architecture Performance Analysis interviewer.

## Case Study Summary

`SystemC/TLM Architecture Performance Labs` is a compact architecture-level
performance modeling project built around a reproducible experiment chain:

```text
workload -> trace -> metrics -> sweep -> comparison -> demo
```

The project does not try to present a production interconnect model. Its value
is narrower and more practical: take a workload or trace source, replay it
through a SystemC/TLM performance analysis backend, and produce measurable
latency, bank-conflict, throughput, `summary.csv`, and `comparison.md`
artifacts.

The current LT-side evolution is:

```text
Synthetic workload
-> normalized trace replay
-> gem5 SE-derived trace replay
```

This staged flow shows how a controlled synthetic experiment can become a trace
contract, and then accept memory-access streams produced by an external
simulator.

## 1. Project Motivation

Architecture performance work usually needs a chain of evidence, not just a
model file. A useful performance model should make it possible to answer:

- What workload or traffic pattern was used?
- What trace evidence was produced?
- Which metrics were computed?
- Can multiple cases be compared consistently?
- Can another engineer reproduce the result?

This project was built to make that chain explicit. The core question is not
"is this cycle-accurate hardware?" The core question is:

> Can a workload stream be turned into trace evidence and architecture-level
> performance metrics in a repeatable way?

For interview purposes, the project demonstrates performance-modeling judgment:
define a bounded abstraction, preserve trace evidence, compute interpretable
metrics, automate sweeps, and avoid overclaiming fidelity.

## 2. Why Start With SystemC/TLM LT and AT Labs

The project starts with SystemC/TLM because TLM is a natural fit for virtual
platform and architecture-level performance experiments. It lets the model
focus on transaction flow, latency decomposition, arbitration observability,
and workload sensitivity before attempting lower-level timing fidelity.

The LT lab is the foundation because it is the fastest way to establish the
workflow:

- workload knobs
- transaction trace generation
- latency decomposition
- metrics extraction
- sweep automation
- generated comparison reports

The AT lab exists as the timing-refinement direction. It exposes TLM-2.0 phase
observability with `BEGIN_REQ`, `END_REQ`, `BEGIN_RESP`, and `END_RESP`, and it
shows how arbitration policy affects request-accept latency.

The important modeling decision is staged fidelity:

| Layer | Purpose | What it is good for |
| --- | --- | --- |
| LT | Architecture-level workflow | Workload sensitivity, latency decomposition, metrics, sweeps. |
| AT | Phase-level timing refinement | Request/response phase observability and arbitration effects. |

LT and AT are not presented as a complete AXI/CHI/NoC model. They are bounded
labs that make performance questions measurable.

## 3. Phase16A: Synthetic Memory Access Pattern MVP

Phase16A adds explicit memory access patterns on top of the LT workflow. The
goal is to compare controlled synthetic traffic patterns and observe how the
minimal bank-conflict abstraction changes latency and throughput metrics.

Traffic sources:

- `sequential`
- `stride`
- `hotspot`

The important pair for this case study is `sequential` vs `stride`.

Phase16A keeps the same chain:

```text
synthetic workload
-> trace.csv
-> summary.csv
-> comparison.md
-> demo PASS
```

### Phase16A Results

| workload | avg_latency_ns | p99_latency_ns | bank_conflict_ratio_pct | throughput_txn_per_us |
| --- | ---: | ---: | ---: | ---: |
| `sequential` | 100.000 | 120.000 | 0.000 | 20.000 |
| `stride` | 119.688 | 140.000 | 98.438 | 16.710 |

Engineering interpretation:

- `sequential` walks through the minimal bank model without repeated same-bank
  hits.
- `stride` uses 16-byte spacing, which maps repeated accesses back to the same
  minimal bank in the current LT abstraction.
- The result is an architecture-level signal: access pattern changes
  `bank_conflict_ratio_pct`, tail latency, and throughput.

This does not claim real DRAM bank timing. It only shows that the model can
turn workload shape into repeatable performance evidence.

## 4. Project B: Normalized Trace Replay Bridge MVP

Project B separates traffic generation from replay. Instead of requiring all
traffic to come from an in-model synthetic generator, it defines a normalized
CSV trace interface and replays that trace through the existing LT analysis
backend.

Input schema:

```text
workload_name,txn_id,timestamp_ns,initiator_id,command,address,size_bytes
```

Project B chain:

```text
normalized external trace
-> run_trace_replay_lab.py
-> trace.csv
-> summary.csv
-> comparison.md
```

This step is important because it creates a stable trace contract before
introducing gem5. The project can now ask whether an external memory-access
stream can be represented, validated, replayed, and compared using the same
metrics.

### Project B Results

| workload | avg_latency_ns | p99_latency_ns | bank_conflict_ratio_pct | throughput_txn_per_us |
| --- | ---: | ---: | ---: | ---: |
| `sample_sequential` | 100.000 | 100.000 | 0.000 | 10.000 |
| `sample_stride` | 119.688 | 120.000 | 98.438 | 9.969 |

Engineering interpretation:

- The replay bridge reproduces the same bank-conflict signal as Phase16A for a
  stride-shaped input trace.
- The metrics are generated from normalized trace replay, not from a live
  simulator integration.
- The `timestamp_ns` field is an issue-time and ordering hint for replay. It is
  not gem5 timing and not cycle timing.

Project B is the interface step: it proves that the backend can consume
external traces.

## 5. Project C: gem5 SE Trace Extraction MVP

Project C adds gem5 SE mode as an external trace producer. It runs small
AArch64 C workloads under gem5 SE, captures `PROJECT_C_MEM` markers, converts
them into normalized trace CSV, and reuses Project B replay.

Validated Project C chain:

```text
AArch64 C workload
-> gem5 SE mode
-> PROJECT_C_MEM markers
-> run_stdout.txt
-> convert_gem5_se_trace.py
-> normalized trace CSV
-> run_trace_replay_lab.py
-> summary.csv / comparison.md
```

Workloads:

- `sequential_scan.c`
- `stride_scan.c`

gem5 role:

- gem5 is only the offline trace producer.
- The SystemC/TLM lab remains the replay and analysis backend.

Project C does not connect gem5 and SystemC in a live simulation loop.

### Project C Results

| workload | avg_latency_ns | p99_latency_ns | bank_conflict_ratio_pct | throughput_txn_per_us |
| --- | ---: | ---: | ---: | ---: |
| `gem5_sequential_scan` | 100.000 | 100.000 | 0.000 | 10.000 |
| `gem5_stride_scan` | 119.688 | 120.000 | 98.438 | 9.969 |

Engineering interpretation:

- gem5 SE executes the AArch64 user-level workload and produces a marker stream.
- The converter maps the marker stream into the normalized trace schema.
- The replay backend observes the same stride-vs-sequential pattern as the
  earlier stages.
- This closes the staged path from synthetic traffic to gem5 SE-derived trace
  replay.

## 6. Evolution Chain

The three stages are deliberately small and cumulative.

```text
Phase16A
Synthetic workload
-> controlled access-pattern experiment
-> trace / metrics / comparison

Project B
Normalized trace replay
-> file-based trace contract
-> external traffic can enter the backend

Project C
gem5 SE-derived trace replay
-> external simulator produces memory-access stream
-> SystemC/TLM lab replays and analyzes it
```

The key design principle is separation of concerns:

| Stage | Traffic source | Backend | Main value |
| --- | --- | --- | --- |
| Phase16A | Built-in synthetic patterns | LT performance lab | Controlled access-pattern sensitivity. |
| Project B | Normalized CSV traces | Trace replay backend | Stable external trace contract. |
| Project C | gem5 SE-derived marker stream | Project B replay backend | External producer connected through files. |

This evolution avoids jumping directly into gem5-SystemC live co-simulation.
That would mix workload setup, simulator synchronization, timing ownership,
trace schema, and performance analysis in one step. The staged approach keeps
each boundary testable.

## 7. Key Results

### Phase16A

| workload | avg_latency_ns | p99_latency_ns | bank_conflict_ratio_pct | throughput_txn_per_us |
| --- | ---: | ---: | ---: | ---: |
| `sequential` | 100.000 | 120.000 | 0.000 | 20.000 |
| `stride` | 119.688 | 140.000 | 98.438 | 16.710 |

### Project B

| workload | avg_latency_ns | p99_latency_ns | bank_conflict_ratio_pct | throughput_txn_per_us |
| --- | ---: | ---: | ---: | ---: |
| `sample_sequential` | 100.000 | 100.000 | 0.000 | 10.000 |
| `sample_stride` | 119.688 | 120.000 | 98.438 | 9.969 |

### Project C

| workload | avg_latency_ns | p99_latency_ns | bank_conflict_ratio_pct | throughput_txn_per_us |
| --- | ---: | ---: | ---: | ---: |
| `gem5_sequential_scan` | 100.000 | 100.000 | 0.000 | 10.000 |
| `gem5_stride_scan` | 119.688 | 120.000 | 98.438 | 9.969 |

Across all three stages, the consistent observation is that a stride-shaped
access stream triggers the current LT backend's minimal bank-conflict
abstraction, while a sequential stream does not.

The exact latency and throughput values differ between Phase16A and the replay
stages because they exercise different paths. The important comparison is the
repeatable access-pattern effect, not a hardware timing claim.

## 8. Scope and Boundaries

This case study is about:

- architecture-level performance modeling
- offline trace-driven replay
- reproducible trace / metrics / comparison artifacts
- gem5 SE as a trace producer
- SystemC/TLM lab as replay and analysis backend

This case study is not:

- gem5-SystemC live co-simulation
- full-system Linux simulation
- cycle-accurate AXI model
- cycle-accurate CHI model
- cycle-accurate NoC model
- cycle-accurate DRAM model
- cycle-accurate GPU model
- silicon correlation
- production interconnect protocol compliance

`timestamp_ns` in normalized traces is an issue-time / ordering hint. It is not
gem5 timing and not cycle timing.

## 9. Interview Explanation: 60 Seconds

`SystemC/TLM Architecture Performance Labs` is a staged architecture-level
performance modeling project. I built it around a reproducible chain:
`workload -> trace -> metrics -> sweep -> comparison -> demo`.

The first stage, Phase16A, uses synthetic memory access patterns. It shows that
a stride pattern raises `bank_conflict_ratio_pct` from `0.000%` to `98.438%`
in the current LT abstraction.

Project B then moves from synthetic generation to normalized trace replay. It
defines a CSV trace contract and proves that an external trace can be replayed
through the same backend.

Project C uses gem5 SE mode as an offline trace producer. gem5 runs an AArch64
workload, emits `PROJECT_C_MEM` markers, the converter produces normalized CSV,
and the SystemC/TLM lab replays and analyzes it.

The key point is scope discipline: this is architecture-level performance
modeling and offline trace replay. It is not gem5-SystemC live co-simulation,
not full-system Linux, and not a cycle-accurate AXI/CHI/NoC/DRAM/GPU model.

## 10. Interview Explanation: 3 Minutes

I designed this project as a small but complete architecture performance
workflow. The central idea is that performance analysis should be reproducible:
define a workload, capture trace evidence, compute metrics, run comparisons,
and generate a demo or report.

I started with SystemC/TLM LT because LT is the right level for early
architecture exploration. It lets me focus on workload sensitivity and latency
composition without claiming cycle-level protocol accuracy. In Phase16A, I
added synthetic memory access patterns: `sequential`, `stride`, and `hotspot`.
The key result is that `stride` raises `bank_conflict_ratio_pct` to `98.438%`,
while `sequential` remains at `0.000%`. That shows the workflow can turn an
access-pattern change into measurable metrics.

Then I built Project B, the normalized trace replay bridge. This separates
traffic production from analysis. A trace only needs a stable CSV schema:
`workload_name`, `txn_id`, `timestamp_ns`, `initiator_id`, `command`,
`address`, and `size_bytes`. The replay backend reads the trace, validates it,
sorts it deterministically, computes latency and bank-conflict metrics, and
writes `summary.csv` and `comparison.md`.

Project C uses that bridge for gem5 SE-derived traces. gem5 SE runs AArch64
`sequential_scan` and `stride_scan` workloads. The workloads emit
`PROJECT_C_MEM` markers, which are captured in `run_stdout.txt`. The converter
turns those markers into normalized CSV, and Project B replay produces the same
kind of summary and comparison artifacts. The result is that
`gem5_stride_scan` shows `bank_conflict_ratio_pct = 98.438%`, while
`gem5_sequential_scan` stays at `0.000%`.

The important engineering choice is that gem5 is only an offline trace
producer. The SystemC/TLM lab is the replay and analysis backend. This avoids
claiming live co-simulation or cycle accuracy before the file-based trace
contract is stable.

## 11. Possible Interview Questions and Answers

### Q1: What is the main engineering value of this project?

It demonstrates a complete architecture performance analysis workflow:
workload definition, trace capture, metric extraction, comparison generation,
and reproducible demo behavior. The value is not protocol completeness; the
value is turning workload behavior into measurable, explainable evidence.

### Q2: Why did you start with LT instead of AT or full gem5 integration?

LT is the fastest way to validate the architecture-level workflow. Before
adding phase-level timing or external simulators, I wanted a stable chain for
workload, trace, metrics, sweep, and comparison. That makes later extensions
debuggable.

### Q3: Why add AT if the current evolution chain focuses on LT replay?

AT is the timing-refinement direction. LT gives fast architecture-level
observability; AT exposes TLM phase timing such as `BEGIN_REQ`, `END_REQ`,
`BEGIN_RESP`, and `END_RESP`. The two labs answer different questions.

### Q4: What did Phase16A prove?

It proved that controlled synthetic memory patterns can produce repeatable
architecture-level metric differences. In the current LT abstraction,
`stride` produces `bank_conflict_ratio_pct = 98.438%`, while `sequential`
stays at `0.000%`.

### Q5: What did Project B add?

Project B added a normalized trace replay contract. Instead of requiring
traffic to be generated inside the model, it lets an external CSV memory trace
enter the same replay and analysis backend.

### Q6: What did Project C add?

Project C added gem5 SE mode as an offline producer of normalized traces. gem5
runs the AArch64 workload, captures `PROJECT_C_MEM` markers, and the converter
turns them into CSV traces that Project B can replay.

### Q7: Is this gem5-SystemC co-simulation?

No. gem5 is not connected to the SystemC kernel in a live simulation loop. gem5
produces a file-based trace, and the SystemC/TLM lab replays and analyzes that
trace offline.

### Q8: Is `timestamp_ns` gem5 timing?

No. In this MVP, `timestamp_ns` is a normalized issue-time and ordering hint
used by the replay backend. It is not gem5 timing and not cycle timing.

### Q9: Why do Project B and Project C have the same stride results?

Because Project C ultimately feeds a gem5 SE-derived stride-shaped memory
stream into the same Project B replay backend. The backend's minimal bank model
sees the same access spacing and therefore produces the same bank-conflict
signal.

### Q10: What is the biggest limitation?

The current model is intentionally not cycle-accurate. It does not implement
AXI, CHI, NoC, DRAM, GPU, cache coherence, or full-system Linux behavior. The
strength is the reproducible architecture-level workflow, not hardware fidelity.

### Q11: What would you do next?

I would improve trace quality and metadata: add better workload-region
filtering, preserve PC or symbol information when useful, and expand replay
coverage to read/write mixes or multiple initiators. I would keep the same
principle: file-based evidence first, more timing fidelity later.

## 12. Closing Statement

This case study is intentionally conservative. It does not claim to be a
cycle-accurate platform. It shows how to build a practical, staged performance
modeling workflow:

```text
controlled synthetic workload
-> normalized trace interface
-> gem5 SE-derived trace input
-> SystemC/TLM replay and analysis
```

For SoC architecture, ESL, and performance modeling interviews, the signal is
engineering discipline: define the boundary, produce trace evidence, compute
repeatable metrics, compare cases, and state limitations clearly.
