# Next-Phase Roadmap

## Stage 2 Positioning

Stage 2 is an industry-inspired architecture performance modeling roadmap.

Working theme: Industry-inspired architecture performance modeling roadmap.

Stage 2 does not copy Apple, NVIDIA, or Arm internal implementations. It borrows industry problem types:

- heterogeneous SoC shared memory fabric
- GPU-like throughput and memory saturation
- AMBA-inspired NoC QoS and coherency-boundary exploration

Stage 2 is inspired by industry problem types, not by any proprietary Apple, NVIDIA, or Arm internal implementation. The models remain bounded AT-level synthetic explorations for trend comparison, bottleneck isolation, and architecture recommendation logic.

## What Stage 2 Is

- bounded AT-level synthetic modeling
- architecture performance exploration
- bottleneck isolation
- workload-to-metric reasoning
- architecture recommendation logic
- portfolio-grade evidence generation

## What Stage 2 Is Not

- not Apple Silicon simulation
- not NVIDIA GPU simulation
- not Arm CHI / AXI / ACE compliance
- not real NoC implementation
- not real DRAM-controller implementation
- not cycle-accurate modeling
- not silicon validation
- not production signoff

## Roadmap

### Project T: Stage-1 Summary and Industry Roadmap

Project T documents Stage 1 as a completed portfolio phase and opens the bridge toward Stage 2. It turns the completed memory-system bottleneck labs into a concise stage summary, engineering lesson set, and industry-inspired roadmap.

### Project AT-6: Heterogeneous SoC Shared Memory Fabric Lab

Project AT-6 builds a synthetic AT-level lab where CPU-like, NPU-like, DMA-like, and ISP-like initiators share a memory fabric.

Status:

```text
independent lab implemented, not yet integrated into portfolio evidence harness
```

It observes:

- mixed traffic interference
- bandwidth partition
- latency-sensitive vs throughput-oriented flow
- fabric contention
- starvation risk
- simple QoS / bandwidth cap policy

Primary docs:

- [`docs/project_at6_heterogeneous_soc_fabric.md`](project_at6_heterogeneous_soc_fabric.md)

This is not Apple Silicon simulation. It is an Apple-like heterogeneous SoC problem type.

### Project U: Integrate AT-6 into Evidence Harness

Project U should add AT-6 to the portfolio evidence pack with clear PASS markers, result artifacts, summary checks, and claim-boundary validation.

### Project AT-7: GPU-like Throughput Engine and Memory Saturation Lab

Project AT-7 should build a GPU-like throughput traffic generator focused on memory saturation and latency hiding.

It should observe:

- occupancy-like outstanding request depth
- memory bandwidth saturation
- latency hiding
- throughput collapse
- request burstiness
- bandwidth wall

This is not NVIDIA GPU simulation. It is an NVIDIA-like throughput problem type.

### Project V: Integrate AT-7 into Evidence Harness

Project V should add AT-7 to the portfolio evidence pack with reproducible outputs, bounded validation checks, and explicit unsupported claims.

### Project AT-8: AMBA-inspired NoC QoS and Coherency Boundary Lab

Project AT-8 should build an AMBA-inspired NoC / interconnect-level synthetic lab.

It should observe:

- QoS classes
- route contention
- coherency boundary effect
- read/write interference
- ordering pressure
- protocol-inspired but not protocol-compliant behavior

This is not an Arm CHI / AXI / ACE compliance model.

### Project W: Integrate AT-8 into Evidence Harness

Project W should add AT-8 to the portfolio evidence pack with repeatable checks for traces, summaries, recommendations, and claim-boundary language.

### Project X: Portfolio Release Pack / Interview Demo Pack

Project X should organize the final portfolio release pack:

- README project map
- architecture diagrams
- demo scripts
- result summaries
- interview notes
- claim boundary
- release tag

## Apple-like Direction

The Apple-like direction is heterogeneous SoC shared memory fabric / unified memory pressure.

This is a problem type, not Apple Silicon simulation.

## NVIDIA-like Direction

The NVIDIA-like direction is GPU-like throughput engine / occupancy vs memory bandwidth.

This is a problem type, not NVIDIA GPU simulation.

## Arm-like Direction

The Arm-like direction is AMBA-inspired NoC QoS / coherency boundary.

This is protocol-inspired exploration, not CHI / AXI / ACE compliance.

## Recommended Next Project

The recommended next project is Project AT-6: Heterogeneous SoC Shared Memory Fabric Lab.

AT-6 is the most natural extension from the Stage 1 memory-system bottleneck portfolio. It also best demonstrates SoC architecture PM, performance modeling, and platform architecture thinking while staying within bounded AT-level synthetic architecture exploration.
