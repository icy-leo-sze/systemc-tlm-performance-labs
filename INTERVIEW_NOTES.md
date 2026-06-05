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

## 11. 面试官可能追问的问题和参考回答

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

## 12. Phase 16 后续计划

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
