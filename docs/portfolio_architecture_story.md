# SystemC/TLM Architecture Performance Modeling Portfolio

## 1. One-Minute Summary

This repository is a portfolio of bounded architecture performance modeling labs.
它从 LT workload bottleneck characterization 起步，逐步推进到 AT transaction
timing、multi-initiator contention、QoS-like sensitivity 和 SLA violation
analysis。项目目标不是 protocol compliance 或 cycle accuracy，而是在 RTL 之前用
较低成本的模型支持早期 architecture reasoning。它把 synthetic workloads、
traces、metrics、sweeps 和 generated reports 串成一条可复现链路，让 reviewer
能看到每个结论来自哪些输入和指标。Project K/L 关注 memory bottleneck 和
evidence-driven recommendation，Project AT-1/2/3 关注 phase timing、contention、
fairness、tail latency 和 SLA tradeoff。当前模型适合表达趋势、瓶颈、policy
sensitivity 和 bounded recommendation，不适合表达真实芯片验证或生产级协议签核。
这也是它的作品集边界：展示 SoC architecture performance modeling 判断力，而不是把
教学性模型包装成工业实现。

## 2. Modeling Pipeline

| Stage | Project | Modeling Level | Main Question | Key Metrics | Output Artifact | Claim Boundary |
| --- | --- | --- | --- | --- | --- | --- |
| LT bottleneck evidence | Project K | LT / memory subsystem abstraction | Which workload pattern exposes which memory bottleneck? | queue latency, service latency, bank conflict ratio, throughput | summary / sweep / report | Synthetic trace 上的趋势级 bottleneck attribution；不是真实 workload 或硬件 counter evidence |
| LT recommendation layer | Project L | LT / evidence-driven recommendation | Given metrics, what architecture action is supported by evidence? | sensitivity score, bottleneck classification, confidence | recommendation CSV and report | 基于 Project K metrics 的 bounded recommendation；不是 production signoff 或 silicon claim |
| AT phase timing | Project AT-1 | AT / single-initiator four-phase timing | How do BEGIN_REQ, END_REQ, BEGIN_RESP, END_RESP expose transaction timing? | request accept latency, service latency, response latency, blocked time | trace / summary / report | TLM-2.0 AT phase observability；不是 AXI / CHI protocol implementation 或 cycle accuracy |
| AT contention | Project AT-2 | AT / multi-initiator contention | How do arbitration policies affect fairness and tail latency? | p95/p99 latency, arbitration delay, back-pressure, fairness index | policy summary and report | bounded contention and arbitration comparison；不是实际 NoC model 或 silicon validation |
| AT QoS-like sensitivity | Project AT-3 | AT / QoS-like sensitivity and SLA analysis | How do weights, queue depth, and service latency affect SLA violations? | SLA violation rate, p99 latency, fairness, throughput, recommendation | sweep summary, recommendations, report | QoS-like architecture exploration；不是 AXI / CHI QoS compliance、cache coherence 或 production signoff |

## 3. Why LT and AT Both Matter

LT 和 AT 是 complementary, not competing。

LT 适合 faster conceptual exploration。它可以快速构造 synthetic workload，
提取 high-level trace，并用 latency decomposition、bank conflict ratio、
throughput 和 sensitivity sweep 观察 memory architecture tradeoff。对于 Project K/L
这类问题，LT 的价值在于把 workload bottleneck 和 recommendation logic 做成可复现、
可解释、可审计的实验链路。

AT 适合观察 transaction phase timing。它把 `BEGIN_REQ`、`END_REQ`、`BEGIN_RESP`
和 `END_RESP` 暴露到 trace 层，让 request acceptance、response timing、queueing、
back-pressure、multi-initiator contention 和 QoS-like arbitration tradeoff 可以被
单独分析。对于 Project AT-1/2/3，AT 更接近早期 SoC architecture exploration 里对
仲裁、排队、tail latency 和 SLA risk 的讨论方式。

## 4. Architecture Reasoning Examples

1. Project K/L: 如果 `bank_conflict_ratio_pct` 占主导，增加 modeled bank count 或调整
   address mapping 可能有帮助，但这只是基于当前 synthetic trace 的 architecture
   hypothesis。
2. Project AT-2: 如果 fixed priority 下 p99 latency 上升，说明 lower-priority traffic
   正在被牺牲，policy 需要同时看 average latency 和 tail latency。
3. Project AT-3: 如果 weighted arbitration 保护 `accel0` 但伤害 `cpu0`，QoS weights
   需要显式 trade-off review，而不是只报告 protected traffic 的改善。
4. Project AT-3: 如果 shallow queue depth 提高 back-pressure 和 SLA violation rate，
   queue depth 可能是瓶颈的一部分，应和 service latency 一起 sweep。
5. Project AT-1/AT-3: 如果 slow memory service 支配所有 initiator 的 latency，
   arbitration tuning alone cannot solve the problem。
6. Project AT-2: 如果 round-robin improves fairness but not tail latency，fairness
   和 latency 应该分开分析，不能用单一分数替代。

## 5. What This Portfolio Demonstrates

- SystemC/TLM modeling
- LT vs AT modeling awareness
- synthetic workload design
- trace generation and analysis
- latency decomposition
- multi-initiator contention modeling
- arbitration policy comparison
- QoS-like sensitivity analysis
- SLA violation detection
- evidence-driven recommendation
- claim-boundary discipline
- reproducible demo scripts
- CMake-based validation across Mac and Ubuntu

## 6. What This Portfolio Does Not Claim

这些边界不是削弱项目价值，而是让作品集的 architecture reasoning 保持可信：当前仓库展示
的是早期建模、指标解释和 tradeoff analysis，不是生产级协议、RTL 或芯片签核流程。

- No AXI / CHI protocol compliance.
- No cycle accuracy.
- No real NoC model.
- No cache coherence model.
- No real DRAM timing model.
- No silicon validation.
- No production signoff.
- No GPU simulation.
- No real workload performance claim.
- No PMU / perf / Nsight correlation claim unless explicitly added later.

## 7. Interview Narrative

I built this repository to demonstrate how early architecture performance
modeling can guide design trade-offs before RTL. The project starts with LT
workload bottleneck analysis, where synthetic access patterns are converted into
traces, latency decomposition, bottleneck classification, and bounded memory
architecture recommendations. That gives me a fast way to reason about whether a
workload appears queue-bound, service-bound, or bank-conflict-bound before
committing to lower-level implementation detail.

I then extended the portfolio into AT transaction timing. Project AT-1 exposes
the four TLM phases, so request acceptance, service latency, response latency,
and initiator blocked time can be measured directly. Project AT-2 moves from a
single initiator to multi-initiator arbitration, where policy choices affect
fairness, back-pressure, and tail latency. Project AT-3 adds QoS-like
sensitivity and SLA violation detection, showing how weights, queue depth, and
service latency interact when traffic classes compete for shared resources.

The important boundary is that this is not a claim of protocol compliance,
cycle accuracy, silicon validation, or production signoff. It is a bounded
architecture modeling portfolio. This is aligned with the kind of reasoning used
in SoC performance modeling and architecture exploration roles, including roles
that care about NVIDIA / Apple style architecture trade-off thinking, without
claiming any internal company work.

## 8. Suggested Reading Path

1. Start with README Project Map.
2. Read `docs/portfolio_architecture_story.md`.
3. Run Project AT-3 demo.
4. Inspect Project AT-3 recommendations.
5. Backtrack to Project AT-2 for arbitration.
6. Backtrack to AT-1 for four-phase timing.
7. Backtrack to K/L for LT bottleneck and recommendation logic.

## 9. Future Roadmap

- AT-4: Regression Dashboard / Portfolio Evidence Pack
- AT-5: Cache-like Shared Resource Modeling
- AT-6: NoC-inspired Topology Exploration under explicit non-compliance boundary
- External trace ingestion from gem5 or synthetic accelerator traces
