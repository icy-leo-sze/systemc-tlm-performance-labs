# Minimal AT smoke lab

[Project overview](../../README.md) | [LT performance lab](../lt/README_performance_lab.md)

This directory is a small, original TLM-2.0 approximately-timed smoke lab. The local
`references/doulos_at_example/` tree was used only as a protocol-shape reference:
it is not redistributed here, and this example does not copy Doulos source blocks.

`examples/lt` remains the stable loosely-timed performance workflow baseline.
This `examples/at` lab is the first step on a future AT timing refinement path.
It is not a cycle-accurate model, and it is not a real AXI, CHI, or NoC timing
model. Its only goal is to validate the TLM-2.0 AT four-phase flow and produce a
phase trace that makes that flow visible.

The lab now contains:

- initiator 101
- initiator 102
- one simple AT bus / arbiter
- one shared target
- one WRITE followed by one READ from each initiator
- CSV tracing of the four base-protocol phases

The target stores two 32-bit words. Initiator 101 writes `0x1010abcd` to
address `0x0` with transaction id `101001`, then reads it back with transaction
id `101002`. Initiator 102 writes `0x1020abcd` to address `0x4` with
transaction id `102001`, then reads it back with transaction id `102002`.

## Phase Flow

For each transaction:

1. Initiator sends `BEGIN_REQ` on the forward path.
2. Bus forwards `BEGIN_REQ` to the target.
3. Target accepts the request and sends `END_REQ` on the backward path.
4. Target executes the command and sends `BEGIN_RESP` on the backward path.
5. Initiator checks the response and sends `END_RESP` on the forward path.

The bus writes these transitions to `phase_trace.csv`.

## Phase 12: Dual Initiator Arbitration

Phase 12 extends the smoke lab to two initiators sharing one target path. The
bus is a tiny FIFO arbiter: it accepts `BEGIN_REQ` from either initiator, keeps
queued requests alive, and forwards only one active request at a time to the
target. The next queued request is released after the current transaction's
`END_RESP` reaches the target.

Because `BEGIN_REQ` is traced when the bus receives the initiator request, while
`END_REQ` is traced only after that request reaches the target, the analyzer's
`request_accept_latency_ns` exposes arbitration / queueing delay. This is still
only an AT smoke lab; it is not a cycle-accurate AXI, CHI, or NoC model.

## Phase 13: Arbitration Policy Knob

Phase 13 adds a small policy knob on the same bus. Set
`AT_ARBITRATION_POLICY` before running the executable:

```bash
AT_ARBITRATION_POLICY=fifo ./build/examples/at/at
AT_ARBITRATION_POLICY=priority_101 ./build/examples/at/at
AT_ARBITRATION_POLICY=priority_102 ./build/examples/at/at
```

`fifo` is the default when the variable is unset. `priority_101` chooses an
initiator 101 request first when both initiators have pending requests, while
`priority_102` does the same for initiator 102. The CSV schema is unchanged, so
the same analyzer can compare `request_accept_latency_ns` across policies. This
policy knob is still a smoke-lab refinement only; it is not a NoC, bank-conflict,
AXI, CHI, or cycle-accurate timing model.

## Phase 14: Arbitration Sweep Runner

Phase 14 adds a small runner that executes multiple arbitration policies and
collects analyzer output:

```bash
python3 examples/at/tools/run_arbitration_sweep.py \
  --binary ./build/examples/at/at
```

By default it runs `fifo`, `priority_101`, and `priority_102`, then writes:

- `examples/at/results/arbitration_sweep/summary.csv`
- `examples/at/results/arbitration_sweep/comparison.md`
- one case directory per policy, each with `phase_trace.csv`,
  `summary_metrics.csv`, `timeline.csv`, and captured stdout/stderr files

Use `--output-dir <path>` to put generated files elsewhere, and `--keep-going`
to continue after a failed case. The runner is an AT arbitration policy sweep
for this smoke lab; it is not an AXI, CHI, NoC, bank-conflict, or
cycle-accurate timing model.

## One-command AT demo

Phase 15 adds a small wrapper that runs the AT smoke lab, analyzes the default
trace, and then runs the arbitration sweep:

```bash
python3 examples/at/tools/demo_at_lab.py \
  --binary ./build/examples/at/at
```

It writes:

- `phase_trace.csv`
- `examples/at/results/analysis.txt`
- `examples/at/results/arbitration_sweep/summary.csv`
- `examples/at/results/arbitration_sweep/comparison.md`

The demo only orchestrates the existing AT binary, phase trace analyzer, and
arbitration sweep runner. It is not an AXI, CHI, NoC, bank-conflict, or
cycle-accurate timing model.

## Project AT-1: Four-Phase AT Memory Transaction Timing Lab

Project AT-1 adds an independent AT mainline example under
`examples/at/four_phase_memory_timing/`. It keeps the existing arbitration smoke
lab unchanged and focuses on a minimal AT memory target with finite queue depth.

The model demonstrates:

- `nb_transport_fw` request path with `BEGIN_REQ` and `END_RESP`
- `nb_transport_bw` response path with `END_REQ` and `BEGIN_RESP`
- `sequential`、`bursty`、`hotspot` 三类 synthetic transaction pattern
- target queueing、initiator stall 和 visible back-pressure
- per-transaction `trace.csv` with four phase timestamps

Run the one-command Project AT-1 demo:

```bash
python3 examples/at/tools/demo_project_at1_four_phase_memory_timing.py
```

It writes:

- `examples/at/results/project_at1_four_phase_memory_timing/model_runs/<case_name>/trace.csv`
- `examples/at/results/project_at1_four_phase_memory_timing/project_at1_summary.csv`
- `examples/at/results/project_at1_four_phase_memory_timing/project_at1_report.md`

Project AT-1 is a SystemC/TLM AT teaching and architecture modeling lab. It is
not AXI / CHI protocol compliance, not cycle-accurate simulation, not silicon
validation, not production signoff, and not a real DRAM timing model.

## Project AT-2: Multi-Initiator AT Arbitration and Contention Lab

Project AT-2 adds an independent AT mainline example under
`examples/at/multi_initiator_arbitration/`. It keeps Project AT-1 behavior
unchanged and extends the AT teaching path from single-initiator four-phase
timing to multi-initiator contention and arbitration.

The model demonstrates:

- multiple synthetic initiators: `cpu0`, `dma0`, `accel0`
- `round_robin`, `fixed_priority`, and `weighted_priority` arbitration policy
- per-initiator request queueing pressure
- fairness / p95-p99 tail latency tradeoff
- target queue back-pressure and aggregate throughput comparison

Build and run Project AT-2 from the repository root:

```bash
cmake -S examples/at -B build-at2 \
  -DUSER_SYSTEMC_INCLUDE_DIR=$HOME/local/systemc/include \
  -DUSER_SYSTEMC_LIB_DIR=$HOME/local/systemc/lib

cmake --build build-at2 --target project_at2_multi_initiator_arbitration -j

python3 examples/at/tools/demo_project_at2_multi_initiator_arbitration.py \
  --build-dir build-at2
```

It writes:

- `examples/at/results/project_at2_multi_initiator_arbitration/model_runs/<case_name>/trace.csv`
- `examples/at/results/project_at2_multi_initiator_arbitration/project_at2_summary.csv`
- `examples/at/results/project_at2_multi_initiator_arbitration/project_at2_policy_summary.csv`
- `examples/at/results/project_at2_multi_initiator_arbitration/project_at2_report.md`

Project AT-2 is a SystemC/TLM AT teaching and architecture modeling lab. It is
not AXI / CHI protocol compliance, not a cycle-accurate interconnect model, not
a real NoC model, not silicon validation, not production signoff, not a real
DRAM timing model, and it does not model cache coherence.

## Build and Run

From the repository root:

```bash
cmake -S examples/at -B build/examples/at \
  -DUSER_SYSTEMC_LIB_DIR=<absolute path to SystemC lib> \
  -DUSER_SYSTEMC_INCLUDE_DIR=<absolute path to SystemC include>
cmake --build build/examples/at
./build/examples/at/at
```

If SystemC is installed in a standard search path, the two `USER_SYSTEMC_*`
arguments may be omitted.

To build against the bundled SystemC source tree instead:

```bash
cmake -S systemc -B build/systemc \
  -DCMAKE_CXX_STANDARD=17 \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build/systemc --target systemc
cmake -S examples/at -B build/examples/at \
  -DUSER_SYSTEMC_LIB_DIR="$PWD/build/systemc/src" \
  -DUSER_SYSTEMC_INCLUDE_DIR="$PWD/systemc/src"
cmake --build build/examples/at
./build/examples/at/at
```

The trace is written to the current working directory of the `at` executable.
When using the commands above, that is the repository root.

## Analyze Phase Trace

Use the analyzer to rebuild each transaction timeline from `phase_trace.csv`:

```bash
python3 examples/at/tools/analyze_phase_trace.py --trace phase_trace.csv
python3 examples/at/tools/analyze_phase_trace.py --trace phase_trace.csv --fail-on-sanity
python3 examples/at/tools/analyze_phase_trace.py --trace phase_trace.csv --summary-csv-output /tmp/at_summary.csv
python3 examples/at/tools/analyze_phase_trace.py --trace phase_trace.csv --timeline-csv-output /tmp/at_timeline.csv
```

`--summary-csv-output` writes one row of run-level metrics. Use
`--timeline-csv-output` when a per-transaction CSV is needed.

To compare policies:

```bash
AT_ARBITRATION_POLICY=fifo ./build/examples/at/at
python3 -B examples/at/tools/analyze_phase_trace.py \
  --trace phase_trace.csv \
  --timeline-csv-output /tmp/fifo_timeline.csv \
  --fail-on-sanity

AT_ARBITRATION_POLICY=priority_101 ./build/examples/at/at
python3 -B examples/at/tools/analyze_phase_trace.py \
  --trace phase_trace.csv \
  --timeline-csv-output /tmp/priority101_timeline.csv \
  --fail-on-sanity

AT_ARBITRATION_POLICY=priority_102 ./build/examples/at/at
python3 -B examples/at/tools/analyze_phase_trace.py \
  --trace phase_trace.csv \
  --timeline-csv-output /tmp/priority102_timeline.csv \
  --fail-on-sanity
```

## Expected Trace Shape

A representative trace contains four complete transactions:

```csv
txn_id,component,direction,phase,command,address,data,time_ns,delay_ns,response_status
102001,bus,FW,BEGIN_REQ,WRITE,0x0000000000000004,0x1020abcd,0.000,0.000,TLM_INCOMPLETE_RESPONSE
101001,bus,FW,BEGIN_REQ,WRITE,0x0000000000000000,0x1010abcd,0.000,0.000,TLM_INCOMPLETE_RESPONSE
102001,bus,BW,END_REQ,WRITE,0x0000000000000004,0x1020abcd,1.000,0.000,TLM_INCOMPLETE_RESPONSE
102001,bus,BW,BEGIN_RESP,WRITE,0x0000000000000004,0x1020abcd,5.000,0.000,TLM_OK_RESPONSE
102001,bus,FW,END_RESP,WRITE,0x0000000000000004,0x1020abcd,5.000,0.000,TLM_OK_RESPONSE
102002,bus,FW,BEGIN_REQ,READ,0x0000000000000004,0x00000000,5.000,0.000,TLM_INCOMPLETE_RESPONSE
101001,bus,BW,END_REQ,WRITE,0x0000000000000000,0x1010abcd,6.000,0.000,TLM_INCOMPLETE_RESPONSE
101001,bus,BW,BEGIN_RESP,WRITE,0x0000000000000000,0x1010abcd,10.000,0.000,TLM_OK_RESPONSE
101001,bus,FW,END_RESP,WRITE,0x0000000000000000,0x1010abcd,10.000,0.000,TLM_OK_RESPONSE
101002,bus,FW,BEGIN_REQ,READ,0x0000000000000000,0x00000000,10.000,0.000,TLM_INCOMPLETE_RESPONSE
102002,bus,BW,END_REQ,READ,0x0000000000000004,0x00000000,11.000,0.000,TLM_INCOMPLETE_RESPONSE
102002,bus,BW,BEGIN_RESP,READ,0x0000000000000004,0x1020abcd,15.000,0.000,TLM_OK_RESPONSE
102002,bus,FW,END_RESP,READ,0x0000000000000004,0x1020abcd,15.000,0.000,TLM_OK_RESPONSE
101002,bus,BW,END_REQ,READ,0x0000000000000000,0x00000000,16.000,0.000,TLM_INCOMPLETE_RESPONSE
101002,bus,BW,BEGIN_RESP,READ,0x0000000000000000,0x1010abcd,20.000,0.000,TLM_OK_RESPONSE
101002,bus,FW,END_RESP,READ,0x0000000000000000,0x1010abcd,20.000,0.000,TLM_OK_RESPONSE
```
