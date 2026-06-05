# Validation Plan

状态：2026-06-05

本文档定义 `SystemC/TLM Architecture Performance Labs` 的验证策略。目标是把当前
教学实验推进成一个可验证的 architecture-level performance modeling framework，同时保持
scope conservative：只验证已经实现的 artifact chain，不把未来能力写成当前结果。

核心验证对象：

```text
workload -> trace -> metrics -> sweep -> comparison -> demo
```

## 1. Validation Goals

验证目标分三层：

| 层级 | 目标 |
| --- | --- |
| Artifact correctness | trace、summary、comparison、demo output 存在、非空、schema 正确。 |
| Metric sanity | latency、percentile、bank conflict、throughput 等指标满足内部不变量。 |
| Modeling boundary honesty | 文档、demo、comparison 不声称 cycle accuracy、protocol compliance 或 live co-simulation。 |

通过验证后可以说：

- 这是一个可复现的 architecture-level performance modeling framework。
- 它能把 synthetic workload、normalized trace 和 gem5 SE-derived trace 统一进 LT replay/analysis 链路。
- 它能把 AT arbitration policy 转成可观测 phase trace 和 request acceptance timing。

仍然不能说：

- 它是 cycle-accurate model。
- 它实现了 AXI / CHI / NoC / DRAM protocol。
- 它是 GPU shared memory real model。
- 它是 gem5-SystemC live co-simulation。
- 它验证了 full-system Linux。

## 2. Current Validation Matrix

| 模块 | 当前验证对象 | 当前检查方式 | 状态 |
| --- | --- | --- | --- |
| LT base lab | `latency_trace.csv`、`analyze_latency.py`、workload sweep | trace schema、latency decomposition、summary metrics、comparison output | 当前能力 |
| Phase16A | `demo_memory_access_pattern_lab.py` | `sequential` / `stride` / `hotspot` 三个 case、summary fields、demo PASS | 当前能力 |
| AT arbitration lab | `demo_at_lab.py`、`analyze_phase_trace.py`、`run_arbitration_sweep.py` | phase ordering、transaction completeness、policy sweep output | 当前能力 |
| Project B replay | `run_trace_replay_lab.py`、`demo_trace_replay_lab.py` | normalized trace schema、deterministic sorting、summary invariants、demo PASS | 当前能力 |
| Project C extraction | `run_gem5_se_trace_extraction.py`、`convert_gem5_se_trace.py` | gem5 marker extraction、normalized trace generation、Project B replay | 当前能力，依赖外部 gem5 和 target binary |
| gem5 stats correlation | gem5 `stats.txt` vs replay metrics | marker count、memory access count、region stats、future correlation script | 未来工作 |
| RTL / silicon / profiler correlation | 外部真实数据 vs model metrics | calibration dataset、error budget、correlation report | 未来工作 |

## 3. Internal Sanity Checks

所有 analyzer、sweep runner、demo wrapper 至少应满足以下内部 sanity checks。

Trace 层：

- trace 文件存在且非空。
- required fields 全部存在。
- numeric fields 可解析。
- timestamp / start / end time 不为负。
- `end_time_ns >= start_time_ns`。
- transaction id 在单个 workload 内稳定且可追溯。

Metric 层：

- transaction count 大于 0。
- latency metrics 非负。
- percentile ordering 满足 `p50_latency_ns <= p95_latency_ns <= p99_latency_ns <= max_latency_ns`。
- `bank_conflict_ratio_pct` 在 `0.000` 到 `100.000` 之间。
- `throughput_txn_per_us` 为 `NA` 或非负。
- `summary.csv` 一行对应一个 workload / case / policy。
- `comparison.md` 从 `summary.csv` 生成，不手写漂移。

Demo 层：

- demo 只有在所有必要 artifacts 都存在且 sanity checks 通过时才打印 `PASS`。
- demo 输出必须列出关键 artifact 路径。
- demo 输出必须包含 scope reminder，例如不是 cycle-accurate / protocol compliance / live co-simulation。

## 4. Trace Schema Validation

### 4.1 LT Trace

LT analyzer 当前依赖的核心字段包括：

```text
initiator_id,target_id,command,address,data,start_time_ns,delay_ns,end_time_ns,
decoded_port,masked_address,data_length,response_status,request_time_ns,
bus_grant_time_ns,queue_delay_ns,target_service_delay_ns,total_delay_ns,
target_busy_until_ns
```

bank abstraction 字段可以作为 optional/defaulted fields：

```text
bank_id,bank_conflict,bank_conflict_delay_ns
```

Phase16A 还应检查 workload metadata，例如：

```text
workload_transaction_count,workload_address_stride,workload_memory_pattern,
workload_hotspot_ratio,transaction_index,is_hotspot_access
```

### 4.2 AT Phase Trace

AT phase trace 当前 schema：

```text
txn_id,component,direction,phase,command,address,data,time_ns,delay_ns,response_status
```

验证重点：

- 每个 transaction 至少能重建 expected phase path。
- `BEGIN_REQ`、`END_REQ`、`BEGIN_RESP`、`END_RESP` 的 ordering 不违反当前 AT lab 假设。
- `response_status` 最终到达 `TLM_OK_RESPONSE`。
- `request_accept_latency_ns` 可从 `BEGIN_REQ` 到 `END_REQ` 计算。
- policy sweep 中 `fifo`、`priority_101`、`priority_102` 均产生独立 summary。

### 4.3 Project B Normalized Trace

Project B replay 的 required fields：

```text
workload_name,txn_id,timestamp_ns,initiator_id,command,address,size_bytes
```

当前 MVP 约束：

- 每个输入 trace 文件只有一个 `workload_name`。
- 当前 replayer 支持 `initiator_id=101`。
- 当前 replayer 支持 `command=READ`。
- 当前 replayer 支持 `size_bytes=4`。
- `timestamp_ns` 必须是非负数。
- `address` 必须可解析为 decimal 或 hex，并映射到当前 LT MVP target window。
- 同一个 trace 内 `txn_id` 不重复。
- replay 排序使用 `timestamp_ns`，再使用 `txn_id`。

### 4.4 Project C Normalized Trace

Project C converter 输出应兼容 Project B required fields，并可额外保留：

```text
pc,symbol,source
```

验证重点：

- real gem5 输出时 `source=gem5_se_simout`。
- sample format fallback 输出时 `source=sample_expected_format_not_real_gem5`，不能当成真实 gem5 validation。
- `pc` 和 `symbol` 是 optional metadata，不能成为 Project B replay 的 required fields。

## 5. Regression Demo Checks

回归验证应该覆盖四类命令：

1. Phase16A demo。
2. Project B normalized trace replay demo。
3. Project C gem5 SE trace extraction。
4. Project C replay through Project B backend。

详细命令集中维护在 [REGRESSION_TESTPLAN.md](REGRESSION_TESTPLAN.md)。

每次回归至少检查：

- command exit code 为 0。
- demo 输出包含 `PASS` 或明确的 success marker。
- expected artifacts 存在。
- `summary.csv` schema 与当前脚本定义一致。
- `comparison.md` 明确保留 model boundary。

## 6. gem5 Marker Extraction Checks

Project C 的 gem5 SE validation 应先验证 target binary 和 gem5 prerequisites，再验证 marker flow。

Binary checks：

```bash
file build/project_c/gem5_se/sequential_scan
readelf -h build/project_c/gem5_se/sequential_scan
readelf -l build/project_c/gem5_se/sequential_scan

file build/project_c/gem5_se/stride_scan
readelf -h build/project_c/gem5_se/stride_scan
readelf -l build/project_c/gem5_se/stride_scan
```

Marker checks：

- gem5 run 产生 `simout` 或 `run_stdout.txt`。
- marker source 中存在 `PROJECT_C_MEM` 行。
- 每个 marker 至少包含 `workload`、`seq`、`command`、`address`、`size`。
- converter 能生成 normalized CSV。
- normalized CSV 行数与 marker count 一致，或差异由 `--command-filter` 明确解释。
- normalized `address` 不为负。
- normalized `timestamp_ns` 单调且符合 `--timestamp-step-ns`。
- 输出 trace 可通过 Project B `--validate-only`。

## 7. Future gem5 Stats Correlation

未来 gem5 correlation 不应直接声称已经完成。建议分阶段加入：

| 阶段 | 检查内容 | 产物 |
| --- | --- | --- |
| Stats presence | gem5 output dir 包含 `stats.txt`，且 run exit code 为 0。 | prerequisite report |
| Count correlation | `PROJECT_C_MEM` marker count 与 workload loop count / selected stats counter 一致。 | marker count table |
| Timing boundary | 明确区分 gem5 tick、normalized `timestamp_ns`、SystemC replay latency。 | timing semantics note |
| Metric correlation | 比较 gem5 memory-related stats 与 replay metrics 的趋势，不比较绝对 cycle。 | correlation report |
| Calibration | 用真实或更高保真数据校准 latency 参数。 | calibrated model version |

在这些步骤完成前，Project C 只能称为 gem5 SE offline trace producer flow。

## 8. Future RTL / Silicon / Profiler Correlation

工业级 validation 需要外部 ground truth。未来可以加入：

- RTL simulation trace 或 performance counters。
- FPGA / silicon performance counters。
- CPU / GPU profiler trace。
- vendor simulator 或 cycle model output。
- workload region markers，用来对齐同一段 workload。

推荐 correlation 输出：

- workload / region id。
- model version。
- input trace hash。
- replay metric。
- reference metric。
- absolute error。
- percentage error。
- known mismatch reason。

在 correlation 数据完成前，不应声称 silicon correlation、RTL equivalence 或 profiler validation。

## 9. Documentation Validation

面试文档、README、portfolio、comparison 必须同步遵守以下规则：

- 主语言使用中文，技术名词和命令保留英文。
- 优先表达 `workload -> trace -> metrics -> sweep -> comparison -> demo`。
- 明确区分 LT workflow、AT timing refinement、Project B replay、Project C offline trace producer。
- 不把 `references/doulos_at_example` 描述成本项目 mainline 实现。
- 不把 generated outputs 当成 source artifacts。
- 不把 future work 写成已完成 capability。

## 10. Mac-to-Ubuntu Packaging Reminder

从 Mac 打包到 Ubuntu 验证环境时，使用：

```bash
tar --disable-copyfile --no-xattrs -czf systemc-tlm-performance-labs.tar.gz \
  systemc-tlm-performance-labs
```

这样可以避免 macOS resource fork 和 xattrs 生成 `._*` 文件污染源码。
