#!/usr/bin/env python3

import argparse
import csv
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROBOT = Path("examples/lt/lt.robot")
DEFAULT_OUTPUT_DIR = Path("examples/lt/results/sweep")
DEFAULT_TRACE = Path("examples/lt/results/latency_trace.csv")
DEFAULT_WORKLOAD_CONFIG = Path("examples/lt/results/workload_config.env")
ANALYZER = Path("examples/lt/tools/analyze_latency.py")

SUMMARY_FIELDS = (
    "case_name",
    "status",
    "burst_count",
    "address_stride",
    "enable_initiator_101",
    "enable_initiator_102",
    "target_pattern",
    "total_transactions",
    "avg_delay_ns",
    "max_delay_ns",
    "avg_queue_delay_ns",
    "max_queue_delay_ns",
    "contention_ratio_pct",
    "avg_target_service_delay_ns",
    "total_bank_conflicts",
    "bank_conflict_ratio_pct",
    "avg_bank_conflict_delay_ns",
    "max_bank_conflict_delay_ns",
    "error",
)

METRIC_FIELDS = (
    "total_transactions",
    "avg_delay_ns",
    "max_delay_ns",
    "avg_queue_delay_ns",
    "max_queue_delay_ns",
    "contention_ratio_pct",
    "avg_target_service_delay_ns",
    "total_bank_conflicts",
    "bank_conflict_ratio_pct",
    "avg_bank_conflict_delay_ns",
    "max_bank_conflict_delay_ns",
)

BASELINE_CASE = "baseline_dual_initiator_current_default"

COMPARISON_CASES = (
    "single_initiator_101_current_default",
    "dual_initiator_target201_hotspot",
    "dual_initiator_target202_hotspot",
    "dual_initiator_stride_16_current_default",
)

BASELINE_REPORT_METRICS = (
    "total_transactions",
    "avg_delay_ns",
    "max_delay_ns",
    "avg_queue_delay_ns",
    "contention_ratio_pct",
    "bank_conflict_ratio_pct",
    "avg_bank_conflict_delay_ns",
)

CASE_COMPARISON_METRICS = (
    "avg_delay_ns",
    "max_delay_ns",
    "avg_queue_delay_ns",
    "contention_ratio_pct",
    "bank_conflict_ratio_pct",
    "avg_bank_conflict_delay_ns",
)

NS_METRICS = {
    "avg_delay_ns",
    "max_delay_ns",
    "avg_queue_delay_ns",
    "max_queue_delay_ns",
    "avg_target_service_delay_ns",
    "avg_bank_conflict_delay_ns",
    "max_bank_conflict_delay_ns",
}

PCT_METRICS = {
    "contention_ratio_pct",
    "bank_conflict_ratio_pct",
}

CASE_INTERPRETATIONS = {
    "single_initiator_101_current_default": (
        "Disabling initiator 102 removes shared-target contention from the "
        "SystemC workload, so queue delay should drop."
    ),
    "dual_initiator_target201_hotspot": (
        "Concentrating traffic on the slower target 201 raises average "
        "latency and target service cost."
    ),
    "dual_initiator_target202_hotspot": (
        "Concentrating traffic on the faster target 202 keeps average latency "
        "lower than the target 201 hotspot."
    ),
    "dual_initiator_stride_16_current_default": (
        "Stride 16 maps accesses to the same bank more often, raising bank "
        "conflict ratio and increasing avg_delay_ns."
    ),
}

CASES = (
    {
        "case_name": "baseline_dual_initiator_current_default",
        "burst_count": 64,
        "address_stride": 4,
        "enable_initiator_101": 1,
        "enable_initiator_102": 1,
        "target_pattern": "both",
    },
    {
        "case_name": "single_initiator_101_current_default",
        "burst_count": 64,
        "address_stride": 4,
        "enable_initiator_101": 1,
        "enable_initiator_102": 0,
        "target_pattern": "both",
    },
    {
        "case_name": "dual_initiator_target201_hotspot",
        "burst_count": 64,
        "address_stride": 4,
        "enable_initiator_101": 1,
        "enable_initiator_102": 1,
        "target_pattern": "target201",
    },
    {
        "case_name": "dual_initiator_target202_hotspot",
        "burst_count": 64,
        "address_stride": 4,
        "enable_initiator_101": 1,
        "enable_initiator_102": 1,
        "target_pattern": "target202",
    },
    {
        "case_name": "dual_initiator_stride_16_current_default",
        "burst_count": 64,
        "address_stride": 16,
        "enable_initiator_101": 1,
        "enable_initiator_102": 1,
        "target_pattern": "both",
    },
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the examples/lt workload sweep and collect latency summaries."
    )
    parser.add_argument(
        "--renode-test-cmd",
        default="renode-test",
        help="Command used to run Robot tests. Defaults to renode-test.",
    )
    parser.add_argument(
        "--robot",
        default=DEFAULT_ROBOT,
        type=Path,
        help="Robot test path. Defaults to examples/lt/lt.robot.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        type=Path,
        help="Sweep output directory. Defaults to examples/lt/results/sweep.",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue running remaining cases after a failure.",
    )
    return parser.parse_args()


def repo_path(path):
    return path if path.is_absolute() else REPO_ROOT / path


def write_text(path, text):
    path.write_text(text or "", encoding="utf-8")


def run_command(command, env, stdout_path, stderr_path):
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        write_text(stdout_path, "")
        write_text(
            stderr_path,
            f"failed to run command: {shlex.join(command)}\n"
            f"{error.__class__.__name__}: {error}\n",
        )
        return getattr(error, "errno", None) or 127

    write_text(stdout_path, result.stdout)
    write_text(stderr_path, result.stderr)
    return result.returncode


def read_summary_metrics(path):
    if not path.exists():
        raise ValueError(f"summary metrics not found: {path}")

    try:
        with path.open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
    except OSError as error:
        raise ValueError(f"failed to read summary metrics: {error}") from error

    if not rows:
        raise ValueError(f"summary metrics is empty: {path}")

    metrics = rows[0]
    missing_fields = [field for field in METRIC_FIELDS if field not in metrics]
    if missing_fields:
        raise ValueError(
            "summary metrics is missing fields: " + ", ".join(missing_fields)
        )

    empty_fields = [
        field
        for field in METRIC_FIELDS
        if metrics.get(field) is None or metrics.get(field) == ""
    ]
    if empty_fields:
        raise ValueError(
            "summary metrics has empty fields: " + ", ".join(empty_fields)
        )

    return {field: metrics[field] for field in METRIC_FIELDS}


def write_sweep_summary(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def markdown_cell(value):
    return str(value).replace("\n", " ").replace("|", "\\|")


def markdown_table(headers, rows):
    lines = [
        "| " + " | ".join(markdown_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(markdown_cell(value) for value in row) + " |")
    return lines


def metric_float(row, field):
    try:
        return float(row.get(field, ""))
    except (TypeError, ValueError):
        return None


def format_metric_value(row, field):
    value = row.get(field, "")
    if value in (None, ""):
        return "N/A"

    if field == "total_transactions":
        try:
            return str(int(float(value)))
        except (TypeError, ValueError):
            return str(value)

    if field in NS_METRICS or field in PCT_METRICS:
        number = metric_float(row, field)
        return "N/A" if number is None else f"{number:.3f}"

    return str(value)


def format_delta(value):
    return "N/A" if value is None else f"{value:+.3f}"


def comparison_rows(baseline, case):
    rows = []
    for metric in CASE_COMPARISON_METRICS:
        baseline_value = metric_float(baseline, metric)
        case_value = metric_float(case, metric)
        delta = None
        delta_pct = None
        if baseline_value is not None and case_value is not None:
            delta = case_value - baseline_value
            if baseline_value != 0:
                delta_pct = (delta / baseline_value) * 100

        rows.append(
            (
                metric,
                format_metric_value(baseline, metric),
                format_metric_value(case, metric),
                format_delta(delta),
                format_delta(delta_pct),
            )
        )
    return rows


def row_passed(row):
    return row is not None and row.get("status") == "PASS"


def write_comparison_report(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows_by_case = {row.get("case_name"): row for row in rows}
    baseline = rows_by_case.get(BASELINE_CASE)

    lines = [
        "# LT Workload Sweep Comparison",
        "",
        "Generated from `summary.csv` by `run_workload_sweep.py`.",
        "",
        "## Baseline",
        "",
    ]

    if not row_passed(baseline):
        lines.append(
            "Baseline case is missing or failed; comparison is unavailable."
        )
        if baseline and baseline.get("error"):
            lines.extend(("", f"Error: `{baseline['error']}`"))
        lines.append("")
        write_text(path, "\n".join(lines))
        return

    lines.extend(
        markdown_table(
            ("metric", "value"),
            (
                (metric, format_metric_value(baseline, metric))
                for metric in BASELINE_REPORT_METRICS
            ),
        )
    )
    lines.extend(("", "## Case Comparison", ""))

    for case_name in COMPARISON_CASES:
        case = rows_by_case.get(case_name)
        lines.extend((f"### `{case_name}`", ""))
        if case is None:
            lines.extend(("Case is missing from `summary.csv`.", ""))
            continue
        if case.get("status") != "PASS":
            lines.append("Case failed; comparison is unavailable.")
            if case.get("error"):
                lines.append(f"Error: `{case['error']}`")
            lines.append("")
            continue

        lines.extend(
            markdown_table(
                ("metric", "baseline", "case", "delta", "delta_pct"),
                comparison_rows(baseline, case),
            )
        )
        lines.append("")

    lines.extend(("## Interpretation", ""))
    for case_name in COMPARISON_CASES:
        case = rows_by_case.get(case_name)
        if not row_passed(case):
            lines.append(
                f"- `{case_name}`: case failed or is missing; interpretation "
                "is unavailable."
            )
            continue
        lines.append(f"- `{case_name}`: {CASE_INTERPRETATIONS[case_name]}")

    lines.append("")
    write_text(path, "\n".join(lines))


def case_environment(case):
    env = os.environ.copy()
    env.update(
        {
            "LT_BURST_COUNT": str(case["burst_count"]),
            "LT_ADDRESS_STRIDE": str(case["address_stride"]),
            "LT_ENABLE_INITIATOR_101": str(case["enable_initiator_101"]),
            "LT_ENABLE_INITIATOR_102": str(case["enable_initiator_102"]),
            "LT_TARGET_PATTERN": case["target_pattern"],
        }
    )
    return env


def workload_config_text(case):
    return "\n".join(
        (
            "# Generated by examples/lt/tools/run_workload_sweep.py",
            f"LT_BURST_COUNT={case['burst_count']}",
            f"LT_ADDRESS_STRIDE={case['address_stride']}",
            f"LT_ENABLE_INITIATOR_101={case['enable_initiator_101']}",
            f"LT_ENABLE_INITIATOR_102={case['enable_initiator_102']}",
            f"LT_TARGET_PATTERN={case['target_pattern']}",
            "",
        )
    )


def write_workload_config(case, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path, workload_config_text(case))


def remove_workload_config(path):
    try:
        path.unlink(missing_ok=True)
    except OSError as error:
        return str(error)
    return ""


def empty_metrics():
    return {field: "" for field in METRIC_FIELDS}


def base_summary_row(case):
    row = {
        "case_name": case["case_name"],
        "status": "PASS",
        "burst_count": case["burst_count"],
        "address_stride": case["address_stride"],
        "enable_initiator_101": case["enable_initiator_101"],
        "enable_initiator_102": case["enable_initiator_102"],
        "target_pattern": case["target_pattern"],
        "error": "",
    }
    row.update(empty_metrics())
    return row


def parse_hex(value):
    try:
        return int(str(value), 16)
    except (TypeError, ValueError):
        return None


def trace_rows(trace_path):
    with trace_path.open(newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def expected_trace_target_pattern(case):
    if case["target_pattern"] == "target201":
        return "target201_only"
    if case["target_pattern"] == "target202":
        return "target202_only"
    return "current_default"


def validate_stride(systemc_rows, stride):
    if stride <= 0:
        return ["address_stride must be > 0"]

    errors = []
    groups = {}
    for row in systemc_rows:
        address = parse_hex(row.get("address"))
        if address is None:
            errors.append(f"invalid address {row.get('address')}")
            continue

        key = (row.get("initiator_id"), row.get("target_id"), row.get("command"))
        groups.setdefault(key, set()).add(address)

    for key, addresses in sorted(groups.items()):
        sorted_addresses = sorted(addresses)
        if len(sorted_addresses) < 2:
            continue

        deltas = [
            right - left
            for left, right in zip(sorted_addresses, sorted_addresses[1:])
        ]
        bad_deltas = [delta for delta in deltas if delta != stride]
        if bad_deltas:
            errors.append(
                "address_stride mismatch for "
                f"initiator={key[0]} target={key[1]} command={key[2]}: "
                f"expected {stride}, saw {bad_deltas[0]}"
            )

    return errors


def validate_workload_fields(systemc_rows, case):
    expected = {
        "workload_transaction_count": str(case["burst_count"]),
        "workload_address_stride": str(case["address_stride"]),
        "workload_target_pattern": expected_trace_target_pattern(case),
        "workload_enable_initiator_101": str(case["enable_initiator_101"]),
        "workload_enable_initiator_102": str(case["enable_initiator_102"]),
    }

    errors = []
    for field, expected_value in expected.items():
        observed_values = {
            row.get(field)
            for row in systemc_rows
            if row.get(field) not in (None, "")
        }
        if not observed_values:
            errors.append(f"trace missing {field}")
        elif observed_values != {expected_value}:
            errors.append(
                f"{field} expected {expected_value}, saw "
                + "/".join(sorted(observed_values))
            )

    return errors


def validate_case_trace(case, trace_path):
    rows = trace_rows(trace_path)
    systemc_rows = [
        row for row in rows if row.get("initiator_id") in {"101", "102"}
    ]
    errors = []

    if (case["enable_initiator_101"] or case["enable_initiator_102"]) and not systemc_rows:
        errors.append("trace has no SystemC traffic_generator rows")

    for initiator_id in ("101", "102"):
        enabled = case[f"enable_initiator_{initiator_id}"]
        if not enabled and any(row.get("initiator_id") == initiator_id for row in systemc_rows):
            errors.append(f"disabled initiator {initiator_id} appears in trace")

    if case["target_pattern"] == "target201":
        unexpected_targets = sorted(
            {row.get("target_id") for row in systemc_rows if row.get("target_id") != "201"}
        )
        if unexpected_targets:
            errors.append(
                "target201 case contains SystemC target_id "
                + "/".join(unexpected_targets)
            )
    elif case["target_pattern"] == "target202":
        unexpected_targets = sorted(
            {row.get("target_id") for row in systemc_rows if row.get("target_id") != "202"}
        )
        if unexpected_targets:
            errors.append(
                "target202 case contains SystemC target_id "
                + "/".join(unexpected_targets)
            )

    errors.extend(validate_stride(systemc_rows, int(case["address_stride"])))
    errors.extend(validate_workload_fields(systemc_rows, case))
    return errors


def run_case(case, args, output_dir, trace_path, workload_config_path):
    case_dir = output_dir / case["case_name"]
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)

    if trace_path.exists():
        trace_path.unlink()
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    row = base_summary_row(case)
    env = case_environment(case)
    case_config_path = case_dir / "workload_config.env"
    try:
        write_workload_config(case, case_config_path)
        write_workload_config(case, workload_config_path)
    except OSError as error:
        row["status"] = "FAIL"
        row["error"] = f"failed to write workload config: {error}"
        return row

    renode_command = shlex.split(args.renode_test_cmd) + [str(repo_path(args.robot))]
    try:
        renode_status = run_command(
            renode_command,
            env,
            case_dir / "renode-test.stdout.txt",
            case_dir / "renode-test.stderr.txt",
        )
    finally:
        cleanup_error = remove_workload_config(workload_config_path)

    if cleanup_error:
        row["status"] = "FAIL"
        row["error"] = f"failed to remove workload config: {cleanup_error}"
        return row

    if renode_status != 0:
        row["status"] = "FAIL"
        row["error"] = f"renode-test exited with {renode_status}"
        return row

    case_trace = case_dir / "latency_trace.csv"
    if not trace_path.exists():
        row["status"] = "FAIL"
        row["error"] = f"trace not found: {trace_path}"
        return row

    shutil.copy2(trace_path, case_trace)

    summary_metrics_path = case_dir / "summary_metrics.csv"
    analyze_command = [
        sys.executable,
        str(repo_path(ANALYZER)),
        "--trace",
        str(case_trace),
        "--initiator",
        "101",
        "--initiator",
        "102",
        "--dedup-identical",
        "--fail-on-sanity",
        "--summary-csv-output",
        str(summary_metrics_path),
    ]
    analyze_status = run_command(
        analyze_command,
        env,
        case_dir / "analysis.txt",
        case_dir / "analysis.stderr.txt",
    )
    if analyze_status != 0:
        row["status"] = "FAIL"
        row["error"] = f"analyze_latency.py exited with {analyze_status}"
        return row

    try:
        row.update(read_summary_metrics(summary_metrics_path))
    except ValueError as error:
        row["status"] = "FAIL"
        row["error"] = str(error)

    validation_errors = validate_case_trace(case, case_trace)
    if validation_errors:
        row["status"] = "FAIL"
        row["error"] = "; ".join(validation_errors[:4])

    return row


def main():
    args = parse_args()
    output_dir = repo_path(args.output_dir)
    trace_path = repo_path(DEFAULT_TRACE)
    workload_config_path = repo_path(DEFAULT_WORKLOAD_CONFIG)
    summary_path = output_dir / "summary.csv"
    comparison_path = output_dir / "comparison.md"

    output_dir.mkdir(parents=True, exist_ok=True)
    remove_workload_config(workload_config_path)

    rows = []
    failed = False
    for case in CASES:
        print(f"[sweep] running {case['case_name']}")
        row = run_case(case, args, output_dir, trace_path, workload_config_path)
        rows.append(row)
        write_sweep_summary(summary_path, rows)

        if row["status"] != "PASS":
            failed = True
            print(f"[sweep] {case['case_name']} failed: {row['error']}", file=sys.stderr)
            if not args.keep_going:
                break

    try:
        write_comparison_report(rows, comparison_path)
    except OSError as error:
        failed = True
        print(f"[sweep] failed to write {comparison_path}: {error}", file=sys.stderr)

    print(f"[sweep] wrote {summary_path}")
    print(f"[sweep] wrote {comparison_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
