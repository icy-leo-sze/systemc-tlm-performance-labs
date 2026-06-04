# SystemC/TLM Architecture Performance Labs

## 项目定位

本仓库是一个 SystemC/TLM 架构级性能建模实验室。项目从 LT 架构级性能工作流起步，
并逐步扩展到 AT phase-level timing refinement。部分 LT 示例保留了 Renode-SystemC
集成基础，但当前项目的重点不是 fork 来源，而是一条可重复的实验链路：

```text
workload -> trace -> metrics -> sweep -> comparison -> demo
```

本项目不是 cycle-accurate AXI、CHI 或 NoC 模型。

## 项目目录

| 实验室 | 路径 | 抽象层级 | 主要能力 | 演示命令 |
| --- | --- | --- | --- | --- |
| LT 性能实验室 | [`examples/lt`](examples/lt) | LT | 延迟分解、workload sweep、memory access pattern sweep、normalized trace replay | `python3 examples/lt/tools/demo_performance_lab.py` |
| AT 仲裁实验室 | [`examples/at`](examples/at) | AT | TLM phase trace 和 arbitration policy sweep | `python3 examples/at/tools/demo_at_lab.py --binary ./build/examples/at/at` |

详细说明：

- LT 工作流：[`examples/lt/README_performance_lab.md`](examples/lt/README_performance_lab.md)
- AT 工作流：[`examples/at/README.md`](examples/at/README.md)

LT lab 现在有两个边界清晰的性能建模入口：

1. 内建 synthetic memory access pattern sweep。
2. normalized external trace replay MVP。

两者都保持同一条 `trace -> metrics -> summary.csv -> comparison.md` 链路。详细说明和
已验证结果见 [`examples/lt/README_performance_lab.md`](examples/lt/README_performance_lab.md)。

## 为什么有价值

LT 主线展示的是架构级性能分析工作流：workload knobs、transaction trace
instrumentation、延迟分解、workload sweep 和自动生成的 comparison report。

AT 主线展示的是 TLM-2.0 base protocol phase 的 timing observability，包括
`BEGIN_REQ`、`END_REQ`、`BEGIN_RESP` 和 `END_RESP`。它也展示了一个小型 arbitration
policy knob 如何改变 request-accept latency。

这两个实验室合在一起，形成一条从架构级工作流到 AT timing refinement 的演进
路径，但不声称 protocol completeness 或 cycle accuracy。

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

LT 的 Renode 配置、生成文件和结果解释见
[`examples/lt/README_performance_lab.md`](examples/lt/README_performance_lab.md)。

## 关键结果快照

下面是已验证的实验快照，不是硬件 timing claim。

| 实验室 | 场景 | 结果 |
| --- | --- | --- |
| LT | `stride=4` 到 `stride=16` | `bank_conflict_ratio_pct` 从 `46.875%` 上升到 `98.438%`；`avg_delay_ns` 从 `164.688 ns` 上升到 `185.312 ns` |
| LT Phase 16A | `sequential` / `stride` / `hotspot` | `stride` 的 `bank_conflict_ratio_pct = 98.438%`，明显高于 `sequential` 和 `hotspot` |
| LT Project B | `sample_sequential` / `sample_stride` | normalized trace replay 复现同类 bank conflict 观测：`sample_stride bank_conflict_ratio_pct = 98.438%` |
| AT | `fifo` | `complete_transactions = 4` |
| AT | `priority_101` | `101xxx` 更快被接受：`101xxx avg = 1.000 ns`，`102xxx avg = 6.000 ns` |
| AT | `priority_102` | `102xxx` 更快被接受：`102xxx avg = 1.000 ns`，`101xxx avg = 6.000 ns` |

## 路线图

后续方向保持小步、可验证：

- AT multi-target path。
- AT response scheduling。
- outstanding transaction depth。
- 等价 workload 下的 LT vs AT 对比。
- normalized trace replay 到 gem5-derived trace replay 的离线扩展。

这些都是未来方向，不是当前已完成能力。

## 边界

- 本仓库是教学和实验性质的架构级性能建模实验室。
- 不声称 cycle accuracy。
- 不声称 AXI、CHI 或 NoC compliance。
- 不声称真实 interconnect protocol support。
- LT lab 是架构级工作流，不是最终 timing model。
- AT lab 是 smoke / arbitration lab，不是 production interconnect model。
- Project B 第一阶段不接真实 gem5，也不做 gem5-SystemC live co-simulation。
- 如果本地存在 Doulos AT example，它只是 protocol-shape reference，不作为本项目
  mainline deliverable，也不由本仓库重新分发。

## 许可证和致谢

部分 LT 示例基于 Renode-SystemC 集成基础，上游 notice 已按需要保留。
详见 [`LICENSE`](LICENSE) 和 [`NOTICE`](NOTICE)。
