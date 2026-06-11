# Interview Notes

Target roles: SoC Architecture, Performance Modeling, SystemC/TLM, ESL, and
Architecture Performance Analysis.

Project: `SystemC/TLM Architecture Performance Labs`

Core chain:

```text
workload → trace → metrics → sweep → comparison → demo
```

## 1. 60秒项目介绍

这是一个 SystemC/TLM virtual platform performance modeling lab。我的目标不是做一个
cycle-accurate AXI、CHI 或 NoC 模型，而是建立一个可复现实验链路：
`workload → trace → metrics → sweep → comparison → demo`。

项目分成两条主线。`examples/lt` 是 LT Performance Lab，用来做
architecture-level performance workflow：通过 workload knob 改变访问模式，
采集 LT trace，拆分 `queue_delay_ns`、`target_service_delay_ns` 和
`bank_conflict_delay_ns`，再用 sweep 生成 `summary.csv` 和 `comparison.md`。

`examples/at` 是 AT Arbitration Lab，用来观察 TLM-2.0 AT phase-level timing：
它记录 `BEGIN_REQ / END_REQ / BEGIN_RESP / END_RESP`，并通过 `fifo`、
`priority_101`、`priority_102` 三种 arbitration policy 比较
`request_accept_latency_ns`。

我希望这个项目证明的是：我能把一个建模问题拆成可运行的 workload、可解释的
trace、可量化的 metrics、可复现的 sweep 和适合面试/作品集展示的 demo。

## 2. 3分钟技术讲解

这个项目从 LT 开始，因为 LT 更适合先建立 architecture-level 的实验框架。LT
lab 里我关注的是 workload 对性能指标的影响，而不是模拟每一个 bus cycle。
例如改变 stride 后，访问模式会影响 bank conflict。实验结果显示：
`stride=16` 让 `bank_conflict_ratio_pct` 从 `46.875%` 上升到 `98.438%`，
`avg_delay_ns` 从 `164.688 ns` 上升到 `185.312 ns`。

这个结果本身不是硬件真实性声明，而是说明建模链路有效：workload knob 改变了
访问形态，trace 捕捉到了延迟组成，metrics 能聚合出趋势，sweep 能复现实验，
comparison 能把差异表达清楚，demo 能一条命令重跑。

AT lab 是下一步。LT 可以解释 workload-level latency composition，但如果要讨论
TLM-2.0 phase-level timing，就需要 AT。AT lab 记录四个 base protocol phase：
`BEGIN_REQ`、`END_REQ`、`BEGIN_RESP`、`END_RESP`，trace schema 包含
`txn_id`、`direction` 和 `response_status` 等字段。它不是完整 interconnect，
而是一个小的 dual initiator arbitration lab。

AT 的关键观察是 arbitration policy 会改变请求被接受的延迟。在 `fifo` 下：
`102001 request_accept_latency_ns = 1.000`，
`101001 request_accept_latency_ns = 6.000`，
`102002 request_accept_latency_ns = 6.000`，
`101002 request_accept_latency_ns = 6.000`。

在 `priority_101` 下，`101001 = 1.000`，`101002 = 1.000`，
`102001 = 11.000`。在 `priority_102` 下，`102001 = 1.000`，
`102002 = 1.000`，`101001 = 11.000`。这说明 policy knob 对 AT phase trace
中的 request acceptance timing 有可观测影响。

AT demo 的复现命令是：

```bash
python3 examples/at/tools/demo_at_lab.py --binary ./build/examples/at/at
```

## 3. LT Performance Lab 讲解

`examples/lt` 关注的是 architecture-level performance workflow。它把一次
transaction 的延迟拆成几个可解释部分：

- `queue_delay_ns`
- `target_service_delay_ns`
- `bank_conflict_delay_ns`

实验不是只跑单个 case，而是通过 workload knobs 和 workload sweep 比较不同访问
模式。输出包括 `summary.csv` 和 `comparison.md`，用于把单次 trace 变成可读的
性能结论。

真实数据可以这样讲：

- `stride=16` 让 `bank_conflict_ratio_pct` 从 `46.875%` 上升到 `98.438%`
- `avg_delay_ns` 从 `164.688 ns` 上升到 `185.312 ns`

我的解释重点是：这个 lab 证明 workload pattern 可以通过 trace 和 metrics 转化
为 architecture-level performance evidence。它不证明真实 DRAM bank timing，也不
证明 cycle-accurate memory controller 行为。

## 4. AT Arbitration Lab 讲解

`examples/at` 关注 TLM-2.0 AT phase trace 和 arbitration policy 对 timing 的影响。
trace 记录：

- `BEGIN_REQ`
- `END_REQ`
- `BEGIN_RESP`
- `END_RESP`
- `txn_id`
- `direction`
- `response_status`

工具链包括：

- `analyze_phase_trace.py`
- `run_arbitration_sweep.py`
- `demo_at_lab.py`

AT arbitration policy 包括：

- `fifo`
- `priority_101`
- `priority_102`

真实数据可以这样讲：

`fifo`:

- `102001 request_accept_latency_ns = 1.000`
- `101001 request_accept_latency_ns = 6.000`
- `102002 request_accept_latency_ns = 6.000`
- `101002 request_accept_latency_ns = 6.000`

`priority_101`:

- `101001 = 1.000`
- `101002 = 1.000`
- `102001 = 11.000`

`priority_102`:

- `102001 = 1.000`
- `102002 = 1.000`
- `101001 = 11.000`

我的解释重点是：AT lab 不是为了声称完整 interconnect，而是为了把 arbitration
policy 对 phase-level timing 的影响做成可观测、可复现、可比较的实验。

### Project AT-1：Four-Phase AT Memory Transaction Timing Lab

Project AT-1 是 `examples/at` 下新增的独立 AT 主线 demo。它不继续做 LT 统计，而是用
一个最小 initiator + memory target 展示 TLM-2.0 approximately-timed non-blocking
transport：initiator 通过 `nb_transport_fw` 发出 `BEGIN_REQ`，target 通过
`nb_transport_bw` 返回 `END_REQ` 和 `BEGIN_RESP`，initiator 再用 `END_RESP` 结束
response path。

面试叙事重点可以这样讲：

- LT 把一次 transaction latency 抽象进 blocking call；AT-1 把 request/response phase
  timing 显式暴露出来。
- `BEGIN_REQ -> END_REQ` 对应 request acceptance latency，可观察 initiator stall 和
  target back-pressure。
- target 维护有限 queue depth，因此 `bursty` 和 `hotspot` pattern 会在 trace 和
  summary 里出现 `backpressure_events` 与 `initiator_blocked_ns`。
- 这个 demo 证明我理解 TLM-2.0 non-blocking transport semantics 和 four-phase
  base-protocol timing。
- 它适合 early SoC architecture exploration before RTL，但不是 AXI / CHI protocol
  compliance、cycle-accurate simulation、silicon validation 或 production signoff。

复现命令：

```bash
python3 examples/at/tools/demo_project_at1_four_phase_memory_timing.py
```

### Project AT-2：Multi-Initiator AT Arbitration and Contention Lab

Project AT-2 是 AT 主线的下一阶段。AT-1 证明我能把单个 initiator 到 memory target
的四阶段 timing 拆出来；AT-2 则把问题推进到多个 initiator 共享一个 simple AT
interconnect / memory target 时，arbitration policy 如何影响 request latency、
p95 / p99 tail latency、initiator-level fairness、back-pressure 和 throughput。

模型里有三个 synthetic initiator：`cpu0`、`dma0`、`accel0`。它们通过
`nb_transport_fw` 发出 `BEGIN_REQ`，interconnect 维护 per-initiator request queue，
再用 `round_robin`、`fixed_priority` 或 `weighted_priority` 选择下一个 request
送往有限 queue depth 的 memory target。target 通过 `END_REQ` 和 `BEGIN_RESP`
返回 timing，initiator 再发 `END_RESP`。每笔 transaction 都会写入四阶段或近似四阶段
timestamp，并由 Python demo 汇总成 initiator-level 和 policy-level metrics。

面试叙事重点可以这样讲：

- multi-initiator contention 会把单个 transaction timing 问题变成共享路径资源竞争问题。
- `round_robin` 更适合作为 fairness baseline，但不保证每个 initiator 都有最低 tail latency。
- `fixed_priority` 可以保护高优先级 traffic，例如 `dma0`，但低优先级 initiator 的 p95 / p99
  latency 可能显著上升。
- `weighted_priority` 是 QoS-like tradeoff，可以偏向 `accel0`，但这不是 AXI QoS /
  CHI QoS compliance。
- bursty traffic 会放大 queueing pressure 和 back-pressure，这些现象可以在
  `initiator_blocked_ns`、`backpressure_events`、`fairness_share` 和
  `fairness_index` 中观察到。

复现命令：

```bash
cmake -S examples/at -B build-at2 \
  -DUSER_SYSTEMC_INCLUDE_DIR=$HOME/local/systemc/include \
  -DUSER_SYSTEMC_LIB_DIR=$HOME/local/systemc/lib
cmake --build build-at2 --target project_at2_multi_initiator_arbitration -j
python3 examples/at/tools/demo_project_at2_multi_initiator_arbitration.py \
  --build-dir build-at2
```

边界讲法要保持清楚：AT-2 是 teaching / architecture modeling lab，适合讨论 RTL 前的
SoC architecture exploration 和 arbitration tradeoff；它不是 AXI / CHI protocol
compliance，不是 cycle-accurate interconnect model，不是真实 NoC，不是 silicon
validation，也不是 production signoff。

### Project AT-3：QoS Sensitivity and SLA Violation Lab

Project AT-3 是 AT 主线的第三阶段。AT-1 展示 single transaction phase timing；
AT-2 展示多个 initiator 的 arbitration、contention、fairness 和 tail latency；
AT-3 则把问题推进到 QoS-like weighted arbitration、SLA violation detection 和
bounded architecture recommendation。

模型里仍然使用 synthetic `cpu0`、`dma0`、`accel0` traffic，但每个 initiator 有明确
traffic class 和 SLA target latency。demo 会扫描不同 weight vector、queue depth、
service latency 和 burstiness，生成 per-transaction trace、initiator summary、
policy sweep 和 recommendation CSV。

面试叙事重点可以这样讲：

- QoS-like weighted arbitration 可以保护某一类 latency-sensitive traffic，例如
  `accel0` 或 interactive `cpu0`。
- 保护一个 traffic class 往往会牺牲 fairness，或者把 p95 / p99 tail latency 转移给
  其他 initiator。
- SLA violation rate 比平均 latency 更适合表达 tail-risk，尤其适合讨论 early SoC
  architecture tradeoff。
- shallow queue 会放大 back-pressure 和 SLA violation；slow memory service 是 target
  bottleneck，不能只靠 arbitration weight 解决。
- Project AT-3 的价值不是声称真实 AXI QoS / CHI QoS，而是用可复现 sweep 帮助 RTL 前
  判断该调 weight、加 queue depth、降低 service latency，还是降低 burstiness。

复现命令：

```bash
cmake -S examples/at -B build-at3 \
  -DUSER_SYSTEMC_INCLUDE_DIR=$HOME/local/systemc/include \
  -DUSER_SYSTEMC_LIB_DIR=$HOME/local/systemc/lib
cmake --build build-at3 --target project_at3_qos_sensitivity_sla -j
python3 examples/at/tools/demo_project_at3_qos_sensitivity_sla.py \
  --build-dir build-at3
```

边界讲法要保持清楚：AT-3 是 teaching / architecture modeling lab。它支持 bounded
QoS sensitivity、SLA violation analysis、protected traffic class 和 architecture
recommendation，不声称 AXI / CHI QoS compliance，不声称 cycle-accurate interconnect
model，不是真实 NoC，不是 cache coherence model，不是 silicon validation，也不是
production signoff。

## 5. 我为什么这样设计实验链路

我把实验链路设计成 `workload → trace → metrics → sweep → comparison → demo`，
原因是它符合 performance modeling 的工程闭环。

- `workload`: 定义输入条件和访问模式，而不是只看模型内部行为。
- `trace`: 保留原始观测证据，便于 debug 和解释。
- `metrics`: 把 trace 聚合成可比较的指标。
- `sweep`: 系统性改变 knob，避免单点结论。
- `comparison`: 用报告表达不同 case 的差异。
- `demo`: 让别人可以用一条命令复现主要结果。

这个链路的重点不是复杂，而是可复现和可解释。面试中我会强调：我更关心能不能
把建模假设、输入、输出和结论连接起来，而不是只展示一个模型文件。

## 6. 项目证明了什么

这个项目证明了几件事：

- 我能用 SystemC/TLM 搭建 architecture performance experiment。
- 我能把 workload knob 和 trace instrumentation 连接起来。
- 我能把 trace 转成 metrics，再通过 sweep 和 comparison 做趋势分析。
- LT lab 能展示 workload-sensitive latency decomposition。
- AT lab 能展示 phase-level timing observability 和 arbitration policy effect。
- 我能把工程结果包装成 one-command demo，而不是停留在一次手工运行。

更具体地说，LT 的 stride 实验证明了访问模式变化会反映到
`bank_conflict_ratio_pct` 和 `avg_delay_ns` 上。AT 的 arbitration 实验证明了
priority policy 会改变不同 transaction group 的 `request_accept_latency_ns`。

## 7. 项目没有证明什么

这个项目没有证明：

- 真实 AXI cycle accuracy
- 真实 CHI cycle accuracy
- 真实 NoC cycle accuracy
- 商用 interconnect 的完整协议行为
- 真实 memory controller 的全部 timing path
- silicon correlation
- RTL equivalence

我会主动说明这些边界。项目的价值是 architecture-level modeling workflow 和
phase-level timing observability，不是协议合规模型。

`references/doulos_at_example` 只是外部参考材料，用于学习 Doulos AT example 的
结构和 TLM-2.0 AT phase-level coding pattern。它不是本项目成果，也不是
`examples/at` 的主线实现。

## 8. LT vs AT 如何解释

LT 和 AT 的区别我会这样解释：

LT 更适合先建立 architecture-level 性能实验。它关注 transaction-level 的延迟、
workload pattern 和性能指标，可以比较快地把 workload 变化转成性能趋势。

AT 更适合表达 phase-level timing。它把 transaction 拆成 `BEGIN_REQ`、
`END_REQ`、`BEGIN_RESP`、`END_RESP`，因此可以观察 request acceptance、response
latency 和 arbitration policy 对 phase ordering/timing 的影响。

在这个项目里，LT 是稳定的 workflow baseline；AT 是 timing refinement path。两者
不是互相替代，而是建模抽象层次不同。

## 9. 为什么这是 Architecture-Level Performance Modeling

这是 architecture-level performance modeling，因为实验围绕 architecture knobs
和可解释性能指标展开，而不是围绕具体 RTL cycle 或协议 beat 展开。

LT 中的 stride 是 workload-level knob，bank conflict ratio 和 average delay 是
architecture-level metrics。AT 中的 arbitration policy 是 micro-architecture
policy knob，`request_accept_latency_ns` 是 phase-level observable metric。

项目的核心是比较设计选择对性能观察值的影响：先定义 workload/policy，再采集
trace，再生成 metrics 和 comparison。这正是 architecture performance analysis
需要的工作方式。

## 10. 为什么不是 AXI / CHI / NoC Cycle-Accurate Model

我不会把它描述成 AXI、CHI 或 NoC cycle-accurate model，原因很明确：

- 没有实现 AXI/CHI/NoC 的完整协议语义。
- 没有建模真实 channel、beat、credit、ordering、coherency 或 QoS 细节。
- 没有 RTL cycle-by-cycle 对齐。
- 没有 silicon 或 RTL correlation。
- 当前 AT lab 只观察 TLM-2.0 base protocol phase 和一个小的 arbitration policy。

更准确的说法是：这是一个 SystemC/TLM architecture performance modeling lab，
用于展示 workload sensitivity、trace instrumentation、metrics extraction、
sweep automation 和 AT phase-level observability。

## 11. Project K 面试叙事：Workload-Aware Bottleneck Characterization

Problem：

我想回答的问题不是“这个模型能不能预测真实 GPU 或真实 memory controller 性能”，而是：
当 workload access pattern 改变时，简化 banked memory subsystem 里的压力会如何迁移？
具体来说，`streaming`、`stride` 和 `hot_bank` 三类 core 输入会分别制造不同的
memory-system stressor：平滑连续访问、固定步长映射敏感性、以及集中到少数 bank 的
queue pressure。当前 K.2/K.3 还加入 `tiled_gemm_like` 和
`attention_like_blocked` 两类 optional synthetic access-pattern-inspired traces，但不把它们
解释成真实 GEMM、attention 或 GPU workload。

Method：

Project K 把这个问题做成一条可复现链路：

```text
synthetic workload access pattern
-> memory-system stressor
-> measurable symptom
-> bottleneck attribution
-> bounded recommendation
```

实现上我没有扩展 C++ / SystemC model，而是复用 Project E simplified banked memory
model。Python wrapper 生成 5 类 Project E-compatible synthetic traces，提取 trace-derived
features，例如 `sequentiality_score`、`dominant_stride`、`burstiness_score`、
`bank_entropy` 和 `max_bank_share`；再从 Project E `trace.csv` / `summary.csv` 提取
model-derived metrics，例如 `queue_delay_ratio`、`service_delay_ratio`、
`bank_conflict_proxy` 和 `p95_p50_latency_ratio`。

Evidence：

Project K 的 attribution 不是黑箱模型，而是显式规则。`bank_conflict_bound` 看
`max_bank_share`、`bank_entropy` 和 `bank_conflict_proxy`；`queueing_bound` 看
`queue_delay_ratio`、queue occupancy 和 rejected transactions；`service_latency_bound`
看 `service_delay_ratio`；`burstiness_bound` 看 burstiness 和 tail amplification。
K.2/K.3 还保留 `locality_loss_bound` 和 `bandwidth_pressure_bound` 作为 modeled proxy
规则，但不写成真实 cache miss 或真实 bandwidth claim。
每个 workload 的输出都会保留 `primary_bottleneck`、`confidence`、`evidence_fields` 和
`recommendation`。

Result：

当前 demo 一条命令生成 5 类 workload、5 行 summary 和 45 行
`bank_count × address_mapping` sweep 结果；K.3 同时把 CSV schema 固定为
`schema_version=k0.2` 并加入 schema / claim-boundary self-check：

```bash
python3 examples/lt/tools/demo_project_k_workload_bottleneck_lab.py
```

核心观察是：`streaming` 在当前模型中主要表现为 `service_latency_bound` baseline；
`stride` 更容易形成 same-bank waiting 和 queueing；`hot_bank` 会把 modeled bank 压满，
出现高 `queue_delay_ratio`、高 queue occupancy 和 rejected transactions。这个结果把
workload 形态、memory-system stressor、可测症状和 attribution 连成了一个可展示的
architecture case。

当前状态保留 `streaming`、`stride`、`hot_bank` 三类 core workload，同时加入
`tiled_gemm_like` 和 `attention_like_blocked` 两类 optional synthetic pattern。我会把这一步
解释成 mapping sensitivity 和 workload-shape coverage，而不是真实 GEMM、attention、GPU
或 LLM performance。

Boundary：

Project K 的 recommendation 只表示 expected direction，例如增加 modeled bank
parallelism 或分散 synthetic address mapping。它不是真实硬件收益百分比，不声称真实
GPU 性能，不声称 GEMM / attention kernel performance，不接 PMU、Linux perf 或
NVIDIA Nsight，也不做 silicon validation、production signoff、full-system cycle
accuracy 或 AXI / CHI protocol compliance。

## 12. Project L 面试叙事：Evidence-Driven Memory Architecture Recommendation

Problem：

Project L 回答的是 architecture decision support 问题：当 Project K 已经给出
workload-level bottleneck evidence 后，怎样把这些 metrics 转成有边界、可解释、可审计
的内存架构建议，而不是停留在“看起来某个指标变高了”。

Method：

Project L 不改 C++ / SystemC 模型，也不改变 Project E 或 Project K 的输出契约。它读取
Project K 的 `summary_rows` 和 `bank_count × address_mapping` sweep 结果，把
`bank_conflict_proxy`、`queue_delay_ratio`、`service_delay_ratio`、
`mapping_sensitivity_score`、`bank_count_sensitivity_score`、locality proxy 等信号解释为
bounded recommendations。输出动作被限制在几个工程上可讨论的方向：增加 modeled bank
parallelism、改变 address mapping、改善 locality / tiling、降低 queueing pressure、降低
target service latency，或者在证据不足时继续观察。

Evidence：

这一步的价值是 trace/model metric interpretation。Project L 不把 recommendation 写成
绝对收益，而是保留 `primary_bottleneck`、`confidence`、best observed bank/mapping knob、
signal strength 和 `evidence_summary`，让面试官可以从一行 recommendation 追到具体
Project K metric。

Boundary：

Project L 的 claim 是 bounded design hypothesis。它不声称真实硬件收益，不声称 GPU /
GEMM / attention workload performance，不做 PMU、Linux perf 或 Nsight correlation，也
不做 silicon validation、production signoff、cycle accuracy 或 AXI / CHI protocol
compliance。它适合 early-stage architecture tradeoff thinking：在还没有更高保真 reference
之前，先用受控 trace 和模型指标帮助决定下一步该扫 bank parallelism、mapping、locality、
queueing 还是 service-latency knob。

Role Value：

对 SoC architecture / performance modeling roles 来说，这个项目展示的是三件事：
第一，把 workload trace 和 model symptom 连接起来；第二，把 metrics 转成克制的
architecture recommendation；第三，清楚区分 supported evidence 和 unsupported claim。
这比单独展示一个脚本更接近真实 architecture exploration 的工作方式。

## 13. 面试官可能追问的问题和参考回答

### Q1: 这个项目一句话是什么？

答：这是一个 SystemC/TLM virtual platform performance modeling lab，用
`workload → trace → metrics → sweep → comparison → demo` 建立可复现实验链路。

### Q2: 你最想让面试官看到什么能力？

答：我希望展示我能把 architecture question 转成可运行实验，并把 trace 转成
可解释的 metrics 和 comparison，而不是只写一个孤立模型。

### Q3: 为什么先做 LT？

答：LT 更适合快速建立 architecture-level workflow。它能先验证 workload knob、
trace instrumentation、metrics 和 sweep 这条链路是否成立。

### Q4: 为什么还要做 AT？

答：LT 对 phase-level timing 表达有限。AT 可以记录 `BEGIN_REQ`、`END_REQ`、
`BEGIN_RESP`、`END_RESP`，更适合观察 arbitration policy 对 request acceptance
timing 的影响。

### Q5: LT lab 的关键结果是什么？

答：`stride=16` 让 `bank_conflict_ratio_pct` 从 `46.875%` 上升到 `98.438%`，
`avg_delay_ns` 从 `164.688 ns` 上升到 `185.312 ns`。我把它解释为 workload
pattern 对 latency decomposition 的可观测影响。

### Q6: AT lab 的关键结果是什么？

答：在 `priority_101` 下，`101001 = 1.000`、`101002 = 1.000`、
`102001 = 11.000`；在 `priority_102` 下，`102001 = 1.000`、
`102002 = 1.000`、`101001 = 11.000`。这说明 priority policy 改变了不同
transaction group 的 request acceptance latency。

### Q7: fifo 的结果怎么解释？

答：`fifo` 下结果是 `102001 = 1.000`，`101001 = 6.000`，
`102002 = 6.000`，`101002 = 6.000`。它反映了当前 pending request arrival
order 和 bus service timing 下的 request acceptance latency。

### Q8: 你如何保证结果可复现？

答：我没有只保留手工运行结果，而是提供 demo 和 sweep script。AT demo 可以用
`python3 examples/at/tools/demo_at_lab.py --binary ./build/examples/at/at` 复现。

### Q9: trace 为什么重要？

答：trace 是 metrics 的证据来源。没有 trace，summary 只是结论；有 trace 后，
可以回看每个 transaction 的 phase、direction、timestamp 和 response status。

### Q10: metrics 为什么不直接写在模型里？

答：模型负责产生行为和 trace，分析脚本负责聚合 metrics。这样模型和分析逻辑分离，
更容易 debug、扩展和复现实验。

### Q11: sweep 的价值是什么？

答：sweep 避免只看单点。它系统性改变 workload 或 policy，把多个 case 聚合成
`summary.csv` 和 `comparison.md`，更适合 architecture performance analysis。

### Q12: comparison.md 的价值是什么？

答：它把 raw metrics 转成面向工程判断的对比结果。面试官或 reviewer 不需要先读
全部 trace，也能看到 case 之间的差异。

### Q13: 这个项目是否 cycle accurate？

答：不是。我会明确说它不声明 cycle accuracy。它是 architecture-level 和
phase-level 的 performance modeling lab。

### Q14: 它是 AXI 模型吗？

答：不是。它没有实现 AXI 的完整 channel、beat、ordering 或协议细节，也没有
cycle-by-cycle 对齐。

### Q15: 它是 CHI 或 NoC 模型吗？

答：不是。它没有建模 coherency protocol、NoC routing、credit flow 或真实 QoS。
它只用 TLM/AT phase 和 arbitration lab 表达 timing observability。

### Q16: 为什么用 `request_accept_latency_ns`？

答：因为在 AT arbitration 场景里，请求从 `BEGIN_REQ` 到 `END_REQ` 的时间能直接
反映 request 被接受的延迟，对比较 arbitration policy 很有用。

### Q17: 为什么 trace schema 要包含 `txn_id`？

答：`txn_id` 让 analyzer 能把同一个 transaction 的四个 phase 重新组合起来，
否则只看 phase event 很难做 per-transaction latency analysis。

### Q18: 为什么要记录 `direction`？

答：AT phase 有 forward path 和 backward path。`direction` 可以帮助区分
`BEGIN_REQ`/`END_RESP` 与 `END_REQ`/`BEGIN_RESP` 的路径，避免分析时混淆。

### Q19: 为什么要记录 `response_status`？

答：因为 timing 之外还要确认 transaction 是否完成以及响应是否合理。它是 sanity
check 的一部分。

### Q20: 你从 Doulos AT example 复制了代码吗？

答：没有把 `references/doulos_at_example` 当作本项目成果，也没有把它作为
`examples/at` 主线实现。它只是外部参考材料，用来学习 AT phase-level coding
pattern。如果借鉴设计思想，需要保留 attribution。

### Q21: 如果要继续提高 AT lab，你会先做什么？

答：我会先扩展可验证的 phase-level 场景，比如 multi-target、response scheduling
或 outstanding transaction depth，而不是直接声称完整 interconnect。

### Q22: 如果面试官问 silicon correlation，你怎么回答？

答：我会说当前项目没有做 silicon correlation。它证明的是建模和实验链路，不证明
真实芯片 timing。

### Q23: 如果面试官问为什么不用 RTL？

答：RTL 适合 cycle-level implementation verification；这个项目目标是更早期的
architecture performance exploration。SystemC/TLM 更适合快速表达 workload、
policy、trace 和 metrics。

### Q24: 如果面试官问这个项目最大的限制是什么？

答：限制是模型抽象层次较高，协议和 timing 细节都被简化了。因此它适合解释趋势和
方法，不适合当作协议合规或 cycle-accurate signoff 模型。

## 14. Phase 16 后续计划

Phase 16 后我会保持同样的原则：小步扩展、每一步都有 trace、metrics、sweep 和
demo，不把未来计划说成已经完成的能力。

优先方向：

- 整理 portfolio evidence cards，让项目入口更适合面试和 hiring manager 快速阅读。
- 扩展 AT multi-target path，观察 arbitration 之外的 target selection effect。
- 加入 AT response scheduling，使 response path 的 timing 更容易比较。
- 加入 outstanding transaction depth，观察并发度对 request acceptance 和 total
  transaction latency 的影响。
- 做 LT vs AT under equivalent workload 的对照，但明确两者抽象层次不同。
- 保持 generated artifacts 和 source 分离，继续用 `summary.csv`、`comparison.md`
  和 one-command demo 做复现闭环。

我不会在后续计划里声称 AXI、CHI、NoC cycle accuracy。后续目标仍然是
architecture-level performance modeling 和 TLM phase-level timing refinement。
