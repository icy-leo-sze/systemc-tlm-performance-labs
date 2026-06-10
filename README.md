# SystemC/TLM Architecture Performance Labs

## 项目定位

本仓库是一个 SystemC/TLM 架构级性能建模与验证证据实验室。项目从 LT 架构级性能工作流
起步，并逐步扩展到 AT phase-level timing refinement、standalone C++ replay / memory
subsystem modeling、bounded RTL reference correlation，以及 profiler / counter / evidence
packet 接口。部分 LT 示例保留了 Renode-SystemC 集成基础，但当前项目的重点不是 fork
来源，而是一条可重复、可审计的实验链路：

```text
workload -> trace -> metrics -> sweep -> comparison -> demo
```

新增的 validation 主线把这条链路扩展为：

```text
workload
-> aligned measurement region
-> model metrics
-> reference metrics
-> error formula
-> error budget
-> validation packet
```

本项目不是 cycle-accurate AXI、CHI 或 NoC 模型，也不声称 production signoff、
silicon validation、full-system cycle accuracy 或 full SoC validation。

## 项目目录

| 实验室 | 路径 | 抽象层级 | 主要能力 | 演示命令 |
| --- | --- | --- | --- | --- |
| LT 性能实验室 | [`examples/lt`](examples/lt) | LT | 延迟分解、workload sweep、memory access pattern sweep、normalized trace replay、gem5 SE-derived trace replay、standalone C++ replay engine、banked memory controller queueing model、gem5 stats trend correlation report | `python3 examples/lt/tools/demo_performance_lab.py` |
| AT 仲裁实验室 | [`examples/at`](examples/at) | AT | TLM phase trace 和 arbitration policy sweep | `python3 examples/at/tools/demo_at_lab.py --binary ./build/examples/at/at` |

详细说明：

- LT 工作流：[`examples/lt/README_performance_lab.md`](examples/lt/README_performance_lab.md)
- AT 工作流：[`examples/at/README.md`](examples/at/README.md)

LT lab 现在支持六类边界清晰的流量来源、replay backend 和 trend report：

1. 内建 synthetic memory access pattern sweep。
2. normalized external trace replay MVP。
3. gem5 SE-derived normalized traces。
4. standalone C++ trace replay engine。
5. standalone C++ banked memory controller queueing model。
6. gem5 SE stats vs replay model trend correlation report。

这条演进线是：

```text
Python trace replay
-> gem5 SE-derived trace
-> standalone C++ replay engine
-> banked memory controller queueing model
-> gem5 stats trend correlation report
```

前四个 replay / model backend 都保持同一条 `trace -> metrics -> summary.csv ->
comparison.md` 链路。Project C 中 gem5 只作为 offline trace producer，SystemC/TLM lab
作为 replay and analysis backend。Project D 则把 Project B / Project C 当前 Python
replay 的核心 metrics 逻辑迁移到 standalone C++ replay engine；Python 仍负责 demo
orchestration、Python vs C++ metrics equivalence check 和 `comparison.md` 生成。
Project F 在这些 generated summaries 之上生成 qualitative trend report，不改变既有
输出语义。详细说明见
[`examples/lt/README_performance_lab.md`](examples/lt/README_performance_lab.md)。

## Project Map

| Project | 当前角色 | 主要产物 | 当前 claim 边界 |
| --- | --- | --- | --- |
| LT / AT labs | 主实验链路 | `examples/lt`、`examples/at`、demo、sweep、comparison report | architecture-level performance workflow 和 AT phase observability；不是 protocol-complete 或 cycle-accurate model |
| Project B / C | normalized trace replay 和 gem5 SE-derived trace replay | normalized trace、`summary.csv`、`comparison.md` | gem5 SE 是 offline trace producer；`timestamp_ns` 是 normalized ordering hint，不是 gem5 timing |
| Project D | standalone C++ trace replay engine | C++ replay binary、Python vs C++ summary equivalence check | replay metrics equivalence；不接 SystemC kernel，不做 live co-simulation |
| Project E | standalone C++ banked memory controller queueing model | queueing summary、tail latency、bank utilization、reject statistics | memory subsystem abstraction；不是 JEDEC DRAM timing 或 production controller |
| Project F | gem5 stats trend correlation report | `correlation_summary.csv`、`correlation_report.md` | qualitative trend-level correlation；不是 RTL、profiler、counter 或 silicon validation |
| Project G | Golden Reference Correlation Roadmap | [`docs/project_g_golden_reference_correlation_plan.md`](docs/project_g_golden_reference_correlation_plan.md)、[`docs/accuracy_validation_taxonomy.md`](docs/accuracy_validation_taxonomy.md) | roadmap / taxonomy / claim-boundary document；不新增模型或 observed error |
| Project H | Verilator RTL Golden Model MVP | [`docs/project_h_verilator_rtl_golden_model_report.md`](docs/project_h_verilator_rtl_golden_model_report.md)、`examples/lt/rtl_banked_memory_controller/`、`examples/lt/tools/demo_rtl_golden_model_lab.py` | local Verilator RTL reference for banked memory controller only；不是 full SoC、silicon 或 production RTL validation |
| Project I | Profiler / Counter Correlation Interface | [`docs/project_i_profiler_counter_correlation_interface_report.md`](docs/project_i_profiler_counter_correlation_interface_report.md)、`examples/lt/tools/demo_profiler_counter_correlation_lab.py` | sample-only profiler/counter schema and ingest interface；不是 hardware counter validation |
| Project J | Accuracy Validation Evidence Packet | [`docs/project_j_accuracy_validation_report.md`](docs/project_j_accuracy_validation_report.md)、`examples/lt/tools/demo_accuracy_validation_packet.py` | claim-bounded evidence packet；不是 silicon validation、production signoff 或 full-system cycle accuracy |
| Project K | Workload-aware memory bottleneck characterization | [`docs/project_k_workload_aware_memory_bottleneck_report.md`](docs/project_k_workload_aware_memory_bottleneck_report.md)、`examples/lt/tools/demo_project_k_workload_bottleneck_lab.py` | synthetic trace + Project E simplified banked model 的趋势级 bottleneck attribution；不是 GPU、AI kernel、silicon 或 hardware-counter validation |

## Project D：Standalone C++ Trace Replay Engine

Project D 已在 Ubuntu 验证通过。它是一个 standalone C++ trace replay engine，输入
Project B / Project C 的 normalized trace CSV，输出 `trace.csv` 和 `summary.csv`。
Python 仍然负责 orchestration、Python vs C++ metrics equivalence check，以及
`comparison.md` 生成。

验证命令：

```bash
cmake -S examples/lt/replay_cpp -B build/examples/lt/replay_cpp
cmake --build build/examples/lt/replay_cpp -j"$(nproc)"

python3 examples/lt/tools/demo_cpp_trace_replay_lab.py
```

已验证输出：

```text
[replay-cpp] Project D standalone C++ trace replay PASS
[compare] Python vs C++ replay summary equivalence PASS
[demo-cpp] Project D Standalone C++ Trace Replay MVP PASS
```

Project D 不接 SystemC kernel，不做 gem5 live co-simulation，也不声称 cycle accuracy。

## Project E：Banked Memory Controller Queueing Model

Project E 是新增的 standalone C++ memory subsystem abstraction。它复用 normalized
trace CSV 输入，把模型升级为 banked memory controller + queueing model，支持
`bank_count`、`queue_depth`、per-bank `busy_until_ns`、address-to-bank mapping、
row-buffer hit/miss、queue occupancy、tail latency、bank utilization、row hit ratio、
throughput 和 queue full reject 统计。

Python 只负责 demo orchestration、生成 demo input traces，以及从 C++ `summary.csv`
生成 `comparison.md`。

验证命令：

```bash
cmake -S examples/lt/banked_memory_controller_cpp \
  -B build/examples/lt/banked_memory_controller_cpp
cmake --build build/examples/lt/banked_memory_controller_cpp

python3 examples/lt/tools/demo_banked_memory_controller_lab.py
```

默认输出：

```text
examples/lt/results/project_e_banked_memory_controller/trace.csv
examples/lt/results/project_e_banked_memory_controller/summary.csv
examples/lt/results/project_e_banked_memory_controller/comparison.md
```

详细说明见
[`docs/project_e_banked_memory_controller_report.md`](docs/project_e_banked_memory_controller_report.md)。

Project E 第一版不接 SystemC kernel，不做 gem5 live co-simulation，不做 JEDEC DRAM
timing，不实现 AXI、CHI 或 NoC protocol，也不声称 cycle accuracy。

## Project F：gem5 Stats Trend Correlation Report

Project F compares gem5 SE `stats.txt` with replay summaries at trend level and
documents model boundaries. 它生成 `correlation_summary.csv` 和
`correlation_report.md`，用于解释 `sequential` vs `stride` 的趋势是否一致。

运行命令：

```bash
python3 examples/lt/tools/demo_gem5_stats_correlation_lab.py
```

默认输出：

```text
examples/lt/results/project_f_gem5_stats_correlation/correlation_summary.csv
examples/lt/results/project_f_gem5_stats_correlation/correlation_report.md
```

详细说明见
[`docs/project_f_gem5_stats_correlation_report.md`](docs/project_f_gem5_stats_correlation_report.md)。

Project F 不做 gem5 live co-simulation，不声称 cycle accuracy，不声称 RTL / silicon /
profiler correlation。Project B / C normalized trace 中的 `timestamp_ns` 仍然只是
normalized issue-time / ordering hint，不是 gem5 timing。

## Project K：Workload-Aware Bottleneck Characterization

Project K 用三类 core synthetic workload traces（`streaming`、`stride`、`hot_bank`）和两类
optional synthetic access-pattern-inspired traces（`tiled_gemm_like`、
`attention_like_blocked`）复用 Project E simplified banked memory model，把 access
pattern 转成 trace-derived features、model-derived metrics、bottleneck attribution、
mapping sensitivity sweep 和 bounded recommendation。

运行命令：

```bash
python3 examples/lt/tools/demo_project_k_workload_bottleneck_lab.py
```

关键输出：

```text
examples/lt/results/project_k_workload_bottleneck/project_k_workload_bottleneck_summary.csv
examples/lt/results/project_k_workload_bottleneck/project_k_what_if_sweep_summary.csv
examples/lt/results/project_k_workload_bottleneck/project_k_report.md
```

Project K 只支持 synthetic trace 上的趋势级 bottleneck attribution，不声称真实 GPU
性能、真实 GEMM / attention / FlashAttention / LLM kernel performance、PMU / perf /
Nsight correlation、silicon validation 或 AXI / CHI protocol compliance。

## 为什么有价值

LT 主线展示的是架构级性能分析工作流：workload knobs、transaction trace
instrumentation、延迟分解、workload sweep 和自动生成的 comparison report。

AT 主线展示的是 TLM-2.0 base protocol phase 的 timing observability，包括
`BEGIN_REQ`、`END_REQ`、`BEGIN_RESP` 和 `END_RESP`。它也展示了一个小型 arbitration
policy knob 如何改变 request-accept latency。

这两个实验室合在一起，形成一条从架构级工作流到 AT timing refinement 的演进
路径，但不声称 protocol completeness 或 cycle accuracy。

Project G/H/I/J 在这条主线之后增加 validation evidence discipline：先定义 claim
taxonomy，再用 local Verilator RTL reference 做 bounded block-level comparison，预留
profiler / counter ingest interface，最后用 evidence packet 汇总哪些 claim 有证据、哪些
claim 仍然 unsupported。

## 快速开始

从仓库根目录构建 AT lab：

```bash
cmake -S examples/at -B build/examples/at
cmake --build build/examples/at
```

如果默认搜索路径找不到 SystemC，可以显式传入 SystemC 路径：

```bash
cmake -S examples/at -B build/examples/at \
  -DUSER_SYSTEMC_LIB_DIR=<absolute path to SystemC lib> \
  -DUSER_SYSTEMC_INCLUDE_DIR=<absolute path to SystemC include>
cmake --build build/examples/at
```

运行 AT one-command demo：

```bash
python3 examples/at/tools/demo_at_lab.py \
  --binary ./build/examples/at/at
```

运行 LT one-command demo：

```bash
python3 examples/lt/tools/demo_performance_lab.py
```

运行 headless regression harness：

```bash
bash scripts/run_all_regressions.sh
cat artifacts/regression_summary.md
```

LT 的 Renode 配置、生成文件和结果解释见
[`examples/lt/README_performance_lab.md`](examples/lt/README_performance_lab.md)。

## G/H/I/J quick commands

Project G 是文档路线图，快速检查：

```bash
test -f docs/project_g_golden_reference_correlation_plan.md
test -f docs/accuracy_validation_taxonomy.md
```

Project H 需要本机或 Ubuntu 环境安装 Verilator：

```bash
python3 examples/lt/tools/demo_rtl_golden_model_lab.py
```

手动 build/run Project H：

```bash
cmake -S examples/lt/rtl_banked_memory_controller \
  -B build/examples/lt/rtl_banked_memory_controller
cmake --build build/examples/lt/rtl_banked_memory_controller

python3 examples/lt/tools/demo_rtl_golden_model_lab.py --no-build
```

如果没有 Verilator，Project H demo 应报告 prerequisite failure，而不是 correlation PASS。

Project I sample-only profiler / counter interface smoke test：

```bash
python3 examples/lt/tools/demo_profiler_counter_correlation_lab.py
```

Project J evidence packet demo：

```bash
python3 examples/lt/tools/demo_accuracy_validation_packet.py
```

## 关键结果快照

下面是已验证的实验快照，不是硬件 timing claim。

| 实验室 | 场景 | 结果 |
| --- | --- | --- |
| LT | `stride=4` 到 `stride=16` | `bank_conflict_ratio_pct` 从 `46.875%` 上升到 `98.438%`；`avg_delay_ns` 从 `164.688 ns` 上升到 `185.312 ns` |
| LT Phase 16A | `sequential` / `stride` / `hotspot` | `stride` 的 `bank_conflict_ratio_pct = 98.438%`，明显高于 `sequential` 和 `hotspot` |
| LT Project B | `sample_sequential` / `sample_stride` | normalized trace replay 复现同类 bank conflict 观测：`sample_stride bank_conflict_ratio_pct = 98.438%` |
| LT Project D | C++ replay vs Python replay | standalone C++ replay 输出 `trace.csv` / `summary.csv`，并通过 Python vs C++ replay summary equivalence check |
| LT Project E | `sequential_scan` / `stride_scan` / `hot_bank_stress` | standalone C++ banked memory controller + queueing model：`sequential_scan p99 = 60.000 ns`，`stride_scan p99 = 424.000 ns`，`hot_bank_stress p99 = 960.000 ns` 且 `stalled_or_rejected_transactions = 68` |
| LT Project F | `sequential` vs `stride` | gem5 `stats.txt` 与 replay / Project E summary 生成 qualitative trend-level report；不比较绝对 cycle，不声称 RTL / silicon / profiler correlation |
| Project G | validation roadmap | 定义 golden-reference correlation path 和 Level 0 到 Level 4 validation taxonomy；不提供 observed error |
| Project H | bounded RTL reference | local Verilator RTL banked memory controller reference path；只覆盖本仓库的 banked memory controller micro-model |
| Project I | counter interface | sample-only counter schema、metadata join、normalization 和 report formatting；不是 hardware counter validation |
| Project J | evidence packet | 把 claim、evidence source、reference、metric、error budget 和 status 收束到 validation packet；不是 silicon validation |
| AT | `fifo` | `complete_transactions = 4` |
| AT | `priority_101` | `101xxx` 更快被接受：`101xxx avg = 1.000 ns`，`102xxx avg = 6.000 ns` |
| AT | `priority_102` | `102xxx` 更快被接受：`102xxx avg = 1.000 ns`，`101xxx avg = 6.000 ns` |

## Validation Ladder / Evidence Chain

Project G 把当前证据分成可升级的 validation ladder。每一级都必须绑定 workload、region、
metric definition、reference source 和 error budget，不能只靠数字相似来扩大 claim。

| Level | 当前项目中的含义 | 当前代表项目 | 可支持的说法 |
| --- | --- | --- | --- |
| Level 0 Internal consistency | implementation consistency、schema stability、demo/regression health | Project D、Project I sample smoke、headless regression | replay / schema / report flow 可复现 |
| Level 1 Trend correlation | selected workloads 下的方向性、ranking 或 qualitative trend | Project F | gem5 stats context 与 replay/model summary 在趋势层面可比较 |
| Level 2 Quantitative correlation | aligned metric + reference + explicit error budget | Project H generated correlation rows, if available | local model-vs-RTL metric error 可计算 |
| Level 3 Bounded golden reference validation | 有边界的 reference source 支撑特定 block、workload、metric claim | Project H | local banked memory controller Verilator RTL reference only |
| Level 4 Enterprise production signoff | 企业级 release / signoff process | 当前不支持 | unsupported / out of scope |

当前 evidence chain 是：

```text
Project G taxonomy
-> Project H bounded local RTL reference path
-> Project I sample-only counter interface
-> Project J claim-bounded evidence packet
```

Project J 不新增 reference data，不补造缺失结果。它把已有 evidence source、metric、error
budget 和 status 汇总为 evidence packet；如果 Project H / I generated results 缺失，应记录为
`not_generated` 或 sample-only state，而不是把缺失数据写成验证通过。

## What This Project Can Claim

- 这是一个 SystemC/TLM architecture performance modeling lab，核心链路是
  `workload -> trace -> metrics -> sweep -> comparison -> demo`。
- LT lab 支持 architecture-level latency decomposition、workload sweep、normalized trace
  replay、standalone C++ replay 和 banked memory controller queueing analysis。
- AT lab 支持 TLM-2.0 base protocol phase trace 和 arbitration observability。
- Project D 支持 Python vs C++ replay summary equivalence。
- Project E 支持 bounded standalone C++ memory subsystem queueing model analysis。
- Project F 支持 selected workloads 下的 gem5 stats trend-level correlation report。
- Project G 支持 golden-reference roadmap、accuracy validation taxonomy 和 claim-boundary
  definition。
- Project H 支持 local Verilator RTL reference path for banked memory controller only，并在
  Verilator 环境和 generated correlation rows 存在时支持 bounded model-vs-RTL metric
  comparison。
- Project I 支持 sample-only profiler/counter ingestion interface、schema validation、
  metadata join、normalization 和 report formatting。
- Project J 支持 evidence packet，把 claim、evidence source、reference、metric、
  error-budget state 和 support status 对齐记录。

## What This Project Does Not Claim

- 不声称 production signoff。
- 不声称 silicon validation。
- 不声称 full-system cycle accuracy。
- 不声称 full SoC validation。
- 不声称 AXI、CHI、NoC protocol compliance 或 production interconnect support。
- 不声称 real DRAM timing validation 或 real product memory-controller validation。
- 不声称 gem5-SystemC live co-simulation。
- 不声称 full-system Linux timing validation。
- 不把 Project H 的 local Verilator RTL banked memory controller reference 扩大成 full
  SoC、silicon 或 production RTL validation。
- 不把 Project I 的 sample synthetic counter data 说成 hardware counter validation。
- 不把 Project J 的 evidence packet 说成 silicon validation、production release readiness
  或 full-system accuracy proof。

## 路线图

后续方向保持小步、可验证：

- AT multi-target path。
- AT response scheduling。
- outstanding transaction depth。
- 等价 workload 下的 LT vs AT 对比。

这些都是未来方向，不是当前已完成能力。

## 许可证和致谢

部分 LT 示例基于 Renode-SystemC 集成基础，上游 notice 已按需要保留。
详见 [`LICENSE`](LICENSE) 和 [`NOTICE`](NOTICE)。
