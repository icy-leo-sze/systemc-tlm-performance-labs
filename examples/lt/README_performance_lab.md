# examples/lt 性能建模实验室

`examples/lt` 是一个基于原始 Renode + SystemC/TLM loosely-timed 示例改造出来的小型
性能建模实验室。它保留了原来的 Renode bridge 和 LT blocking transport 路径，并在此
基础上加入 transaction trace、latency 分析、workload sweep，以及一个最小 bank
conflict / locality 模型。

这个 lab 的目标是把 transaction-level trace 转成 architecture-level latency analysis。
它可以把一次 transaction 的延迟拆成：

- target service cost
- shared-resource queue delay
- minimal bank conflict delay

它还可以通过可重复的 sweep cases 比较 single initiator、dual initiator、target hotspot
和 stride/locality workload。

这仍然是一个 minimal LT performance model，不是完整 NoC、cache 或 DRAM 模型。

## 这个 Lab 能说明什么

- 两个 initiator 共享同一条 target path 时，会产生 queue delay。
- target 201 hotspot 比 target 202 hotspot 慢，因为 target 201 的 service delay 更高。
- 在 Phase 6 minimal bank model 下，`stride=16` 相比 `stride=4` 会提高 bank conflict
  ratio。
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

## 快速开始

Ubuntu 示例，从仓库根目录执行：

```bash
cd /home/leo/renode-systemc-examples

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

column -s, -t examples/lt/results/sweep/summary.csv | sed -n '1,12p'
sed -n '1,220p' examples/lt/results/sweep/comparison.md
```

如果 `renode-test` 不在 `PATH` 中，可以显式指定：

```bash
python3 examples/lt/tools/run_workload_sweep.py \
  --renode-test-cmd /home/leo/tools/renode_1.16.1-dotnet_portable/renode-test \
  --robot examples/lt/lt.robot \
  --output-dir examples/lt/results/sweep \
  --keep-going
```

如果 `lt` binary 还没有构建，可以先执行：

```bash
cd /home/leo/renode-systemc-examples/examples/lt

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
- 给 `summary.csv` 和 `comparison.md` 增加 tail latency metrics
- 增加显式 arbitration policy knobs
- 增加简单 per-target bandwidth 参数
