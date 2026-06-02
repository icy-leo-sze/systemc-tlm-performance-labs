# SystemC/TLM Performance Labs

## What This Project Is

This repository is a SystemC/TLM virtual platform performance modeling lab built
on Renode-SystemC integration examples. It starts with an LT architecture-level
performance workflow and extends toward AT phase-level timing refinement. It is
not a cycle-accurate AXI, CHI, or NoC model. Its value is a reproducible
experiment chain: workload -> trace -> metrics -> sweep -> comparison -> demo.

## Project Map

| Lab | Path | Abstraction | Main capability | Demo |
| --- | --- | --- | --- | --- |
| LT Performance Lab | [`examples/lt`](examples/lt) | LT | Latency decomposition and workload sweep | `python3 examples/lt/tools/demo_performance_lab.py` |
| AT Arbitration Lab | [`examples/at`](examples/at) | AT | Phase trace and arbitration policy sweep | `python3 examples/at/tools/demo_at_lab.py --binary ./build/examples/at/at` |

Detailed lab notes:

- LT workflow: [`examples/lt/README_performance_lab.md`](examples/lt/README_performance_lab.md)
- AT workflow: [`examples/at/README.md`](examples/at/README.md)

## Why It Matters

The LT line demonstrates an architecture-level performance workflow: workload
knobs, transaction trace instrumentation, latency decomposition, workload sweep,
and generated comparison reports.

The AT line demonstrates phase-level timing observability with the TLM-2.0 base
protocol phases: `BEGIN_REQ`, `END_REQ`, `BEGIN_RESP`, and `END_RESP`. It also
shows how a small arbitration policy knob can change visible request-accept
latency.

Together, the two labs form a migration path from architecture workflow to AT
timing refinement without claiming protocol completeness or cycle accuracy.

## Quick Start

Build the AT lab from the repository root:

```bash
cmake -S examples/at -B build/examples/at
cmake --build build/examples/at
```

If SystemC is not discoverable through the default search paths, pass explicit
paths:

```bash
cmake -S examples/at -B build/examples/at \
  -DUSER_SYSTEMC_LIB_DIR=<absolute path to SystemC lib> \
  -DUSER_SYSTEMC_INCLUDE_DIR=<absolute path to SystemC include>
cmake --build build/examples/at
```

Run the AT one-command demo:

```bash
python3 examples/at/tools/demo_at_lab.py \
  --binary ./build/examples/at/at
```

Run the LT one-command demo:

```bash
python3 examples/lt/tools/demo_performance_lab.py
```

For LT Renode setup, generated artifacts, and detailed interpretation, see
[`examples/lt/README_performance_lab.md`](examples/lt/README_performance_lab.md).

## Key Results Snapshot

These are validated lab snapshots, not hardware timing claims.

| Lab | Case | Result |
| --- | --- | --- |
| LT | `stride=4` to `stride=16` | `bank_conflict_ratio_pct` rises from `46.875%` to `98.438%`; `avg_delay_ns` rises from `164.688 ns` to `185.312 ns` |
| AT | `fifo` | `complete_transactions = 4` |
| AT | `priority_101` | accepts `101xxx` faster: `101xxx avg = 1.000 ns`, `102xxx avg = 6.000 ns` |
| AT | `priority_102` | accepts `102xxx` faster: `102xxx avg = 1.000 ns`, `101xxx avg = 6.000 ns` |

## Roadmap

Planned directions are deliberately small and validation-oriented:

- AT multi-target path
- AT response scheduling
- outstanding transaction depth
- LT vs AT comparison under equivalent workload

These items are future work, not completed capabilities.

## Boundaries

- This is an educational and experimental modeling lab.
- It is not cycle accurate.
- It is not AXI, CHI, or NoC compliant.
- It does not claim real interconnect protocol support.
- The LT lab is an architecture-level workflow, not a final timing model.
- The AT lab is a smoke/arbitration lab, not a production interconnect model.
- A local Doulos AT example, if present, is only a protocol-shape reference and
  is not redistributed by this repository.

## License and Attribution

This repository retains the upstream Renode-SystemC integration license and
notice files. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
