# Project K：Workload-Aware Memory System Bottleneck Characterization MVP

状态：v0.1 source-level report，2026-06-10

Project K v0.1 的目标是在不修改 Project G/H/I/J、不修改 Project H RTL path、不修改
Project I counter schema、不修改 Project J evidence packet、也不修改核心 C++ / SystemC
memory model 的前提下，建立一个第一天可落地的 workload-aware bottleneck
characterization 闭环。

v0.1 复用 Project E simplified banked memory model。Project K 只新增 Python
orchestration、CSV/markdown 输出和显式 bottleneck attribution 规则。

## Scope

Current scope：

- 生成三类 core synthetic workload traces：`streaming`、`stride`、`hot_bank`。
- 使用 Project E-compatible trace schema：
  `workload_name,txn_id,timestamp_ns,initiator_id,command,address,size_bytes`。
- 运行现有 Project E C++ binary。
- 解析 Project E `summary.csv` 和 `trace.csv`。
- 计算 trace-derived features。
- 计算 model-derived metrics。
- 执行四类最小 bottleneck attribution。
- 执行 `bank_count = 4 / 8 / 16` 最小 sweep。
- 生成 CSV 和 generated markdown report。
- 输出 demo PASS marker。

Out of scope：

- 不实现 `tiled_gemm_like` 或 `attention_like_blocked` hard gate。
- 不修改 Project E C++ model。
- 不修改 SystemC model。
- 不修改 Project G/H/I/J。
- 不接入 cache hierarchy、NoC、DRAM timing、HBM channel model、AXI / CHI、
  PMU、Linux perf、NVIDIA Nsight、real GPU kernel 或 full SoC semantics。

## Flow

```text
synthetic workload trace
-> workload feature extraction
-> Project E simplified banked memory model run
-> model metric normalization
-> bottleneck attribution
-> minimal bank_count sweep
-> CSV / markdown report
-> demo PASS
```

## Workloads

| Workload | Pattern | Purpose |
| --- | --- | --- |
| `streaming` | 连续地址访问 | low-conflict baseline。 |
| `stride` | 固定 stride 访问 | 观察 bank mapping sensitivity、stride resonance 和 tail amplification。 |
| `hot_bank` | 地址集中映射到少数 modeled bank，并带 bursty issue pattern | 观察 bank concentration、queueing 和 latency tail。 |

`tiled_gemm_like` 和 `attention_like_blocked` 是 future optional synthetic
access-pattern-inspired traces。即使未来加入，它们也不能被写成真实 GEMM kernel simulator、
真实 Transformer / attention simulator、GPU simulator 或真实 AI kernel performance
验证。

## Metrics

Trace-derived features：

- `total_requests`
- `total_bytes`
- `read_ratio`
- `write_ratio`
- `unique_cacheline_count`
- `reuse_ratio`
- `sequentiality_score`
- `dominant_stride`
- `burstiness_score`
- `bank_entropy`
- `max_bank_share`

`unique_cacheline_count` 和 `reuse_ratio` 只是 locality proxy，不声称真实 cache behavior。
`bank_entropy` 和 `max_bank_share` 基于 Project K synthetic bank mapping / Project E
bank-count assumption，不声称真实 DRAM bank conflict、GPU shared-memory bank conflict 或
silicon counter behavior。

Model-derived metrics：

- `avg_latency_ns`
- `p50_latency_ns`
- `p95_latency_ns`
- `throughput_txn_per_us`
- `queue_delay_ratio`
- `service_delay_ratio`
- `bank_conflict_proxy`
- `p95_p50_latency_ratio`

Field degradation rules：

- 如果 Project E `summary.csv` 没有 `p50_latency_ns`，但 `trace.csv` 有
  `total_latency_ns`，则从 `trace.csv` 计算。
- 如果没有 `queue_delay_ns`，则 `queue_delay_ratio=NA`，并降低 queueing attribution
  confidence。
- 如果没有 `service_latency_ns`，则 `service_delay_ratio=NA`，并降低
  service-latency attribution confidence。
- 如果没有真实 `bank_conflict_ratio`，不要伪造，不叫 ratio；v0.1 统一使用
  `bank_conflict_proxy`。
- 缺失字段写 `NA`，不补造数字。

## Attribution Rules

Project K v0.1 使用显式规则，不使用黑箱模型。

| Rule | Evidence fields | Trigger logic | Recommendation direction |
| --- | --- | --- | --- |
| `bank_conflict_bound` | `max_bank_share`, `bank_entropy`, `bank_conflict_proxy`, `p95_p50_latency_ratio`, `bank_utilization_pct` | `max_bank_share` 高、`bank_entropy` 低、`bank_conflict_proxy` 高或 tail amplification 明显。 | 增加 modeled bank parallelism，或让 synthetic address mapping 更分散。 |
| `queueing_bound` | `queue_delay_ratio`, `avg_queue_occupancy`, `max_queue_occupancy`, `stalled_or_rejected_transactions`, `p95_latency_ns` | queue delay 高，或 queue occupancy / rejected transactions 明显。 | 降低 injection pressure、平滑 request issue，或后续评估 buffering / bank parallelism。 |
| `service_latency_bound` | `service_delay_ratio`, `avg_latency_ns`, `row_hit_ratio_pct`, `queue_delay_ratio` | service delay 高且 queue delay 不高。缺少 `service_delay_ratio` 时不强行触发。 | 降低 modeled service latency 或改善 synthetic locality。 |
| `burstiness_bound` | `burstiness_score`, `p95_p50_latency_ratio`, `max_queue_occupancy`, `stalled_or_rejected_transactions` | burstiness 高且 tail amplification 明显。 | 平滑 burst issue pattern；queue-depth sweep 留到 Project K.2。 |

每个 workload 输出：

- `primary_bottleneck`
- `confidence`: `high / medium / low`
- `evidence_fields`
- `recommendation`
- `claim_boundary`

Recommendation 只表达 expected direction，不写真实硬件收益百分比。

## Minimal Sweep

v0.1 hard sweep：

```text
bank_count = 4 / 8 / 16
```

固定项：

- `queue_depth = 16`
- `address_mapping = word_interleave`
- `base_service_latency_ns = 20`
- `row_hit_latency_ns = 8`
- `row_miss_latency_ns = 40`

Project E CLI 已支持 `word_interleave`、`cacheline_interleave` 和 `row_interleave`，但
v0.1 不把 mapping sweep 作为 hard gate，不实现 `xor_folded`。`queue_depth`、
`service_latency` 和 burstiness-mode sweep 留给 Project K.2。

## Generated Outputs

默认运行：

```bash
python3 examples/lt/tools/demo_project_k_workload_bottleneck_lab.py
```

默认输出目录：

```text
examples/lt/results/project_k_workload_bottleneck/
```

Generated outputs：

- `project_k_workload_bottleneck_summary.csv`
- `project_k_what_if_sweep_summary.csv`
- `project_k_report.md`
- `model_runs/bank_count_4/summary.csv`
- `model_runs/bank_count_4/trace.csv`
- `model_runs/bank_count_8/summary.csv`
- `model_runs/bank_count_8/trace.csv`
- `model_runs/bank_count_16/summary.csv`
- `model_runs/bank_count_16/trace.csv`

Generated input traces 默认放在：

```text
build/examples/lt/project_k_workload_bottleneck_inputs/
```

这些 traces 和 results 是 generated artifacts，不是 source-level validation evidence。

## Acceptance

Project K v0.1 最小验收标准：

- demo 一键跑通。
- 生成 3 类 core workload：`streaming`、`stride`、`hot_bank`。
- 输出 `project_k_workload_bottleneck_summary.csv`，至少 3 行。
- 输出 `project_k_what_if_sweep_summary.csv`，至少 9 行。
- 每类 workload 至少有 trace-derived features。
- 每类 workload 至少有 model-derived metrics。
- 每类 workload 至少有一个 `primary_bottleneck`。
- 每个 attribution 有 `evidence_fields`。
- generated report 包含 claim boundary。
- 不修改 Project G/H/I/J。
- 不修改 Project H RTL path。
- 不修改 Project I counter schema。
- 不修改 Project J evidence packet。
- 不修改 C++ / SystemC model。

成功 PASS marker：

```text
Project K Workload-Aware Memory Bottleneck Characterization MVP PASS
core_workloads=3
summary_rows>=3
sweep_rows>=9
claim_boundary=PASS
```

## Supported Claims

Project K v0.1 支持以下 claim：

- 本项目展示了一种受控 synthetic trace 方法，用于观察 workload access pattern 如何影响
  Project E simplified banked memory model。
- 本项目支持当前模型定义内的趋势级 bottleneck attribution。
- 本项目可以比较 `bank_count` 在当前 simplified model 下对 latency、queueing、
  bank concentration proxy 和 throughput 的相对影响。
- 本项目可以输出 claim-bounded recommendation direction。

## Unsupported Claims

Project K v0.1 不支持以下 claim：

- 不声称真实 GPU 性能。
- 不声称 Apple Silicon 验证。
- 不声称 NVIDIA Nsight 集成。
- 不声称 ARM PMU 验证。
- 不声称 Linux perf 验证。
- 不声称 silicon validation。
- 不声称 production signoff。
- 不声称 full-system cycle accuracy。
- 不声称 full SoC validation。
- 不声称 AXI / CHI protocol compliance。
- 不声称真实 GEMM kernel performance。
- 不声称真实 Transformer / attention kernel performance。
- 不声称 GPU simulation。

## Relationship to Existing Projects

- Project G 定义 validation taxonomy 和 claim boundary；Project K 不修改它。
- Project H 是 local Verilator RTL golden reference path；Project K 不修改 RTL path，也不把
  K 的 trend attribution 写成 RTL validation。
- Project I 是 sample-only profiler / counter interface；Project K 不修改 counter schema，也
  不生成伪 profiler / PMU / Nsight 数据。
- Project J 是 accuracy validation evidence packet；Project K v0.1 不把趋势级结果注入
  Project J claim matrix 或 evidence table。

## Future Work

Project K.2 可以考虑：

- 增加 `tiled_gemm_like` synthetic access-pattern-inspired trace。
- 增加 `attention_like_blocked` synthetic access-pattern-inspired trace。
- 增加 `cacheline_interleave` / `row_interleave` mapping sweep。
- 在模型明确支持后再考虑 `xor_folded` mapping。
- 增加 `queue_depth` sweep。
- 增加 `service_latency` sweep。
- 增加 burstiness-mode sweep。
- 后续如需接入 Project J，必须先定义 evidence status，不能把 synthetic trend result 写成
  accuracy validation。
