# examples/lt 性能建模实验室

[Project overview](../../README.md) | [AT arbitration lab](../at/README.md)

`examples/lt` 是一个 LT performance modeling lab。它保留 Renode bridge 和 LT
blocking transport path 作为 integration foundation；当前项目重点是 latency
decomposition、workload sweep、comparison report 和 one-command demo，并包含一个
最小 bank conflict / locality 模型。

这个 lab 的目标是把 transaction-level trace 转成 architecture-level latency analysis。
它可以把一次 transaction 的延迟拆成：

- target service cost
- shared-resource queue delay
- minimal bank conflict delay

它还可以通过可重复的 sweep cases 比较 single initiator、dual initiator、target hotspot、
stride/locality workload，以及 Phase 16A memory access pattern sweep。

这仍然是一个 minimal LT performance model，不是完整 NoC、cache 或 DRAM 模型。

## 这个 Lab 能说明什么

- 两个 initiator 共享同一条 target path 时，会产生 queue delay。
- target 201 hotspot 比 target 202 hotspot 慢，因为 target 201 的 service delay 更高。
- 在 Phase 6 minimal bank model 下，`stride=16` 相比 `stride=4` 会提高 bank conflict
  ratio。
- Phase 16A 会把 `sequential`、`stride`、`hotspot` 三种 memory access pattern 放在同一
  条 trace/summary/comparison 链路里比较。
- `comparison.md` 会把 sweep summary metrics 转成 baseline-vs-case 的架构对比说明。

## 一键演示

最短复现命令：

```bash
python3 examples/lt/tools/demo_performance_lab.py
```

这个脚本会清理旧的 trace/config/sweep 输出，依次运行 `renode-test`、`analyze_latency.py`
和 `run_workload_sweep.py`，最后打印关键输出路径和 4 条架构结论。它只是把已有 analyzer
和 sweep runner 串起来，不改变 SystemC 模型、transaction routing、trace CSV 格式或
统计逻辑。

生成的主要文件：

- `examples/lt/results/analysis.txt`
- `examples/lt/results/sweep/summary.csv`
- `examples/lt/results/sweep/comparison.md`

Phase 16A memory access pattern MVP 使用独立的一键演示。Ubuntu 验证时使用的命令为：

```bash
python3 examples/lt/tools/demo_memory_access_pattern_lab.py \
  --robot examples/lt/lt.robot \
  --output-dir examples/lt/results/memory_access_pattern_lab \
  --renode-test-cmd renode-test
```

这个 demo 是 architecture-level SystemC/TLM memory access pattern lab，只运行三种
pattern：

- `sequential`
- `stride`
- `hotspot`

生成的主要文件：

- `examples/lt/results/memory_access_pattern_lab/trace.csv`
- `examples/lt/results/memory_access_pattern_lab/summary.csv`
- `examples/lt/results/memory_access_pattern_lab/comparison.md`

当前验证结果显示，`stride` 会显著放大 minimal bank conflict；`sequential` 和
`hotspot` 在这组 MVP 输入下保持 zero-conflict baseline。

## 快速开始

Ubuntu 示例，从仓库根目录执行；下面的 `<repo-root>` 表示当前仓库根目录：

```bash
cd <repo-root>

# 单次 Robot 运行前可选清理。
rm -f examples/lt/results/latency_trace.csv
rm -f examples/lt/results/workload_config.env

renode-test examples/lt/lt.robot

python3 examples/lt/tools/analyze_latency.py \
  --trace examples/lt/results/latency_trace.csv

python3 examples/lt/tools/run_workload_sweep.py \
  --robot examples/lt/lt.robot \
  --output-dir examples/lt/results/sweep \
  --keep-going

python3 examples/lt/tools/run_memory_access_pattern_sweep.py \
  --robot examples/lt/lt.robot \
  --output-dir examples/lt/results/memory_access_pattern_lab \
  --keep-going

column -s, -t examples/lt/results/sweep/summary.csv | sed -n '1,12p'
sed -n '1,220p' examples/lt/results/sweep/comparison.md
column -s, -t examples/lt/results/memory_access_pattern_lab/summary.csv | sed -n '1,8p'
sed -n '1,220p' examples/lt/results/memory_access_pattern_lab/comparison.md
```

如果 `renode-test` 不在 `PATH` 中，可以显式指定：

```bash
python3 examples/lt/tools/run_workload_sweep.py \
  --renode-test-cmd /home/leo/tools/renode_1.16.1-dotnet_portable/renode-test \
  --robot examples/lt/lt.robot \
  --output-dir examples/lt/results/sweep \
  --keep-going

python3 examples/lt/tools/run_memory_access_pattern_sweep.py \
  --renode-test-cmd /home/leo/tools/renode_1.16.1-dotnet_portable/renode-test \
  --robot examples/lt/lt.robot \
  --output-dir examples/lt/results/memory_access_pattern_lab \
  --keep-going
```

如果 `lt` binary 还没有构建，可以先执行：

```bash
cd <repo-root>/examples/lt

source /home/leo/tools/renode_1.16.1-dotnet_portable/renode-env

cmake -S . -B build -DCMAKE_PREFIX_PATH=/home/leo/local/systemc
make -C build -j"$(nproc)"

mkdir -p bin
ln -sf ../build/lt bin/lt
```

## 输出文件

- `examples/lt/results/latency_trace.csv`: 从
  `SimpleBusLT::initiatorBTransport()` 记录的原始 transaction trace。
- `examples/lt/results/sweep/summary.csv`: sweep 之后的一行一个 case 的总表。
- `examples/lt/results/sweep/comparison.md`: baseline-vs-case 的 sweep 对比报告。
- `examples/lt/results/memory_access_pattern_lab/trace.csv`: Phase 16A 三种 memory
  access pattern 的合并 trace，包含 `case_id` 字段。
- `examples/lt/results/memory_access_pattern_lab/summary.csv`: Phase 16A MVP summary，
  至少包含 `pattern`、`stride`、`num_transactions`、tail latency、bank conflict ratio
  和 throughput。
- `examples/lt/results/memory_access_pattern_lab/comparison.md`: 适合放进作品集的
  sequential/stride/hotspot 对比说明。

trace 路径由正在运行的 `lt` 可执行文件通过 `/proc/self/exe` 解析。如果可执行文件位于
`examples/lt/build/lt` 或 `examples/lt/bin/lt`，trace 会写到 `examples/lt/results`。

## 验证快照

下面是当前 Ubuntu 环境下的验证快照，不是通用硬件 timing claim。

| case | 关键观测 |
| --- | --- |
| baseline, `stride=4` | `avg_delay_ns = 164.688 ns`, `bank_conflict_ratio_pct = 46.875%` |
| `stride=16` | `avg_delay_ns = 185.312 ns`, `bank_conflict_ratio_pct = 98.438%` |
| single initiator | `avg_queue_delay_ns = 0.000 ns` |
| target 201 hotspot | `avg_delay_ns = 218.906 ns` |
| target 202 hotspot | `avg_delay_ns = 119.375 ns` |

这里重要的不是绝对 timing 数字，而是同一个 LT 模型已经能区分 target service cost、
shared-target contention cost 和 locality-driven bank conflict cost。

## 架构

入口和顶层连线：

- `sc_main`: `examples/lt/systemc/src/main.cpp`
  - 读取 Renode bridge address 和 port 参数。
  - 构造 `top top("top", renode_address, renode_port)`。
  - 调用 `sc_core::sc_start()`。
- `top` module:
  - 声明：`examples/lt/systemc/include/top.h`
  - 连线和 workload config：`examples/lt/systemc/src/top.cpp`

核心组件：

- Bus: `SimpleBusLT<3, 2> m_bus`
  - 文件：`examples/lt/systemc/third-party/systemc-lt-example/SimpleBusLT.h`
  - 3 个 initiator-facing target sockets：initiator 101、initiator 102、Renode bridge。
  - 2 个 target-facing initiator sockets：target 201、target 202。
- Initiator 101/102:
  - 创建位置：`examples/lt/systemc/src/top.cpp`。
  - 类型：`initiator_top`，内部包含 `traffic_generator` 和 `lt_initiator`。
  - workload knobs 通过现有 SystemC object graph 和 env/config-file fallback 传入。
- Target 201:
  - 实例：`m_at_and_lt_target_1`
  - 类型：`at_target_1_phase`
  - nominal service delay：read `120 ns`，write `80 ns`
- Target 202:
  - 实例：`m_lt_target_2`
  - 类型：`lt_target`
  - nominal service delay：read `60 ns`，write `40 ns`
- Renode bridge:
  - 成员：`renode_bridge m_renode_bridge`
  - 接入：`m_renode_bridge.initiator_socket(m_bus.target_socket[2])`
  - trace ID：`initiator_id = 9002`

Blocking transaction 路径：

```text
traffic_generator
  -> lt_initiator::initiator_thread()
  -> initiator_socket->b_transport(...)
  -> SimpleBusLT::initiatorBTransport(...)
  -> target b_transport/custom_b_transport
  -> memory::operation(...)
```

Renode `sysbus` read/write 也会通过 Renode bridge 作为第三个 initiator 进入同一个
`SimpleBusLT`。

## Trace Schema

trace 文件：

```text
examples/lt/results/latency_trace.csv
```

字段：

- `initiator_id`: `101`、`102` 或 Renode bridge 的 `9002`。
- `target_id`: `201`、`202`，或者 unmapped decoded port 的 `-1`。
- `command`: `READ`、`WRITE` 或 `OTHER`。
- `address`: address masking 前的原始 bus address。
- `data`: payload 前 4 bytes 按 `uint32_t` 解释；不可用时为 `0`。
- `start_time_ns`: 有效 bus arrival time。
- `delay_ns`: initiator 可见的 observed transaction delay。
- `end_time_ns`: `start_time_ns + delay_ns`。
- `decoded_port`: `SimpleBusLT` 解码出的 target port。
- `masked_address`: `trans.set_address(...)` 后的地址。
- `data_length`: `trans.get_data_length()`。
- `response_status`: target `b_transport` 返回后的 response string。
- `request_time_ns`: 进入 bus 时的原始 `sc_time_stamp()`。
- `bus_grant_time_ns`: 根据 target `busy_until` 计算出的 service grant time。
- `queue_delay_ns`: shared target serialization 造成的等待时间。
- `target_service_delay_ns`: target 自身增加的 service delay。
- `total_delay_ns`: `queue_delay_ns + target_service_delay_ns +
  bank_conflict_delay_ns`。
- `target_busy_until_ns`: 本次 transaction 后 target 的下一次可服务时间。
- `workload_transaction_count`: 每个启用 initiator 的 transaction count。
- `workload_address_stride`: 配置的 address stride。
- `workload_target_pattern`: `current_default`、`target201_only` 或 `target202_only`。
- `workload_enable_initiator_101`: initiator 101 的 workload enable flag。
- `workload_enable_initiator_102`: initiator 102 的 workload enable flag。
- `workload_memory_pattern`: `legacy`、`sequential`、`stride` 或 `hotspot`。
- `workload_hotspot_ratio`: hotspot pattern 中映射到热点地址的事务比例。
- `transaction_index`: 每个 SystemC initiator 的 trace-local transaction index。
- `is_hotspot_access`: 当前 transaction 是否被 Phase 16A 标记为 hotspot access。
- `bank_id`: Phase 6 minimal bank id。
- `bank_conflict`: 是否命中同 target 连续同 bank 访问。
- `bank_conflict_delay_ns`: minimal bank conflict model 引入的额外 delay。

## Phase 总览

| phase | 功能 |
| --- | --- |
| Phase 1 | 在 `SimpleBusLT::initiatorBTransport()` 中记录 latency CSV |
| Phase 2 | `analyze_latency.py` 架构视角报告 |
| Phase 3/4 | queue delay、target service delay 分解，以及 workload knobs |
| Phase 5 | `run_workload_sweep.py` workload sweep runner |
| Phase 5.5 | 为 GitHub 读者整理 expected sweep results |
| Phase 6 | minimal bank conflict / locality model |
| Phase 7 | `comparison.md` baseline-vs-case sweep report |
| Phase 8 | `demo_performance_lab.py` one-command demo |
| Phase 9 | 从 LT workflow 走向 AT timing refinement 的 roadmap |
| Phase 16A | sequential / stride / hotspot memory access pattern MVP |

## Workload Sweep

sweep runner：

```text
examples/lt/tools/run_workload_sweep.py
```

默认 cases：

- `baseline_dual_initiator_current_default`
- `single_initiator_101_current_default`
- `dual_initiator_target201_hotspot`
- `dual_initiator_target202_hotspot`
- `dual_initiator_stride_16_current_default`

每个 case 会：

- 删除旧的 `examples/lt/results/latency_trace.csv`
- 写入短生命周期的 `examples/lt/results/workload_config.env`
- 运行 `renode-test examples/lt/lt.robot`
- 运行 `analyze_latency.py --fail-on-sanity`
- 校验 initiator enable flags、target pattern 和 address stride
- 把 per-case trace 和 analysis artifacts 写到
  `examples/lt/results/sweep/<case_name>/`
- 向 `examples/lt/results/sweep/summary.csv` 写入一行 summary

`summary.csv` 只有在 `renode-test`、analyzer sanity checks 和 workload semantic checks
都通过时，才会把 case 标记为 `status=PASS`。失败 case 会保留 `error` 字段，并且仍然
可以出现在 `comparison.md` 中。

sweep summary 默认只分析 SystemC traffic generator initiators `101` 和 `102`，不把
Renode bridge initiator `9002` 混入默认性能指标。

## Phase 16A Memory Access Pattern Sweep

Phase 16A MVP runner：

```text
examples/lt/tools/run_memory_access_pattern_sweep.py
```

默认只运行三种 memory access pattern：

| pattern | knobs | 建模含义 |
| --- | --- | --- |
| `sequential` | `LT_MEMORY_PATTERN=sequential`, `LT_ADDRESS_STRIDE=4` | 连续 word access，作为 locality-friendly baseline |
| `stride` | `LT_MEMORY_PATTERN=stride`, `LT_ADDRESS_STRIDE=16` | 固定较大 stride，更容易反复映射到 minimal bank model 的同一 bank |
| `hotspot` | `LT_MEMORY_PATTERN=hotspot`, `LT_ADDRESS_STRIDE=4`, `LT_HOTSPOT_RATIO=0.8` | 约 80% transaction 集中到同一个 base address |

MVP runner 复用已有 LT trace 和 analyzer：

- 每个 case 写入短生命周期的 `examples/lt/results/workload_config.env`
- 运行 `renode-test examples/lt/lt.robot`
- 复制 per-case `trace.csv`
- 运行 `analyze_latency.py --initiator 101 --dedup-identical --fail-on-sanity`
- 校验 trace 中的 `workload_memory_pattern`、`workload_address_stride`、
  `workload_hotspot_ratio` 和 hotspot 标记
- 输出合并后的 `trace.csv`
- 输出一行一个 pattern 的 `summary.csv`
- 输出 sequential/stride/hotspot 的 latency 和 bank conflict 对比报告

Phase 16A `summary.csv` 至少包含：

- `pattern`
- `stride`
- `num_transactions`
- `avg_latency_ns`
- `p50_latency_ns`
- `p95_latency_ns`
- `p99_latency_ns`
- `max_latency_ns`
- `bank_conflict_ratio_pct`
- `throughput_txn_per_us`

### Phase 16A Memory Access Pattern MVP

Phase 16A 是 architecture-level SystemC/TLM memory access pattern lab。它不改变
当前 LT blocking transport path，而是把同一个 workload/trace/metrics/sweep/comparison
链路用于比较三种 access pattern：

| pattern | 建模目的 |
| --- | --- |
| `sequential` | locality-friendly baseline，按较小 stride 连续访问 |
| `stride` | 固定较大 stride，刻意放大 minimal bank model 下的 same-bank repeat |
| `hotspot` | 把热点访问集中到固定 base address，用于和 sequential/stride 对照 |

Ubuntu 验证命令返回：

```text
[demo] Phase 16A Memory Access Pattern MVP PASS
```

关键结果：

| pattern | avg_latency_ns | p99_latency_ns | bank_conflict_ratio_pct | throughput_txn_per_us |
| --- | ---: | ---: | ---: | ---: |
| `sequential` | 100.000 | 120.000 | 0.000% | 20.000 |
| `stride` | 119.688 | 140.000 | 98.438% | 16.710 |
| `hotspot` | 100.000 | 120.000 | 0.000% | 20.000 |

`stride` 的 bank conflict ratio 高达 `98.438%`，原因是 Phase 6 minimal bank model
使用：

```text
bank_id = (masked_address / 4) % 4
```

`sequential` 使用 `stride=4` 时，word address 会在 4 个 minimal banks 之间轮转。
`stride` case 使用 `stride=16`，等价于每次跨过 4 个 word；代入上面的 modulo-4 bank
mapping 后会反复回到同一个 bank。`SimpleBusLT` 又按 target 记录上一次访问的 bank，
所以同一 target 上连续回到同一 bank 的 transaction 会触发 `bank_conflict_delay_ns`。
本轮 64 笔 transaction 中有 63 笔被计为 conflict，因此比例是 `63 / 64 * 100 =
98.438%`。

Phase 16A 的 `comparison.md` 面向作品集展示：它说明三种 access pattern 的 workload
差异、avg/p95/p99 latency delta、bank conflict ratio delta，以及为什么当前 MVP 中
`stride` 比 `sequential` 和 `hotspot` 更容易放大 bank conflict。

这些数字是当前 LT 架构级实验结果，不是通用硬件 timing claim。Phase 16A 不声称
cycle accuracy，也不声称 AXI、CHI、NoC 或 DRAM protocol compliance。

## Workload Knobs

如果没有设置 knobs，默认行为保持原始 `lt.robot` baseline workload。

- `LT_BURST_COUNT`: 每个 initiator 的 transaction count。
- `LT_ADDRESS_STRIDE`: 生成 workload 的 address stride。
- `LT_ENABLE_INITIATOR_101`: 启用或禁用 initiator 101。
- `LT_ENABLE_INITIATOR_102`: 启用或禁用 initiator 102。
- `LT_TARGET_PATTERN`:
  - `both`: 当前 default pattern，访问 target 201 和 target 202。
  - `target201`: 只访问 target 201。
  - `target202`: 只访问 target 202。
- `LT_MEMORY_PATTERN`:
  - `legacy`: 保持原始 workload phase 行为。
  - `sequential`: 按 `LT_ADDRESS_STRIDE` 生成连续 pattern。
  - `stride`: 使用较大 stride 生成 locality/bank-conflict 对比 pattern。
  - `hotspot`: 按 `LT_HOTSPOT_RATIO` 把部分 transaction 固定到热点地址。
- `LT_HOTSPOT_RATIO`: `hotspot` pattern 中热点 transaction 的比例，Phase 16A 默认
  使用 `0.8`。

runner 会把这些值作为 environment variables 传入，同时也会写
`workload_config.env`。这是因为 Renode 启动的 SystemC 子进程不一定继承
`renode-test` 的全部环境变量。

## 分析工具

主分析命令：

```bash
python3 examples/lt/tools/analyze_latency.py \
  --trace examples/lt/results/latency_trace.csv
```

只分析 SystemC traffic generator：

```bash
python3 examples/lt/tools/analyze_latency.py \
  --trace examples/lt/results/latency_trace.csv \
  --initiator 101 \
  --initiator 102 \
  --dedup-identical
```

常用参数：

- `--initiator <id>` / `--exclude-initiator <id>`
- `--target <id>`
- `--command <READ|WRITE|OTHER>`
- `--min-start-time-ns <value>`
- `--max-start-time-ns <value>`
- `--dedup-identical`
- `--summary-csv-output <path>`
- `--fail-on-sanity`

报告包含 overview、by-initiator summary、by-target summary、contention summary、
bank conflict summary、response status counts、address range、sanity checks，以及
first/last timeline rows。

## 建模语义

nominal target service delay：

| target_id | command | target_service_delay_ns |
| --- | --- | ---: |
| 201 | READ | 120 ns |
| 201 | WRITE | 80 ns |
| 202 | READ | 60 ns |
| 202 | WRITE | 40 ns |

当多个 initiator 共享同一条 target path 时，target service delay 不再等于 observed
transaction delay：

```text
delay_ns = observed transaction delay
total_delay_ns = queue_delay_ns + target_service_delay_ns + bank_conflict_delay_ns
```

Phase 6 的 bank model 刻意保持很小：

```text
bank_id = (masked_address / 4) % 4
```

如果 SystemC traffic 连续访问同一个 target 的同一个 bank，bus 会增加 `20 ns` 的
`bank_conflict_delay_ns` penalty。这个模型足以让 `stride=4` 和 `stride=16` 产生不同
sweep metrics，但它不是 cache、DRAM controller、bank scheduler 或完整 NoC 模型。

`analyze_latency.py` 对 pre-bank-conflict trace 保持兼容：如果旧 CSV 缺少 bank 字段，
分析器会把它当作 zero-conflict data。

## Roadmap: From LT Workflow to AT Timing Refinement

当前版本是 LT-based architecture performance analysis workflow，不是 AT 或
cycle-accurate timing model。它的价值在于先建立一条可重复的实验骨架：

- workload parameterization
- transaction trace observability
- architecture-level latency decomposition
- sweep comparison
- reproducible demo

当前 LT 版本不声称解决这些问题：

- cycle-accurate timing
- real AXI/CHI/NoC protocol timing
- true request/response phase overlap
- outstanding transaction reordering
- back-pressure / retry behavior

未来 AT 版本的目标是提升 timing protocol fidelity，而不是推翻当前 workflow。可能的演进
方向包括：

- 用 non-blocking `nb_transport_fw` / `nb_transport_bw` 替换当前 blocking
  `b_transport` path。
- 建模 TLM phases：`BEGIN_REQ`、`END_REQ`、`BEGIN_RESP`、`END_RESP`。
- 跟踪 outstanding transactions。
- 分离 request arbitration 和 response scheduling。
- 建模 initiator-side queues 和 target-side response latency。
- 暴露 AT-level trace fields，用于观察 phase timing、overlap、reordering 和 response
  path latency。

| Layer | Current LT lab | Future AT refinement |
| --- | --- | --- |
| protocol abstraction | blocking `b_transport` transaction | non-blocking `nb_transport_fw` / `nb_transport_bw` phases |
| timing fidelity | transaction-level annotated delay | phase-level timing with request/response handshakes |
| concurrency | 最小 target serialization 和 bank conflict | outstanding transactions、phase overlap、response ordering |
| queue modeling | target `busy_until`、queue delay、bank conflict penalty | request arbitration、initiator queues、target response scheduling |
| trace fields | transaction latency、queue/service/bank delay、workload config | `BEGIN_REQ` / `END_REQ` / `BEGIN_RESP` / `END_RESP` timing and outstanding IDs |
| best use case | 快速建立 workload → trace → metrics → sweep → interpretation 骨架 | 细化 timing protocol fidelity 和更接近真实互连行为的分析 |

因此，当前 LT lab 更适合作为 migration scaffold / experimental scaffold：先把实验输入、
trace、指标、sweep 和解释链路跑通，再逐步替换为 AT timing refinement。

## 限制

- 这是 minimal LT performance model。
- bank conflict model 不是完整 cache、DRAM 或 NoC 模型。
- 验证数字是当前 Ubuntu 环境的 snapshot，不是通用硬件 timing claim。
- 目前没有复杂 arbitration policy。
- 目前没有 multi-stage queueing model。
- 目前没有 bandwidth saturation model。
- 目前没有 outstanding transaction model。
- 目前没有 AT/non-blocking timing path analysis。

## 下一步

适合继续保持小而可重复的方向：

- 把 sweep case matrix 移到一个小配置文件中
- 扩展 Phase 16A 到更多 pattern，例如 read-only、write-only 或 multi-target variant
- 增加显式 arbitration policy knobs
- 增加简单 per-target bandwidth 参数
