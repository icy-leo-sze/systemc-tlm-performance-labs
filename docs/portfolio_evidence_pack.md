# Portfolio Evidence Pack

## 1. Purpose

这份 evidence pack 把当前 repo 中的 LT and AT labs 串成一个可复现、可审阅、可用于面试讨论的作品集入口。Project P 不新增 SystemC/TLM 功能模型；它把 Project K/L 与 Project AT-1/AT-2/AT-3/AT-4 的验证命令、生成结果、关键指标和 claim boundary 汇总成 portfolio-level evidence。

核心目标是让 reviewer 能从一条清楚路径理解项目：先看 architecture story，再运行 validation harness，再读取 CSV-derived evidence summary，最后回到各 Project report 查看细节。

## 2. Evidence Map

| Evidence Area | Projects | What It Shows | Primary Artifacts | How To Reproduce |
| --- | --- | --- | --- | --- |
| LT bottleneck characterization | Project K | synthetic workload pattern 如何触发 queueing、service latency、bank conflict proxy 和 bottleneck attribution | `project_k_workload_bottleneck_summary.csv`、`project_k_what_if_sweep_summary.csv`、`project_k_report.md` | `python3 examples/lt/tools/demo_project_k_workload_bottleneck_lab.py` |
| Evidence-driven recommendation | Project L | 如何把 Project K metrics 转成 bounded memory architecture recommendation | `project_l_recommendations.csv`、`project_l_recommendation_report.md` | `python3 examples/lt/tools/demo_project_k_workload_bottleneck_lab.py` |
| AT transaction timing | Project AT-1 | four-phase AT transaction timing、request acceptance、target service、response latency 和 back-pressure | `project_at1_summary.csv`、`project_at1_report.md`、case trace CSV | `python3 examples/at/tools/demo_project_at1_four_phase_memory_timing.py --build-dir build-at` |
| Arbitration / contention | Project AT-2 | multi-initiator arbitration policy 如何影响 fairness、back-pressure、throughput 和 p99 latency | `project_at2_policy_summary.csv`、`project_at2_report.md`、case trace CSV | `python3 examples/at/tools/demo_project_at2_multi_initiator_arbitration.py --build-dir build-at` |
| QoS-like sensitivity / SLA violation | Project AT-3 | weight vector、queue depth、service latency 如何影响 SLA violation、protected initiator 和 architecture recommendation | `project_at3_policy_sweep.csv`、`project_at3_recommendations.csv`、`project_at3_report.md` | `python3 examples/at/tools/demo_project_at3_qos_sensitivity_sla.py --build-dir build-at` |
| Cache-like shared-resource pressure | Project AT-4 | locality、hit/miss trend、MSHR-like outstanding miss pressure、shared interference / pollution proxy、p95 / p99 tail latency 和 diminishing return | `project_at4_summary.csv`、`project_at4_policy_sweep.csv`、`project_at4_recommendations.csv`、`project_at4_report.md` | `python3 examples/at/tools/demo_at4_cache_mshr_pressure.py --at-build-dir build-at` |
| Portfolio-level validation | Project P | K/L/AT-1/AT-2/AT-3/AT-4 的一键 PASS marker 检查和 CSV-derived evidence summary | `tools/run_portfolio_validation.py`、`tools/generate_portfolio_evidence_summary.py`、`docs/generated/portfolio_evidence_summary.md` | `python3 tools/run_portfolio_validation.py --at-build-dir build-at` |

## 3. Reproduction Flow

先准备 AT build。推荐在 Ubuntu 验证环境中从 repo root 运行：

```bash
cmake -S examples/at -B build-at \
  -DUSER_SYSTEMC_INCLUDE_DIR=$HOME/local/systemc/include \
  -DUSER_SYSTEMC_LIB_DIR=$HOME/local/systemc/lib

cmake --build build-at --target project_at1_four_phase_memory_timing -j
cmake --build build-at --target project_at2_multi_initiator_arbitration -j
cmake --build build-at --target project_at3_qos_sensitivity_sla -j
cmake --build build-at --target project_at4_cache_mshr_pressure -j
```

然后运行 Project P validation harness：

```bash
python3 tools/run_portfolio_validation.py --at-build-dir build-at
```

生成 portfolio evidence summary：

```bash
python3 tools/generate_portfolio_evidence_summary.py --strict
```

LT K/L demo 依赖 Project E standalone C++ banked memory controller binary。如果本地 LT build 尚未准备好，先按 `README.md` 和 `examples/lt/README_performance_lab.md` 完成 LT build。Project P 文档不强行假设 root CMake 一定可用，因为 root CMake 可能包含 Renode 相关配置；Project P harness 使用明确的 AT named project targets 构建 AT-1/2/3/4，并运行 demo、检查 PASS marker 和关键 artifacts，不依赖 legacy aggregate `at` target。

## 4. Key Result Artifacts

- Project K summary / sweep / report: `examples/lt/results/project_k_workload_bottleneck/`
- Project L recommendations / report: `examples/lt/results/project_l_memory_architecture_recommendation/`
- Project AT-1 summary / report / traces: `examples/at/results/project_at1_four_phase_memory_timing/`
- Project AT-2 policy summary / report / traces: `examples/at/results/project_at2_multi_initiator_arbitration/`
- Project AT-3 policy sweep / recommendations / report / traces: `examples/at/results/project_at3_qos_sensitivity_sla/`
- Project AT-4 summary / policy sweep / recommendations / report / traces: `examples/at/results/project_at4_cache_mshr_pressure/`
- Generated portfolio evidence summary: `docs/generated/portfolio_evidence_summary.md`

## 5. Representative Questions This Pack Can Answer

- Which workload pattern creates memory bottlenecks?
- Which memory architecture action is supported by metrics?
- How does a four-phase AT transaction expose timing?
- How do arbitration policies affect fairness and p99 latency?
- How does weighted arbitration protect one initiator and hurt another?
- When does queue depth cause back-pressure?
- How do locality and hit/miss trend affect tail latency?
- When does MSHR-like outstanding miss pressure dominate?
- When does shared traffic interference or pollution proxy explain p95 / p99 growth?
- When does memory service latency dominate and make arbitration tuning insufficient?
- When do larger MSHR-like resources show diminishing return?
- Which architecture recommendation is supported by evidence?

## 6. Interview Usage

- Start with `docs/portfolio_architecture_story.md` for narrative.
- Use `docs/portfolio_evidence_pack.md` for reproducibility.
- Use `docs/generated/portfolio_evidence_summary.md` for metric snippets.
- Use `INTERVIEW_NOTES.md` for pitch.

## 7. Boundary Statement

Project P supports bounded portfolio and early architecture exploration discussion. It does not turn the repo into a production interconnect, protocol-complete model, or silicon correlation result.

- no AXI / CHI protocol compliance
- no cycle accuracy
- no real NoC model
- no cache coherence model
- no real L1/L2/L3 hierarchy model
- no real DRAM timing model
- no silicon validation
- no production signoff
- no real workload performance claim
