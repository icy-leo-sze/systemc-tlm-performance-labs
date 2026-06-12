# SystemC/TLM 架构性能建模作品集

这是一个边界清晰的 SystemC/TLM 早期 SoC 性能建模作品集，覆盖从 LT workload
bottleneck analysis 到 AT transaction timing、arbitration、QoS-like sensitivity、
SLA violation analysis、cache-like MSHR pressure、memory-system backpressure /
QoS collapse，以及可复现 evidence packaging 的完整链路。

> 架构建模只有在 assumptions、metrics 和 claim boundaries 可见时才有价值。

本仓库展示的是一条系统级 architecture modeling workflow：

```text
workload pattern -> transaction model -> latency / throughput / fairness / SLA metrics -> bottleneck diagnosis -> evidence-driven recommendation
```

它面向可审查的 architecture reasoning 和作品集表达，不是 production simulator，也不是
protocol-complete model。

## 从这里开始

| 读者目标 | 建议入口 | 为什么 |
| --- | --- | --- |
| 理解整体架构叙事 | [`docs/portfolio_architecture_story.md`](docs/portfolio_architecture_story.md) | 把 LT 和 AT labs 串成一条作品集主线 |
| 审查可复现证据 | [`docs/portfolio_evidence_pack.md`](docs/portfolio_evidence_pack.md) | 解释 validation flow 和 generated artifacts |
| 查看指标摘要 | [`docs/generated/portfolio_evidence_summary.md`](docs/generated/portfolio_evidence_summary.md) | 汇总 K/L/AT-1/AT-2/AT-3/AT-4/AT-5 的 CSV outputs |
| 准备面试讨论 | [`INTERVIEW_NOTES.md`](INTERVIEW_NOTES.md) | 提供作品集 pitch 和 bounded claim language |
| 运行 portfolio validation | [`tools/run_portfolio_validation.py`](tools/run_portfolio_validation.py) | 检查主线项目的 PASS markers |

## 这个作品集展示什么

- 在明确 synthetic workload 边界下进行 LT workload bottleneck characterization。
- 用 generated metrics 支撑 memory architecture recommendation，而不是手写结论。
- 用 AT four-phase transaction timing 暴露 request / response phase visibility。
- 分析 multi-initiator arbitration、contention、fairness，以及 p95 / p99 tail latency。
- 扫描 QoS-like weighted arbitration sensitivity 和 SLA violation。
- 隔离 locality、MSHR-like pressure、shared-resource interference 和 memory-service bottleneck。
- 展示 downstream saturation 下 backpressure propagation 和 QoS collapse。
- AT-5 demonstrates that priority policies can redistribute contention but cannot create downstream service capacity.
- 通过 validation harness 和 generated summary 形成可复现 evidence packaging。
- 展示 architecture judgment：知道模型能支持什么，也知道模型不能支持什么。

## 建模链路

| Stage | Project | Modeling Level | Main Question | Primary Evidence |
| --- | --- | --- | --- | --- |
| 1 | Project K | LT | 哪些 workload patterns 会暴露 memory bottlenecks？ | workload summary / sweep / report |
| 2 | Project L | LT | 哪些 architecture action 被指标支持？ | recommendation CSV / report |
| 3 | Project AT-1 | AT | transaction phases 如何暴露 timing 和 back-pressure？ | AT-1 summary / traces |
| 4 | Project AT-2 | AT | arbitration policies 如何影响 fairness 和 tail latency？ | policy summary / traces |
| 5 | Project AT-3 | AT | QoS-like weights、queue/service constraints 如何影响 SLA violations？ | policy sweep / recommendations |
| 6 | Project AT-4 | AT | locality、MSHR-like pressure、shared interference 和 memory service bottleneck 如何相互作用？ | policy sweep / recommendations |
| 7 | Project AT-5 | AT | downstream saturation 和 bounded queues 何时让 QoS policy 失效？ | policy sweep / recommendations |
| 8 | Project P / S | Portfolio Evidence | 整条建模主线是否可审查、可复现？ | validation harness / generated evidence summary |

## 快速验证

```bash
python3 tools/generate_portfolio_evidence_summary.py --strict
python3 tools/run_portfolio_validation.py --at-build-dir build-at
```

第二条 AT validation command 假设 `build-at` 已经完成 configure；harness 会使用
明确的 named project targets 构建 AT-1/2/3/4/5，不依赖 legacy aggregate `at` target。

## AT 构建参考

首页快速路径使用独立的 `examples/at` build directory，避免把 root CMake 作为唯一入口。

```bash
cmake -S examples/at -B build-at \
  -DUSER_SYSTEMC_INCLUDE_DIR=$HOME/local/systemc/include \
  -DUSER_SYSTEMC_LIB_DIR=$HOME/local/systemc/lib
cmake --build build-at --target project_at1_four_phase_memory_timing -j
cmake --build build-at --target project_at2_multi_initiator_arbitration -j
cmake --build build-at --target project_at3_qos_sensitivity_sla -j
cmake --build build-at --target project_at4_cache_mshr_pressure -j
cmake --build build-at --target project_at5_backpressure_qos_collapse -j
```

## Claim Boundary

这个作品集支持有边界的 early architecture modeling discussion。它不声称：

- AXI / CHI protocol compliance
- cycle accuracy
- 真实 NoC 建模
- cache coherence modeling
- 真实 DRAM timing
- silicon validation
- production signoff
- GPU、LLM、Transformer、GEMM、FlashAttention、Apple、NVIDIA 或 Arm 产品的真实 workload performance

本仓库的价值在于建模纪律：定义 workload assumptions，暴露 timing 和 contention signals，
生成 metrics，并且只在 evidence boundary 内做 architecture recommendation。

## Repository Map

| Area | Path | Purpose |
| --- | --- | --- |
| LT labs | [`examples/lt/`](examples/lt/) | Loosely-timed memory bottleneck 与 recommendation labs |
| AT labs | [`examples/at/`](examples/at/) | Approximately-timed transaction、arbitration、QoS、SLA、MSHR-like pressure 与 backpressure labs |
| Portfolio docs | [`docs/portfolio_architecture_story.md`](docs/portfolio_architecture_story.md) | 高层 architecture narrative |
| Evidence pack | [`docs/portfolio_evidence_pack.md`](docs/portfolio_evidence_pack.md) | Reproducibility 和 artifact map |
| Generated evidence | [`docs/generated/portfolio_evidence_summary.md`](docs/generated/portfolio_evidence_summary.md) | 从 CSV outputs 生成的 summary |
| Validation tools | [`tools/`](tools/) | Portfolio-level validation 和 evidence generation |
| Interview notes | [`INTERVIEW_NOTES.md`](INTERVIEW_NOTES.md) | 有边界的 portfolio pitch 和 discussion notes |

## Project Map

| Project | 当前角色 | 主要产物 | 当前 claim 边界 |
| --- | --- | --- | --- |
| LT / AT labs | 主实验链路 | `examples/lt`、`examples/at`、demos、sweeps、comparison reports | architecture-level performance workflow 和 AT phase observability；不是 protocol-complete model，也不是 cycle-accuracy evidence |
| Project AT-1 | Four-phase AT memory transaction timing | `examples/at/four_phase_memory_timing/`、`demo_project_at1_four_phase_memory_timing.py`、`project_at1_summary.csv`、`project_at1_report.md` | 在 synthetic scenarios 下观察 TLM-2.0 AT timing、target queueing、back-pressure 和 request/response phase visibility |
| Project AT-2 | Multi-initiator AT arbitration and contention | `examples/at/multi_initiator_arbitration/`、`project_at2_summary.csv`、`project_at2_policy_summary.csv`、`project_at2_report.md` | 观察 shared interconnect / memory-target contention、arbitration policy effects、fairness、p95 / p99 tail latency 和 back-pressure |
| Project AT-3 | QoS sensitivity and SLA violation analysis | `examples/at/qos_sensitivity_sla/`、`project_at3_policy_sweep.csv`、`project_at3_recommendations.csv`、`project_at3_report.md` | 分析 QoS-like weighted arbitration sensitivity、SLA violation rate、queue depth / service latency sensitivity 和 bounded recommendation |
| Project AT-4 | Cache-like Shared Resource and MSHR Pressure Lab | `examples/at/project_at4_cache_mshr_pressure.cpp`、`project_at4_summary.csv`、`project_at4_policy_sweep.csv`、`project_at4_recommendations.csv`、`project_at4_report.md` | Models locality, MSHR-like pressure, shared-resource interference, and diminishing returns at AT-level without claiming real cache coherence or cycle accuracy. |
| Project AT-5 | Memory System Backpressure and QoS Collapse Lab | `examples/at/project_at5_backpressure_qos_collapse.cpp`、`project_at5_summary.csv`、`project_at5_policy_sweep.csv`、`project_at5_recommendations.csv`、`project_at5_report.md` | 分析 bounded queues、downstream saturation、backpressure propagation 和 QoS collapse；不是 real NoC、AXI/CHI、DRAM controller 或 cycle-accurate model |
| Project B / C | Normalized trace replay 和 gem5 SE-derived trace replay | normalized trace inputs、`summary.csv`、`comparison.md` | gem5 SE 只作为 offline trace context；`timestamp_ns` 是 normalized ordering hint，不是 gem5 timing |
| Project D | Standalone C++ trace replay engine | C++ replay binary、Python vs C++ summary equivalence check | replay metric equivalence；不接 SystemC kernel，不做 live co-simulation |
| Project E | Standalone C++ banked memory controller queueing model | queueing summary、tail latency、bank utilization、reject statistics | 用于 queueing 和 bank conflict reasoning 的 memory subsystem abstraction |
| Project F | gem5 stats trend correlation report | `correlation_summary.csv`、`correlation_report.md` | selected workloads 下的 qualitative trend-level comparison |
| Project G | Golden reference correlation roadmap | [`docs/project_g_golden_reference_correlation_plan.md`](docs/project_g_golden_reference_correlation_plan.md)、[`docs/accuracy_validation_taxonomy.md`](docs/accuracy_validation_taxonomy.md) | roadmap / taxonomy / claim-boundary document；不新增 observed error claim |
| Project H | Verilator RTL golden model MVP | [`docs/project_h_verilator_rtl_golden_model_report.md`](docs/project_h_verilator_rtl_golden_model_report.md)、`examples/lt/rtl_banked_memory_controller/`、`demo_rtl_golden_model_lab.py` | 只针对本仓库 banked memory controller 的 local Verilator RTL reference |
| Project I | Profiler / counter correlation interface | [`docs/project_i_profiler_counter_correlation_interface_report.md`](docs/project_i_profiler_counter_correlation_interface_report.md)、`demo_profiler_counter_correlation_lab.py` | sample-only profiler/counter schema 和 ingest interface |
| Project J | Accuracy validation evidence packet | [`docs/project_j_accuracy_validation_report.md`](docs/project_j_accuracy_validation_report.md)、`demo_accuracy_validation_packet.py` | claim-bounded evidence packet，显式记录 support status 和 missing evidence |
| Project K | Workload-aware memory bottleneck characterization | [`docs/project_k_workload_aware_memory_bottleneck_report.md`](docs/project_k_workload_aware_memory_bottleneck_report.md)、`demo_project_k_workload_bottleneck_lab.py` | synthetic trace + simplified banked model 的 trend-level bottleneck attribution |
| Project L | Evidence-driven memory architecture recommendation | `examples/lt/results/project_l_memory_architecture_recommendation/project_l_recommendations.csv`、`project_l_recommendation_report.md` | 基于 Project K evidence 的 bounded recommendation layer |
| Project P / S | Portfolio evidence pack and validation harness | [`docs/portfolio_evidence_pack.md`](docs/portfolio_evidence_pack.md)、[`docs/generated/portfolio_evidence_summary.md`](docs/generated/portfolio_evidence_summary.md)、`tools/run_portfolio_validation.py` | 对 K/L/AT-1/AT-2/AT-3/AT-4/AT-5 做 portfolio-level evidence packaging 和 PASS-marker validation |

## Evidence Chain

当前 portfolio 主线是：

```text
LT -> AT timing -> arbitration -> QoS -> cache-like MSHR pressure -> backpressure QoS collapse -> portfolio validation
```

底层 evidence chain 仍保持：

```text
workload -> trace -> metrics -> sweep -> comparison -> demo -> evidence summary -> validation harness
```

Projects G/H/I/J 使用的 validation-oriented line 是：

```text
workload
-> aligned measurement region
-> model metrics
-> reference metrics
-> error formula
-> error budget
-> validation packet
```

每个 supported claim 都应该绑定 workload assumption、metric definition、evidence source
和明确的 unsupported boundary。

## 关键结果快照

下面是已审查的实验快照，不是 hardware timing claim。

| Area | Scenario | Result |
| --- | --- | --- |
| LT | `stride=4` 到 `stride=16` | `bank_conflict_ratio_pct` 从 `46.875%` 上升到 `98.438%`；`avg_delay_ns` 从 `164.688 ns` 上升到 `185.312 ns` |
| LT Phase 16A | `sequential` / `stride` / `hotspot` | `stride bank_conflict_ratio_pct = 98.438%`，高于 `sequential` 和 `hotspot` |
| LT Project B | `sample_sequential` / `sample_stride` | normalized trace replay 复现同类 bank-conflict signal：`sample_stride bank_conflict_ratio_pct = 98.438%` |
| LT Project D | C++ replay vs Python replay | standalone C++ replay 输出 `trace.csv` / `summary.csv`，并通过 Python vs C++ replay summary equivalence |
| LT Project E | `sequential_scan` / `stride_scan` / `hot_bank_stress` | `sequential_scan p99 = 60.000 ns`，`stride_scan p99 = 424.000 ns`，`hot_bank_stress p99 = 960.000 ns`，`stalled_or_rejected_transactions = 68` |
| LT Project F | `sequential` vs `stride` | gem5 `stats.txt` 与 replay / Project E summaries 生成 qualitative trend-level report |
| Project AT-1 | `sequential_moderate_gap` | `avg_request_accept_latency_ns = 1.000`，`backpressure_events = 0` |
| Project AT-1 | `bursty_queue_pressure` | `avg_initiator_blocked_ns = 9.167`，`backpressure_events = 10` |
| Project AT-1 | `hotspot_backpressure` | `avg_initiator_blocked_ns = 14.667`，`backpressure_events = 11` |
| AT arbitration baseline | `fifo` | `complete_transactions = 4` |
| AT arbitration baseline | `priority_101` | `101xxx avg = 1.000 ns`，`102xxx avg = 6.000 ns` |
| AT arbitration baseline | `priority_102` | `102xxx avg = 1.000 ns`，`101xxx avg = 6.000 ns` |
| Project AT-5 | `downstream_saturation_qos_collapse` | `service_utilization = 1.000`，`queue_full_events = 105`，recommendation 转向 `reduce_memory_service_latency` |
| Project K | workload bottleneck characterization | hard gate：`total_workloads=5`、`sweep_rows=45`、`schema_version=k0.2` |
| Project L | recommendation layer | hard gate：`recommendation_rows=5`、`schema_version=l0.1`、`claim_boundary=PASS` |

## 常用运行命令

LT one-command demo：

```bash
python3 examples/lt/tools/demo_performance_lab.py
```

Project K workload bottleneck characterization：

```bash
python3 examples/lt/tools/demo_project_k_workload_bottleneck_lab.py
```

Project AT-1：

```bash
python3 examples/at/tools/demo_project_at1_four_phase_memory_timing.py
```

Project AT-2：

```bash
python3 examples/at/tools/demo_project_at2_multi_initiator_arbitration.py \
  --build-dir build-at
```

Project AT-3：

```bash
python3 examples/at/tools/demo_project_at3_qos_sensitivity_sla.py \
  --build-dir build-at
```

Project AT-4：

```bash
python3 examples/at/tools/demo_at4_cache_mshr_pressure.py \
  --at-build-dir build-at
```

Project AT-5：

```bash
python3 -B examples/at/tools/demo_at5_backpressure_qos_collapse.py \
  --at-build-dir build-at
```

Headless regression harness：

```bash
bash scripts/run_all_regressions.sh
cat artifacts/regression_summary.md
```

Project H 需要 Verilator-capable environment：

```bash
python3 examples/lt/tools/demo_rtl_golden_model_lab.py
```

如果没有 Verilator，Project H 应报告 prerequisite failure，而不是 end-to-end RTL PASS。

## Validation Ladder

| Level | 本仓库中的含义 | 代表项目 | 可支持的说法 |
| --- | --- | --- | --- |
| Level 0 Internal consistency | implementation consistency、schema stability、demo/regression health | Project D、Project I sample smoke、headless regression | replay / schema / report flow 可复现 |
| Level 1 Trend correlation | selected workloads 下的 direction、ranking 或 qualitative trend | Project F | gem5 stats context 与 replay/model summaries 可以在趋势层面比较 |
| Level 2 Quantitative correlation | aligned metric、reference 和 explicit error budget | Project H generated correlation rows, if available | local model-vs-RTL metric error 可计算 |
| Level 3 Bounded golden reference validation | 针对 specific block、workload、metric 的 bounded reference source | Project H | 只支持 local banked-memory-controller Verilator RTL reference |
| Level 4 Enterprise production signoff | enterprise release / signoff process | Not supported | unsupported / out of scope |

Project J 不补造缺失 reference data。它记录已有 evidence source、metric、
error-budget state 和 support status；缺失的 generated results 保持 `not_generated` 或
sample-only state。

## 路线图

后续方向保持小步、可度量、validation-oriented：

- AT multi-target path。
- AT response scheduling。
- Outstanding transaction depth。
- 等价 workloads 下的 LT-vs-AT comparison。

这些是 future directions，不是当前已完成能力。

## License And Notices

License 和 third-party notice 见 [`LICENSE`](LICENSE) 和 [`NOTICE`](NOTICE)。
