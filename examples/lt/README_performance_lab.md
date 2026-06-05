# examples/lt 性能建模实验室

[项目总览](../../README.md) | [AT 仲裁实验室](../at/README.md)

`examples/lt` 是一个 LT 性能建模实验室。它保留 Renode bridge 和 LT blocking
transport path 作为集成基础；当前重点是延迟分解、workload sweep、comparison report、
one-command demo，以及一个最小 bank conflict / locality 模型。

这个 lab 的目标是把 transaction-level trace 转成架构级 latency analysis。
一次 transaction 的延迟会被拆成：

- target service cost。
- shared-resource queue delay。
- minimal bank conflict delay。

它还可以通过可重复的 sweep cases 比较 single initiator、dual initiator、target hotspot、
stride/locality workload、Phase 16A memory access pattern sweep、Project B
normalized trace replay、Project C gem5 SE-derived normalized trace replay，以及
Project D standalone C++ trace replay engine。

这仍然是一个 minimal LT performance model，不是完整 NoC、cache 或 DRAM 模型。

## 这个实验室能说明什么

- 两个 initiator 共享同一条 target path 时，会产生 queue delay。
- target 201 hotspot 比 target 202 hotspot 慢，因为 target 201 的 service delay 更高。
- 在 Phase 6 minimal bank model 下，`stride=16` 相比 `stride=4` 会提高
  `bank_conflict_ratio_pct`。
- Phase 16A 会把 `sequential`、`stride`、`hotspot` 三种 memory access pattern 放在同一
  条 trace / summary / comparison 链路里比较。
- Project B 会把流量来源扩展到 normalized external trace replay，但第一阶段不接真实
  gem5，也不做 live co-simulation。
- Project C 会把流量来源扩展到 gem5 SE-derived normalized traces；gem5 只作为
  offline trace producer，SystemC/TLM lab 作为 replay and analysis backend。
- Project D 会把 Project B / Project C 当前 Python replay 的核心 metrics 逻辑迁移到
  standalone C++ replay engine，并用 Python vs C++ equivalence check 验证输出一致。
- `comparison.md` 会把 summary metrics 转成 baseline-vs-case 的架构对比说明。

## 一键演示

最短复现命令：

```bash
python3 examples/lt/tools/demo_performance_lab.py
```

这个脚本会清理旧的 trace / config / sweep 输出，依次运行 `renode-test`、
`analyze_latency.py` 和 `run_workload_sweep.py`，最后打印关键输出路径和架构结论。它只是
把已有 analyzer 和 sweep runner 串起来，不改变 SystemC 模型、transaction routing、
trace CSV 格式或统计逻辑。

生成的主要文件：

- `examples/lt/results/analysis.txt`
- `examples/lt/results/sweep/summary.csv`
- `examples/lt/results/sweep/comparison.md`

Phase 16A memory access pattern MVP 使用独立的一键演示：

```bash
python3 examples/lt/tools/demo_memory_access_pattern_lab.py \
  --robot examples/lt/lt.robot \
  --output-dir examples/lt/results/memory_access_pattern_lab \
  --renode-test-cmd renode-test
```

Project B normalized trace replay MVP 使用独立的一键演示：

```bash
python3 examples/lt/tools/demo_trace_replay_lab.py
```

Project C gem5 SE trace extraction MVP 使用外部 gem5 SE 先生成 normalized trace，再复用
Project B replay：

```bash
python3 examples/lt/tools/run_gem5_se_trace_extraction.py \
  --gem5-binary ~/gem5/build/ARM/gem5.opt \
  --gem5-config ~/gem5/configs/deprecated/example/se.py \
  --workload build/examples/lt/workloads/gem5_se/sequential_scan \
  --workload-name gem5_sequential_scan \
  --output-dir examples/lt/results/gem5_se_trace_extraction/sequential \
  --normalized-output examples/lt/traces/gem5_sequential_trace.csv

python3 examples/lt/tools/run_gem5_se_trace_extraction.py \
  --gem5-binary ~/gem5/build/ARM/gem5.opt \
  --gem5-config ~/gem5/configs/deprecated/example/se.py \
  --workload build/examples/lt/workloads/gem5_se/stride_scan \
  --workload-name gem5_stride_scan \
  --output-dir examples/lt/results/gem5_se_trace_extraction/stride \
  --normalized-output examples/lt/traces/gem5_stride_trace.csv

python3 examples/lt/tools/run_trace_replay_lab.py \
  --trace examples/lt/traces/gem5_sequential_trace.csv \
  --trace examples/lt/traces/gem5_stride_trace.csv \
  --output-dir examples/lt/results/gem5_trace_replay_lab
```

Project D standalone C++ trace replay MVP 使用独立 C++ binary 复刻 Project B /
Project C 当前 Python replay 的核心 metrics 逻辑。Python 仍负责 demo orchestration、
Python vs C++ equivalence check 和 `comparison.md` 生成：

```bash
cmake -S examples/lt/replay_cpp -B build/examples/lt/replay_cpp
cmake --build build/examples/lt/replay_cpp -j"$(nproc)"

python3 examples/lt/tools/demo_cpp_trace_replay_lab.py
```

Project D 只做 standalone normalized trace replay；第一版不接 SystemC kernel，不接
gem5 live co-simulation，也不实现 cache、DRAM、AXI、CHI 或 NoC protocol model。

## 快速开始

Ubuntu 示例，从仓库根目录执行；下面的 `<repo-root>` 表示当前仓库根目录。

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

python3 examples/lt/tools/run_trace_replay_lab.py \
  --validate-only \
  --trace examples/lt/traces/sample_sequential_trace.csv \
  --trace examples/lt/traces/sample_stride_trace.csv

python3 examples/lt/tools/demo_trace_replay_lab.py

cmake -S examples/lt/replay_cpp -B build/examples/lt/replay_cpp
cmake --build build/examples/lt/replay_cpp

./build/examples/lt/replay_cpp/replay_cpp \
  --trace examples/lt/traces/sample_sequential_trace.csv \
  --trace examples/lt/traces/sample_stride_trace.csv \
  --trace examples/lt/traces/gem5_sequential_trace.csv \
  --trace examples/lt/traces/gem5_stride_trace.csv \
  --output-dir examples/lt/results/cpp_trace_replay_lab

python3 examples/lt/tools/demo_cpp_trace_replay_lab.py --no-build

aarch64-linux-gnu-gcc -O0 -static \
  examples/lt/workloads/gem5_se/sequential_scan.c \
  -o build/examples/lt/workloads/gem5_se/sequential_scan

aarch64-linux-gnu-gcc -O0 -static \
  examples/lt/workloads/gem5_se/stride_scan.c \
  -o build/examples/lt/workloads/gem5_se/stride_scan

column -s, -t examples/lt/results/sweep/summary.csv | sed -n '1,12p'
sed -n '1,220p' examples/lt/results/sweep/comparison.md
column -s, -t examples/lt/results/memory_access_pattern_lab/summary.csv | sed -n '1,8p'
sed -n '1,220p' examples/lt/results/memory_access_pattern_lab/comparison.md
column -s, -t examples/lt/results/trace_replay_lab/summary.csv
sed -n '1,220p' examples/lt/results/trace_replay_lab/comparison.md
column -s, -t examples/lt/results/gem5_trace_replay_lab/summary.csv
sed -n '1,220p' examples/lt/results/gem5_trace_replay_lab/comparison.md
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

- `examples/lt/results/latency_trace.csv`：从
  `SimpleBusLT::initiatorBTransport()` 记录的原始 transaction trace。
- `examples/lt/results/sweep/summary.csv`：workload sweep 之后的一行一个 case 的总表。
- `examples/lt/results/sweep/comparison.md`：baseline-vs-case 的 sweep 对比报告。
- `examples/lt/results/memory_access_pattern_lab/trace.csv`：Phase 16A 三种 memory
  access pattern 的合并 trace，包含 `case_id` 字段。
- `examples/lt/results/memory_access_pattern_lab/summary.csv`：Phase 16A MVP summary，
  至少包含 `pattern`、`stride`、`num_transactions`、tail latency、
  `bank_conflict_ratio_pct` 和 `throughput_txn_per_us`。
- `examples/lt/results/memory_access_pattern_lab/comparison.md`：`sequential` /
  `stride` / `hotspot` 的对比说明。
- `examples/lt/results/trace_replay_lab/trace.csv`：Project B normalized trace replay
  的合并 trace，保留 `workload_name` 和 `txn_id`，方便回溯输入 trace。
- `examples/lt/results/trace_replay_lab/summary.csv`：Project B 一行一个 workload 的
  summary。
- `examples/lt/results/trace_replay_lab/comparison.md`：Project B `sample_sequential`
  和 `sample_stride` 的对比说明。
- `examples/lt/traces/gem5_sequential_trace.csv`：Project C 从 AArch64
  `sequential_scan` 经 gem5 SE marker flow 转成的 normalized trace。
- `examples/lt/traces/gem5_stride_trace.csv`：Project C 从 AArch64 `stride_scan` 经
  gem5 SE marker flow 转成的 normalized trace。
- `examples/lt/results/gem5_trace_replay_lab/trace.csv`：Project C gem5 SE-derived
  normalized trace replay 的合并 trace。
- `examples/lt/results/gem5_trace_replay_lab/summary.csv`：Project C 一行一个
  gem5-derived workload 的 summary。
- `examples/lt/results/gem5_trace_replay_lab/comparison.md`：Project C
  `gem5_sequential_scan` 和 `gem5_stride_scan` 的对比说明。
- `examples/lt/results/cpp_trace_replay_lab/trace.csv`：Project D standalone C++
  replay engine 生成的合并 trace。
- `examples/lt/results/cpp_trace_replay_lab/summary.csv`：Project D C++ engine
  生成的一行一个 workload 的 summary，字段顺序与 Project B Python replay 对齐。
- `examples/lt/results/cpp_trace_replay_lab/comparison.md`：Project D demo 从 C++
  `summary.csv` 生成的对比说明。

LT trace 路径由正在运行的 `lt` 可执行文件通过 `/proc/self/exe` 解析。如果可执行文件位于
`examples/lt/build/lt` 或 `examples/lt/bin/lt`，trace 会写到 `examples/lt/results`。

## 验证快照

下面是当前 Ubuntu 环境下的验证快照，不是通用硬件 timing claim。

| 场景 | 关键观测 |
| --- | --- |
| baseline, `stride=4` | `avg_delay_ns = 164.688 ns`, `bank_conflict_ratio_pct = 46.875%` |
| `stride=16` | `avg_delay_ns = 185.312 ns`, `bank_conflict_ratio_pct = 98.438%` |
| single initiator | `avg_queue_delay_ns = 0.000 ns` |
| target 201 hotspot | `avg_delay_ns = 218.906 ns` |
| target 202 hotspot | `avg_delay_ns = 119.375 ns` |
| Phase 16A `stride` | `avg_latency_ns = 119.688 ns`, `p99_latency_ns = 140.000 ns`, `bank_conflict_ratio_pct = 98.438%` |
| Project B `sample_stride` | `avg_latency_ns = 119.688 ns`, `p99_latency_ns = 120.000 ns`, `bank_conflict_ratio_pct = 98.438%` |
| Project C `gem5_stride_scan` | `avg_latency_ns = 119.688 ns`, `p99_latency_ns = 120.000 ns`, `bank_conflict_ratio_pct = 98.438%` |
| Project D C++ replay | `[replay-cpp] Project D standalone C++ trace replay PASS`, `[compare] Python vs C++ replay summary equivalence PASS`, `[demo-cpp] Project D Standalone C++ Trace Replay MVP PASS` |

这里重要的不是绝对 timing 数字，而是同一个 LT 模型已经能区分 target service cost、
shared-target contention cost 和 locality-driven bank conflict cost。

## 架构

入口和顶层连线：

- `sc_main`：`examples/lt/systemc/src/main.cpp`
  - 读取 Renode bridge address 和 port 参数。
  - 构造 `top top("top", renode_address, renode_port)`。
  - 调用 `sc_core::sc_start()`。
- `top` module：
  - 声明：`examples/lt/systemc/include/top.h`
  - 连线和 workload config：`examples/lt/systemc/src/top.cpp`

核心组件：

- Bus：`SimpleBusLT<3, 2> m_bus`
  - 文件：`examples/lt/systemc/third-party/systemc-lt-example/SimpleBusLT.h`
  - 3 个 initiator-facing target sockets：initiator 101、initiator 102、Renode bridge。
  - 2 个 target-facing initiator sockets：target 201、target 202。
- Initiator 101/102：
  - 创建位置：`examples/lt/systemc/src/top.cpp`。
  - 类型：`initiator_top`，内部包含 `traffic_generator` 和 `lt_initiator`。
  - workload knobs 通过现有 SystemC object graph 和 env/config-file fallback 传入。
- Target 201：
  - 实例：`m_at_and_lt_target_1`
  - 类型：`at_target_1_phase`
  - nominal service delay：read `120 ns`，write `80 ns`
- Target 202：
  - 实例：`m_lt_target_2`
  - 类型：`lt_target`
  - nominal service delay：read `60 ns`，write `40 ns`
- Renode bridge：
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

## Trace 字段

LT 原始 trace 文件：

```text
examples/lt/results/latency_trace.csv
```

字段含义：

- `initiator_id`：`101`、`102` 或 Renode bridge 的 `9002`。
- `target_id`：`201`、`202`，或者 unmapped decoded port 的 `-1`。
- `command`：`READ`、`WRITE` 或 `OTHER`。
- `address`：address masking 前的原始 bus address。
- `data`：payload 前 4 bytes 按 `uint32_t` 解释；不可用时为 `0`。
- `start_time_ns`：有效 bus arrival time。
- `delay_ns`：initiator 可见的 observed transaction delay。
- `end_time_ns`：`start_time_ns + delay_ns`。
- `decoded_port`：`SimpleBusLT` 解码出的 target port。
- `masked_address`：`trans.set_address(...)` 后的地址。
- `data_length`：`trans.get_data_length()`。
- `response_status`：target `b_transport` 返回后的 response string。
- `request_time_ns`：进入 bus 时的原始 `sc_time_stamp()`。
- `bus_grant_time_ns`：根据 target `busy_until` 计算出的 service grant time。
- `queue_delay_ns`：shared target serialization 造成的等待时间。
- `target_service_delay_ns`：target 自身增加的 service delay。
- `total_delay_ns`：`queue_delay_ns + target_service_delay_ns +
  bank_conflict_delay_ns`。
- `target_busy_until_ns`：本次 transaction 后 target 的下一次可服务时间。
- `workload_transaction_count`：每个启用 initiator 的 transaction count。
- `workload_address_stride`：配置的 address stride。
- `workload_target_pattern`：`current_default`、`target201_only` 或 `target202_only`。
- `workload_enable_initiator_101`：initiator 101 的 workload enable flag。
- `workload_enable_initiator_102`：initiator 102 的 workload enable flag。
- `workload_memory_pattern`：`legacy`、`sequential`、`stride` 或 `hotspot`。
- `workload_hotspot_ratio`：hotspot pattern 中映射到热点地址的 transaction 比例。
- `transaction_index`：每个 SystemC initiator 的 trace-local transaction index。
- `is_hotspot_access`：当前 transaction 是否被 Phase 16A 标记为 hotspot access。
- `bank_id`：Phase 6 minimal bank id。
- `bank_conflict`：是否命中同 target 连续同 bank 访问。
- `bank_conflict_delay_ns`：minimal bank conflict model 引入的额外 delay。

Project B normalized trace 输入字段：

```text
workload_name,txn_id,timestamp_ns,initiator_id,command,address,size_bytes
```

Project B MVP 中，`timestamp_ns` 只是 normalized issue-time / ordering hint，不是 gem5
timing，也不是 cycle timing。

Project C gem5 SE-derived normalized trace 在 Project B required fields 后保留可选
debug metadata：

```text
workload_name,txn_id,timestamp_ns,initiator_id,command,address,size_bytes,pc,symbol,source
```

Project C 中，`timestamp_ns` 同样只是 normalized issue-time / ordering hint，不是 gem5
timing，也不是 cycle timing。

## 阶段总览

| phase | 功能 |
| --- | --- |
| Phase 1 | 在 `SimpleBusLT::initiatorBTransport()` 中记录 latency CSV |
| Phase 2 | `analyze_latency.py` 架构视角报告 |
| Phase 3/4 | `queue_delay_ns`、`target_service_delay_ns` 分解，以及 workload knobs |
| Phase 5 | `run_workload_sweep.py` workload sweep runner |
| Phase 5.5 | 为 GitHub 读者整理 expected sweep results |
| Phase 6 | minimal bank conflict / locality model |
| Phase 7 | `comparison.md` baseline-vs-case sweep report |
| Phase 8 | `demo_performance_lab.py` one-command demo |
| Phase 9 | 从 LT workflow 走向 AT timing refinement 的 roadmap |
| Phase 16A | `sequential` / `stride` / `hotspot` memory access pattern MVP |
| Project B | normalized trace replay MVP |
| Project C | gem5 SE trace extraction MVP |

## 工作负载扫描

workload sweep runner：

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

- 删除旧的 `examples/lt/results/latency_trace.csv`。
- 写入短生命周期的 `examples/lt/results/workload_config.env`。
- 运行 `renode-test examples/lt/lt.robot`。
- 运行 `analyze_latency.py --fail-on-sanity`。
- 校验 initiator enable flags、target pattern 和 address stride。
- 把 per-case trace 和 analysis artifacts 写到
  `examples/lt/results/sweep/<case_name>/`。
- 向 `examples/lt/results/sweep/summary.csv` 写入一行 summary。

`summary.csv` 只有在 `renode-test`、analyzer sanity checks 和 workload semantic checks
都通过时，才会把 case 标记为 `status=PASS`。失败 case 会保留 `error` 字段，并且仍然
可以出现在 `comparison.md` 中。

sweep summary 默认只分析 SystemC traffic generator initiators `101` 和 `102`，不把
Renode bridge initiator `9002` 混入默认性能指标。

## Phase 16A：内建内存访问模式扫描

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

- 每个 case 写入短生命周期的 `examples/lt/results/workload_config.env`。
- 运行 `renode-test examples/lt/lt.robot`。
- 复制 per-case `trace.csv`。
- 运行 `analyze_latency.py --initiator 101 --dedup-identical --fail-on-sanity`。
- 校验 trace 中的 `workload_memory_pattern`、`workload_address_stride`、
  `workload_hotspot_ratio` 和 hotspot 标记。
- 输出合并后的 `trace.csv`。
- 输出一行一个 pattern 的 `summary.csv`。
- 输出 `sequential` / `stride` / `hotspot` 的 latency 和 bank conflict 对比报告。

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

### Phase 16A：内建内存访问模式 MVP

目标：

- 在现有 LT performance workflow 上比较内建 synthetic memory access patterns。
- 保持 `workload -> trace -> metrics -> sweep -> comparison -> demo` 链路不变。
- 用 `sequential`、`stride`、`hotspot` 三个 case 观察平均延迟、尾延迟、
  `bank_conflict_ratio_pct` 和 `throughput_txn_per_us` 的变化。

输入：

- `examples/lt/lt.robot`
- 内建 synthetic workload patterns：
  - `sequential`
  - `stride`
  - `hotspot`

输出：

- `examples/lt/results/memory_access_pattern_lab/trace.csv`
- `examples/lt/results/memory_access_pattern_lab/summary.csv`
- `examples/lt/results/memory_access_pattern_lab/comparison.md`

运行命令：

```bash
python3 examples/lt/tools/demo_memory_access_pattern_lab.py \
  --robot examples/lt/lt.robot \
  --output-dir examples/lt/results/memory_access_pattern_lab \
  --renode-test-cmd renode-test
```

Ubuntu 验证结果：

```text
[demo] Phase 16A Memory Access Pattern MVP PASS
```

关键结果：

| pattern | avg_latency_ns | p99_latency_ns | bank_conflict_ratio_pct | throughput_txn_per_us |
| --- | ---: | ---: | ---: | ---: |
| `sequential` | 100.000 | 120.000 | 0.000 | 20.000 |
| `stride` | 119.688 | 140.000 | 98.438 | 16.710 |
| `hotspot` | 100.000 | 120.000 | 0.000 | 20.000 |

工程解释：

Phase 16A 复用当前 LT trace 和 metrics aggregation 思路。`stride` 的
`bank_conflict_ratio_pct` 达到 `98.438%`，原因是 Phase 6 minimal bank model 使用：

```text
bank_id = (masked_address / 4) % 4
```

`sequential` 使用 `stride=4` 时，word address 会在 4 个 minimal banks 之间轮转。
`stride` case 使用 `stride=16`，等价于每次跨过 4 个 word；代入 modulo-4 bank mapping
后会反复回到同一个 bank。`SimpleBusLT` 又按 target 记录上一次访问的 bank，所以同一
target 上连续回到同一 bank 的 transaction 会触发 `bank_conflict_delay_ns`。

非目标声明：

- 不声称 cycle accuracy。
- 不声称 AXI / CHI / NoC / DRAM protocol compliance。
- 不声称真实 cache、DRAM controller、bank scheduler 或 production interconnect 行为。
- 这些数字是当前 LT 架构级实验结果，不是通用硬件 timing claim。

### Project B：归一化 Trace Replay Bridge MVP

目标：

- 把流量来源从内建 synthetic pattern 扩展到 normalized external trace replay。
- 第一阶段只定义 trace interface 和 replay demo。
- 保持输出仍然是 `trace.csv -> summary.csv -> comparison.md`。
- 面向后续 gem5-derived trace replay 预留接口，但当前不接真实 gem5。

输入：

- `examples/lt/traces/sample_sequential_trace.csv`
- `examples/lt/traces/sample_stride_trace.csv`

Normalized trace CSV schema：

```text
workload_name,txn_id,timestamp_ns,initiator_id,command,address,size_bytes
```

MVP 限定：

- `initiator_id = 101`
- `command = READ`
- `size_bytes = 4`
- `address` 支持 decimal 或 `0x` hexadecimal

输出：

- `examples/lt/results/trace_replay_lab/trace.csv`
- `examples/lt/results/trace_replay_lab/summary.csv`
- `examples/lt/results/trace_replay_lab/comparison.md`

运行命令：

```bash
python3 examples/lt/tools/run_trace_replay_lab.py \
  --validate-only \
  --trace examples/lt/traces/sample_sequential_trace.csv \
  --trace examples/lt/traces/sample_stride_trace.csv

python3 examples/lt/tools/demo_trace_replay_lab.py
```

Ubuntu 验证结果：

```text
[demo] Project B Normalized Trace Replay MVP PASS
```

关键结果：

| workload_name | num_transactions | avg_latency_ns | p99_latency_ns | bank_conflict_ratio_pct | throughput_txn_per_us |
| --- | ---: | ---: | ---: | ---: | ---: |
| `sample_sequential` | 64 | 100.000 | 100.000 | 0.000 | 10.000 |
| `sample_stride` | 64 | 119.688 | 120.000 | 98.438 | 9.969 |

工程解释：

Project B MVP 不依赖 Renode runtime，也不运行真实 gem5。它用 Python 标准库读取
normalized trace，按 `timestamp_ns` 和 `txn_id` 排序，保留 `workload_name` 和
`txn_id` 到输出 trace，复用当前 LT minimal bank model 的抽象逻辑计算
`bank_conflict_ratio_pct`，再生成一行一个 workload 的 `summary.csv` 和只比较
`sample_sequential` / `sample_stride` 的 `comparison.md`。

`sample_stride` 使用 16-byte spacing，连续 transaction 会映射回同一个 minimal bank，
因此 bank conflict ratio 与 Phase 16A 的 stride case 一致为 `98.438%`。这个结果说明
trace replay path 可以复现同一类 architecture-level bank conflict 观测，而不是说明
真实硬件 bank timing。

非目标声明：

- 不声称 cycle accuracy。
- 不声称 AXI / CHI / NoC / DRAM protocol compliance。
- Project B 第一阶段不接真实 gem5。
- Project B 第一阶段不做 gem5-SystemC live co-simulation。
- `timestamp_ns` 只是 normalized issue-time / ordering hint，不是 gem5 timing，也不是
  cycle timing。
- 当前 MVP 不是 GPU、cache、DRAM、AXI、CHI、NoC 或 gem5 co-simulation model。

### Project C：gem5 SE Trace Extraction MVP

目标：

- 使用 gem5 SE mode 作为 offline trace producer。
- 运行 AArch64 C workload，输出 `PROJECT_C_MEM` markers。
- 把 marker stream 转成 Project B 可读取的 normalized trace CSV。
- 复用 `run_trace_replay_lab.py` 生成 `summary.csv` 和 `comparison.md`。
- 保持 SystemC/TLM lab 作为 replay and analysis backend。

验证链路：

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

输入 workload：

- `examples/lt/workloads/gem5_se/sequential_scan.c`
- `examples/lt/workloads/gem5_se/stride_scan.c`

生成 AArch64 静态二进制：

```bash
aarch64-linux-gnu-gcc -O0 -static \
  examples/lt/workloads/gem5_se/sequential_scan.c \
  -o build/examples/lt/workloads/gem5_se/sequential_scan

aarch64-linux-gnu-gcc -O0 -static \
  examples/lt/workloads/gem5_se/stride_scan.c \
  -o build/examples/lt/workloads/gem5_se/stride_scan
```

运行 gem5 SE trace extraction：

```bash
python3 examples/lt/tools/run_gem5_se_trace_extraction.py \
  --gem5-binary ~/gem5/build/ARM/gem5.opt \
  --gem5-config ~/gem5/configs/deprecated/example/se.py \
  --workload build/examples/lt/workloads/gem5_se/sequential_scan \
  --workload-name gem5_sequential_scan \
  --output-dir examples/lt/results/gem5_se_trace_extraction/sequential \
  --normalized-output examples/lt/traces/gem5_sequential_trace.csv

python3 examples/lt/tools/run_gem5_se_trace_extraction.py \
  --gem5-binary ~/gem5/build/ARM/gem5.opt \
  --gem5-config ~/gem5/configs/deprecated/example/se.py \
  --workload build/examples/lt/workloads/gem5_se/stride_scan \
  --workload-name gem5_stride_scan \
  --output-dir examples/lt/results/gem5_se_trace_extraction/stride \
  --normalized-output examples/lt/traces/gem5_stride_trace.csv
```

Replay：

```bash
python3 examples/lt/tools/run_trace_replay_lab.py \
  --trace examples/lt/traces/gem5_sequential_trace.csv \
  --trace examples/lt/traces/gem5_stride_trace.csv \
  --output-dir examples/lt/results/gem5_trace_replay_lab
```

输出：

- `examples/lt/traces/gem5_sequential_trace.csv`
- `examples/lt/traces/gem5_stride_trace.csv`
- `examples/lt/results/gem5_trace_replay_lab/trace.csv`
- `examples/lt/results/gem5_trace_replay_lab/summary.csv`
- `examples/lt/results/gem5_trace_replay_lab/comparison.md`

Ubuntu 验证结果：

| workload_name | num_transactions | avg_latency_ns | p99_latency_ns | bank_conflict_ratio_pct | throughput_txn_per_us |
| --- | ---: | ---: | ---: | ---: | ---: |
| `gem5_sequential_scan` | 64 | 100.000 | 100.000 | 0.000 | 10.000 |
| `gem5_stride_scan` | 64 | 119.688 | 120.000 | 98.438 | 9.969 |

工程解释：

Project C 没有把 gem5 接进 SystemC 仿真内核。gem5 SE mode 只运行 AArch64 user-level
workload，并把 workload 里的 `PROJECT_C_MEM` markers 捕获到 `run_stdout.txt`。
`convert_gem5_se_trace.py` 把这些 markers 转成 normalized trace CSV；随后
`run_trace_replay_lab.py` 按 Project B replay path 计算 architecture-level latency、
bank conflict 和 throughput 指标。

`gem5_stride_scan` 使用 16-byte spacing，经过 normalized trace replay 后，在当前 LT
minimal bank model 中触发 `98.438%` 的 bank conflict ratio。这个结果说明 gem5
SE-derived trace 可以进入现有 replay and analysis backend，并复现同类
architecture-level access-pattern 观测。

非目标声明：

- gem5 只作为 offline trace producer。
- SystemC/TLM lab 只作为 replay and analysis backend。
- 这不是 gem5-SystemC live co-simulation。
- 这不是 full-system Linux。
- 这不是 cycle-accurate GPU / AXI / CHI / NoC / DRAM model。
- `timestamp_ns` 是 normalized issue-time / ordering hint，不是 gem5 timing，也不是
  cycle timing。

### Project D：Standalone C++ Trace Replay Engine MVP

目标：

- 把 Project B / Project C 当前 Python replay 的核心 metrics 逻辑迁移到 standalone
  C++ replay engine。
- 输入 normalized trace CSV。
- 输出 `trace.csv` 和 `summary.csv`。
- 保持 Python 负责 demo orchestration、Python vs C++ metrics equivalence check 和
  `comparison.md` 生成。
- 让演进链路从 Python replay、gem5 SE-derived trace，推进到 standalone C++ simulator
  engineering。

演进关系：

```text
Python trace replay
-> gem5 SE-derived trace
-> standalone C++ replay engine
```

构建和验证命令：

```bash
cmake -S examples/lt/replay_cpp -B build/examples/lt/replay_cpp
cmake --build build/examples/lt/replay_cpp -j"$(nproc)"

python3 examples/lt/tools/demo_cpp_trace_replay_lab.py
```

输出：

- `examples/lt/results/cpp_trace_replay_lab/trace.csv`
- `examples/lt/results/cpp_trace_replay_lab/summary.csv`
- `examples/lt/results/cpp_trace_replay_lab/comparison.md`

Ubuntu 验证结果：

```text
[replay-cpp] Project D standalone C++ trace replay PASS
[compare] Python vs C++ replay summary equivalence PASS
[demo-cpp] Project D Standalone C++ Trace Replay MVP PASS
```

工程解释：

Project D 的 C++ binary 读取一个或多个 normalized trace CSV，复刻 Project B Python
replay 的 latency、minimal bank conflict 和 throughput metrics 逻辑，并输出与 Python
baseline 对齐的 `summary.csv`。demo wrapper 会运行 C++ replay、运行 Python replay
baseline、比较 summary metrics，并生成 `comparison.md`。

非目标声明：

- Project D 不接 SystemC kernel。
- Project D 不做 gem5 live co-simulation。
- Project D 不声称 cycle accuracy。
- Project D 不实现 cache、DRAM、AXI、CHI 或 NoC protocol model。

## 工作负载参数

如果没有设置 knobs，默认行为保持原始 `lt.robot` baseline workload。

- `LT_BURST_COUNT`：每个 initiator 的 transaction count。
- `LT_ADDRESS_STRIDE`：生成 workload 的 address stride。
- `LT_ENABLE_INITIATOR_101`：启用或禁用 initiator 101。
- `LT_ENABLE_INITIATOR_102`：启用或禁用 initiator 102。
- `LT_TARGET_PATTERN`：
  - `both`：当前 default pattern，访问 target 201 和 target 202。
  - `target201`：只访问 target 201。
  - `target202`：只访问 target 202。
- `LT_MEMORY_PATTERN`：
  - `legacy`：保持原始 workload phase 行为。
  - `sequential`：按 `LT_ADDRESS_STRIDE` 生成连续 pattern。
  - `stride`：使用较大 stride 生成 locality / bank-conflict 对比 pattern。
  - `hotspot`：按 `LT_HOTSPOT_RATIO` 把部分 transaction 固定到热点地址。
- `LT_HOTSPOT_RATIO`：`hotspot` pattern 中热点 transaction 的比例，Phase 16A 默认使用
  `0.8`。

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

## 从 LT 工作流到 AT 时序细化的路线图

当前版本是基于 LT 的架构级性能分析工作流，不是 AT 或 cycle-accurate timing model。
它的价值在于先建立一条可重复的实验骨架：

- workload parameterization
- transaction trace observability
- architecture-level latency decomposition
- sweep comparison
- reproducible demo

当前 LT 版本不声称解决这些问题：

- cycle-accurate timing
- real AXI / CHI / NoC protocol timing
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

| 层级 | 当前 LT lab | 未来 AT refinement |
| --- | --- | --- |
| protocol abstraction | blocking `b_transport` transaction | non-blocking `nb_transport_fw` / `nb_transport_bw` phases |
| timing fidelity | transaction-level annotated delay | phase-level timing with request/response handshakes |
| concurrency | 最小 target serialization 和 bank conflict | outstanding transactions、phase overlap、response ordering |
| queue modeling | target `busy_until`、queue delay、bank conflict penalty | request arbitration、initiator queues、target response scheduling |
| trace fields | transaction latency、queue/service/bank delay、workload config | `BEGIN_REQ` / `END_REQ` / `BEGIN_RESP` / `END_RESP` timing 和 outstanding IDs |
| 适用场景 | 快速建立 workload -> trace -> metrics -> sweep -> interpretation 骨架 | 细化 timing protocol fidelity 和更接近真实互连行为的分析 |

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
- 目前没有 AT / non-blocking timing path analysis。
- Project B 第一阶段不接真实 gem5。
- Project B 第一阶段不做 gem5-SystemC live co-simulation。
- Project C 不做 gem5-SystemC live co-simulation。
- Project C 不做 full-system Linux。
- Project C 不声称 cycle-accurate GPU / AXI / CHI / NoC / DRAM model。

## 下一步

适合继续保持小而可重复的方向：

- 把 sweep case matrix 移到一个小配置文件中。
- 扩展 Phase 16A 到更多 pattern，例如 read-only、write-only 或 multi-target variant。
- 增加显式 arbitration policy knobs。
- 增加简单 per-target bandwidth 参数。
- 改进 Project C 的 workload marker 过滤、PC/symbol metadata 和 trace quality。
