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
DEFAULT_OUTPUT_DIR = Path("examples/lt/results/memory_access_pattern_sweep")
DEFAULT_TRACE = Path("examples/lt/results/latency_trace.csv")
DEFAULT_WORKLOAD_CONFIG = Path("examples/lt/results/workload_config.env")
PATTERN_ORDER = ("sequential", "stride", "hotspot")

SUMMARY_FIELDS = (
    "case_id",
    "status",
    "pattern",
    "stride",
    "num_transactions",
    "hotspot_ratio",
    "trace_csv",
    "total_transactions",
    "avg_latency_ns",
    "p50_latency_ns",
    "p95_latency_ns",
    "p99_latency_ns",
    "max_latency_ns",
    "bank_conflict_ratio_pct",
    "throughput_txn_per_us",
    "avg_queue_delay_ns",
    "max_queue_delay_ns",
    "avg_target_service_delay_ns",
    "total_bank_conflicts",
    "error",
)

REQUIRED_MVP_SUMMARY_FIELDS = (
    "pattern",
    "stride",
    "num_transactions",
    "avg_latency_ns",
    "p50_latency_ns",
    "p95_latency_ns",
    "p99_latency_ns",
    "max_latency_ns",
    "bank_conflict_ratio_pct",
    "throughput_txn_per_us",
)

METRIC_FIELDS = (
    "total_transactions",
    "avg_latency_ns",
    "p50_latency_ns",
    "p95_latency_ns",
    "p99_latency_ns",
    "max_latency_ns",
    "bank_conflict_ratio_pct",
    "throughput_txn_per_us",
    "avg_queue_delay_ns",
    "max_queue_delay_ns",
    "avg_target_service_delay_ns",
    "total_bank_conflicts",
)

REQUIRED_TRACE_FIELDS = (
    "start_time_ns",
    "end_time_ns",
    "bank_conflict",
)

CASES = (
    {
        "case_id": "sequential",
        "pattern": "sequential",
        "stride": 4,
        "num_transactions": 64,
        "hotspot_ratio": 0.0,
    },
    {
        "case_id": "stride",
        "pattern": "stride",
        "stride": 16,
        "num_transactions": 64,
        "hotspot_ratio": 0.0,
    },
    {
        "case_id": "hotspot",
        "pattern": "hotspot",
        "stride": 4,
        "num_transactions": 64,
        "hotspot_ratio": 0.8,
    },
)

PATTERN_DESCRIPTIONS = {
    "sequential": (
        "Contiguous word accesses with `stride=4`; the locality-friendly "
        "baseline for the MVP."
    ),
    "stride": (
        "Fixed larger-step accesses with `stride=16`; this intentionally maps "
        "back to the same minimal bank more often."
    ),
    "hotspot": (
        "A concentrated access stream where most transactions target one base "
        "address, controlled by `LT_HOTSPOT_RATIO=0.8`."
    ),
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Phase 16A memory access pattern MVP sweep."
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
        help=(
            "Sweep output directory. Defaults to "
            "examples/lt/results/memory_access_pattern_sweep."
        ),
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue running remaining cases after a failure.",
    )
    return parser.parse_args()


def validate_case_definitions():
    patterns = tuple(case["pattern"] for case in CASES)
    if patterns != PATTERN_ORDER:
        raise ValueError(
            "Phase 16A MVP must run exactly these patterns in order: "
            + ", ".join(PATTERN_ORDER)
        )

    missing_summary_fields = [
        field for field in REQUIRED_MVP_SUMMARY_FIELDS if field not in SUMMARY_FIELDS
    ]
    if missing_summary_fields:
        raise ValueError(
            "summary.csv is missing required MVP fields: "
            + ", ".join(missing_summary_fields)
        )

    for case in CASES:
        if case["num_transactions"] <= 0:
            raise ValueError(f"{case['case_id']} has no transactions")
        if case["stride"] <= 0:
            raise ValueError(f"{case['case_id']} has invalid stride")
        if not 0.0 <= case["hotspot_ratio"] <= 1.0:
            raise ValueError(f"{case['case_id']} has invalid hotspot_ratio")


def repo_path(path):
    return path if path.is_absolute() else REPO_ROOT / path


def display_path(path):
    path = Path(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
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


def workload_config_text(case):
    return "\n".join(
        (
            "# Generated by examples/lt/tools/run_memory_access_pattern_sweep.py",
            f"LT_BURST_COUNT={case['num_transactions']}",
            f"LT_ADDRESS_STRIDE={case['stride']}",
            "LT_ENABLE_INITIATOR_101=1",
            "LT_ENABLE_INITIATOR_102=0",
            "LT_TARGET_PATTERN=target201",
            f"LT_MEMORY_PATTERN={case['pattern']}",
            f"LT_HOTSPOT_RATIO={case['hotspot_ratio']}",
            "",
        )
    )


def write_workload_config(case, path):
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
        "case_id": case["case_id"],
        "status": "OK",
        "pattern": case["pattern"],
        "stride": case["stride"],
        "num_transactions": case["num_transactions"],
        "hotspot_ratio": case["hotspot_ratio"],
        "trace_csv": "",
        "error": "",
    }
    row.update(empty_metrics())
    return row


def parse_hex(value):
    try:
        return int(str(value), 16)
    except (TypeError, ValueError):
        return None


def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_number(value):
    if value is None:
        return ""
    return f"{value:.3f}"


def average(values):
    return sum(values) / len(values) if values else None


def percentile(values, percentile_value):
    if not values:
        return None

    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]

    rank = int(round((percentile_value / 100.0) * (len(sorted_values) - 1)))
    rank = max(0, min(rank, len(sorted_values) - 1))
    return sorted_values[rank]


def latency_value(row):
    latency = parse_float(row.get("total_delay_ns"))
    if latency is not None:
        return latency
    return parse_float(row.get("delay_ns"))


def read_trace_rows(trace_path):
    with trace_path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        missing = [field for field in REQUIRED_TRACE_FIELDS if field not in fieldnames]
        if missing:
            raise ValueError("trace missing fields: " + ", ".join(missing))
        if "total_delay_ns" not in fieldnames and "delay_ns" not in fieldnames:
            raise ValueError("trace missing latency field: total_delay_ns or delay_ns")
        return list(reader), fieldnames


def rows_for_initiator(rows, initiator_id):
    return [row for row in rows if row.get("initiator_id") == str(initiator_id)]


def validate_address_stride(rows, expected_stride):
    errors = []
    for command in ("WRITE", "READ"):
        command_rows = [row for row in rows if row.get("command") == command]
        parsed_addresses = [parse_hex(row.get("address")) for row in command_rows]
        addresses = sorted(
            {address for address in parsed_addresses if address is not None}
        )
        if any(address is None for address in parsed_addresses):
            errors.append(f"{command} contains invalid address")
            continue
        if len(addresses) < 2:
            continue
        deltas = [right - left for left, right in zip(addresses, addresses[1:])]
        bad = [delta for delta in deltas if delta != expected_stride]
        if bad:
            errors.append(
                f"{command} address stride expected {expected_stride}, saw {bad[0]}"
            )
    return errors


def validate_hotspot(rows, expected_ratio):
    hotspot_values = [row.get("is_hotspot_access") for row in rows]
    if not hotspot_values:
        return ["hotspot trace has no rows"]

    hotspot_count = sum(1 for value in hotspot_values if value == "1")
    observed_ratio = hotspot_count / len(hotspot_values)
    if abs(observed_ratio - expected_ratio) > 0.10:
        return [
            "hotspot ratio expected "
            f"{expected_ratio:.3f}, saw {observed_ratio:.3f}"
        ]

    non_hotspot_zero_addresses = [
        row
        for row in rows
        if row.get("is_hotspot_access") != "1" and parse_hex(row.get("address")) == 0
    ]
    if non_hotspot_zero_addresses:
        return ["non-hotspot rows include the hotspot base address"]

    return []


def is_true_field(value):
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def numeric_values(rows, field):
    values = []
    for row in rows:
        value = parse_float(row.get(field))
        if value is not None:
            values.append(value)
    return values


def compute_summary_metrics(case, trace_path):
    rows, fieldnames = read_trace_rows(trace_path)
    if "initiator_id" in fieldnames:
        rows = rows_for_initiator(rows, 101)

    if not rows:
        raise ValueError("trace has no transactions")

    latencies = []
    invalid_latency_rows = 0
    for row in rows:
        latency = latency_value(row)
        if latency is None:
            invalid_latency_rows += 1
            continue
        latencies.append(latency)

    if invalid_latency_rows:
        raise ValueError(
            f"trace has {invalid_latency_rows} rows without total_delay_ns or delay_ns"
        )

    starts = numeric_values(rows, "start_time_ns")
    ends = numeric_values(rows, "end_time_ns")
    if len(starts) != len(rows) or len(ends) != len(rows):
        raise ValueError("trace has non-numeric start_time_ns or end_time_ns")

    transaction_count = len(rows)
    observed_window_ns = max(ends) - min(starts)
    throughput = 0.0
    if observed_window_ns > 0.0:
        throughput = transaction_count / (observed_window_ns / 1000.0)

    bank_conflict_count = sum(
        1 for row in rows if is_true_field(row.get("bank_conflict"))
    )
    bank_conflict_ratio = 100.0 * bank_conflict_count / transaction_count

    queue_delays = numeric_values(rows, "queue_delay_ns")
    service_delays = numeric_values(rows, "target_service_delay_ns")

    return {
        "num_transactions": transaction_count,
        "total_transactions": transaction_count,
        "avg_latency_ns": format_number(average(latencies)),
        "p50_latency_ns": format_number(percentile(latencies, 50)),
        "p95_latency_ns": format_number(percentile(latencies, 95)),
        "p99_latency_ns": format_number(percentile(latencies, 99)),
        "max_latency_ns": format_number(max(latencies)),
        "bank_conflict_ratio_pct": format_number(bank_conflict_ratio),
        "throughput_txn_per_us": format_number(throughput),
        "avg_queue_delay_ns": format_number(average(queue_delays)),
        "max_queue_delay_ns": format_number(max(queue_delays) if queue_delays else None),
        "avg_target_service_delay_ns": format_number(average(service_delays)),
        "total_bank_conflicts": bank_conflict_count,
    }


def validate_case_trace(case, trace_path):
    trace_rows, fieldnames = read_trace_rows(trace_path)
    rows = rows_for_initiator(trace_rows, 101) if "initiator_id" in fieldnames else trace_rows
    errors = []

    if not rows:
        errors.append("trace has no transactions")

    if "case_id" in fieldnames:
        observed_case_ids = {
            row.get("case_id") for row in trace_rows if row.get("case_id") not in (None, "")
        }
        if observed_case_ids and observed_case_ids != {case["case_id"]}:
            errors.append(f"case_id expected {case['case_id']}, saw {sorted(observed_case_ids)}")

    if "initiator_id" in fieldnames and any(row.get("initiator_id") == "102" for row in trace_rows):
        errors.append("MVP sweep should not emit initiator 102 rows")

    expected_values = {
        "workload_transaction_count": str(case["num_transactions"]),
        "workload_address_stride": str(case["stride"]),
        "workload_memory_pattern": case["pattern"],
    }
    for field, expected in expected_values.items():
        if field not in fieldnames:
            continue
        observed = {row.get(field) for row in rows if row.get(field) not in (None, "")}
        if observed and observed != {expected}:
            errors.append(f"{field} expected {expected}, saw {sorted(observed)}")

    if "workload_hotspot_ratio" in fieldnames:
        ratios = {
            parse_float(row.get("workload_hotspot_ratio"))
            for row in rows
            if row.get("workload_hotspot_ratio") not in (None, "")
        }
        if ratios and (
            len(ratios) != 1
            or abs(next(iter(ratios)) - case["hotspot_ratio"]) > 0.001
        ):
            errors.append(f"workload_hotspot_ratio expected {case['hotspot_ratio']}")

    if (
        case["pattern"] in {"sequential", "stride"}
        and "address" in fieldnames
        and "command" in fieldnames
    ):
        errors.extend(validate_address_stride(rows, case["stride"]))
    if "is_hotspot_access" in fieldnames:
        if case["pattern"] in {"sequential", "stride"}:
            if any(is_true_field(row.get("is_hotspot_access")) for row in rows):
                errors.append(f"{case['pattern']} should not mark hotspot accesses")
        elif case["pattern"] == "hotspot":
            errors.extend(validate_hotspot(rows, case["hotspot_ratio"]))

    return errors


def write_summary_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def metric_float(row, field):
    try:
        return float(row.get(field, ""))
    except (TypeError, ValueError):
        return None


def delta_text(case, baseline, field, unit):
    case_value = metric_float(case, field)
    baseline_value = metric_float(baseline, field)
    if case_value is None or baseline_value is None:
        return "NA"
    return f"{case_value - baseline_value:+.3f} {unit}"


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


def row_passed(row):
    return row is not None and row.get("status") == "OK"


def write_comparison_report(rows, path):
    by_pattern = {row.get("pattern"): row for row in rows}
    baseline = by_pattern.get("sequential")
    ordered_rows = [
        by_pattern[pattern] for pattern in PATTERN_ORDER if pattern in by_pattern
    ]
    lines = [
        "# Phase 16A Memory Access Pattern MVP Comparison",
        "",
        "Generated from `summary.csv` by `run_memory_access_pattern_sweep.py`.",
        "",
        "This is an architecture-level SystemC/TLM memory access pattern lab. It "
        "compares exactly three access patterns, `sequential`, `stride`, and "
        "`hotspot`, through the existing LT trace -> metrics -> sweep -> "
        "comparison chain.",
        "",
        "The model is intentionally small: it is not cycle accurate, and it "
        "does not claim AXI, CHI, NoC, cache, or DRAM protocol compliance.",
        "",
        "## Workload Cases",
        "",
    ]

    lines.extend(
        markdown_table(
            ("pattern", "stride", "num_transactions", "hotspot_ratio", "intent"),
            (
                (
                    case["pattern"],
                    case["stride"],
                    case["num_transactions"],
                    case["hotspot_ratio"],
                    PATTERN_DESCRIPTIONS[case["pattern"]],
                )
                for case in CASES
            ),
        )
    )

    lines.extend(("", "## Summary Metrics", ""))
    lines.extend(
        markdown_table(
            REQUIRED_MVP_SUMMARY_FIELDS,
            (
                tuple(row.get(field, "") for field in REQUIRED_MVP_SUMMARY_FIELDS)
                for row in ordered_rows
            ),
        )
    )

    lines.extend(("", "## Delta vs Sequential", ""))
    if not row_passed(baseline):
        lines.append("Sequential baseline is missing or failed; deltas are unavailable.")
    else:
        delta_rows = []
        for pattern in PATTERN_ORDER:
            row = by_pattern.get(pattern)
            if pattern == "sequential" and row_passed(row):
                delta_rows.append(
                    (
                        "sequential",
                        "baseline",
                        "baseline",
                        "baseline",
                        "baseline",
                        "baseline",
                        "baseline",
                    )
                )
                continue

            if not row_passed(row):
                error = row.get("error", "missing") if row else "missing"
                delta_rows.append(
                    (pattern, "FAIL", "FAIL", "FAIL", "FAIL", "FAIL", error)
                )
                continue

            delta_rows.append(
                (
                    pattern,
                    delta_text(row, baseline, "avg_latency_ns", "ns"),
                    delta_text(row, baseline, "p50_latency_ns", "ns"),
                    delta_text(row, baseline, "p95_latency_ns", "ns"),
                    delta_text(row, baseline, "p99_latency_ns", "ns"),
                    delta_text(row, baseline, "bank_conflict_ratio_pct", "pct"),
                    delta_text(row, baseline, "throughput_txn_per_us", "txn/us"),
                )
            )

        lines.extend(
            markdown_table(
                (
                    "pattern",
                    "avg_latency_delta",
                    "p50_latency_delta",
                    "p95_latency_delta",
                    "p99_latency_delta",
                    "bank_conflict_ratio_delta",
                    "throughput_delta",
                ),
                delta_rows,
            )
        )

    lines.extend(("", "## Interpretation", ""))
    lines.extend(
        (
            "- `sequential` is the locality-friendly baseline. Consecutive word "
            "accesses rotate through the minimal bank model, so it should be the "
            "cleanest reference point for both latency and bank conflict ratio.",
            "- `stride` keeps the same transaction count but increases the address "
            "step to 16 bytes. In this model that repeatedly aliases to the same "
            "bank, which should raise bank conflict ratio and push average and "
            "tail latency above the sequential baseline.",
            "- `hotspot` keeps a small stride for non-hotspot accesses but pins most "
            "transactions to one base address. That deliberately stresses repeated "
            "same-bank service and should expose higher bank conflict and tail "
            "latency than sequential access.",
            "- `throughput_txn_per_us` is computed over the observed trace window. "
            "Use it as an internal model comparison metric, not as a hardware "
            "bandwidth claim.",
        )
    )

    lines.extend(("", "## Sanity Checks", ""))
    for pattern in PATTERN_ORDER:
        row = by_pattern.get(pattern)
        if row is None:
            lines.append(f"- `{pattern}`: FAIL - missing from `summary.csv`")
        elif row.get("status") == "OK":
            lines.append(f"- `{pattern}`: OK")
        else:
            lines.append(f"- `{pattern}`: FAIL - {row.get('error')}")

    lines.append("")
    write_text(path, "\n".join(lines))


def write_combined_trace(case_trace_paths, path):
    fieldnames = ["case_id"]
    all_rows = []
    for case_id, trace_path in case_trace_paths:
        if not trace_path.exists():
            continue
        with trace_path.open(newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for field in reader.fieldnames or []:
                if field not in fieldnames:
                    fieldnames.append(field)
            for row in reader:
                row["case_id"] = case_id
                all_rows.append(row)

    if not all_rows:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    return True


def run_case(case, args, output_dir, trace_path, workload_config_path):
    case_dir = output_dir / case["case_id"]
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)

    if trace_path.exists():
        trace_path.unlink()
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    row = base_summary_row(case)
    env = os.environ.copy()
    env.update(
        {
            "LT_BURST_COUNT": str(case["num_transactions"]),
            "LT_ADDRESS_STRIDE": str(case["stride"]),
            "LT_ENABLE_INITIATOR_101": "1",
            "LT_ENABLE_INITIATOR_102": "0",
            "LT_TARGET_PATTERN": "target201",
            "LT_MEMORY_PATTERN": case["pattern"],
            "LT_HOTSPOT_RATIO": str(case["hotspot_ratio"]),
        }
    )

    try:
        write_workload_config(case, case_dir / "workload_config.env")
        write_workload_config(case, workload_config_path)
    except OSError as error:
        row["status"] = "FAIL"
        row["error"] = f"failed to write workload config: {error}"
        return row, None

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
        return row, None

    if renode_status != 0:
        row["status"] = "FAIL"
        row["error"] = f"renode-test exited with {renode_status}"
        return row, None

    if not trace_path.exists():
        row["status"] = "FAIL"
        row["error"] = f"trace not found: {trace_path}"
        return row, None

    case_trace = case_dir / "trace.csv"
    shutil.copy2(trace_path, case_trace)
    row["trace_csv"] = display_path(case_trace)

    try:
        row.update(compute_summary_metrics(case, case_trace))
        validation_errors = validate_case_trace(case, case_trace)
        if validation_errors:
            row["status"] = "FAIL"
            row["error"] = "; ".join(validation_errors[:4])
        else:
            write_text(
                case_dir / "analysis.txt",
                "\n".join(
                    (
                        f"pattern={case['pattern']}",
                        f"trace={display_path(case_trace)}",
                        f"num_transactions={row['num_transactions']}",
                        f"avg_latency_ns={row['avg_latency_ns']}",
                        f"p50_latency_ns={row['p50_latency_ns']}",
                        f"p95_latency_ns={row['p95_latency_ns']}",
                        f"p99_latency_ns={row['p99_latency_ns']}",
                        f"max_latency_ns={row['max_latency_ns']}",
                        f"bank_conflict_ratio_pct={row['bank_conflict_ratio_pct']}",
                        f"throughput_txn_per_us={row['throughput_txn_per_us']}",
                        "",
                    )
                ),
            )
    except (OSError, ValueError, csv.Error) as error:
        row["status"] = "FAIL"
        row["error"] = str(error)

    return row, case_trace


def main():
    args = parse_args()
    try:
        validate_case_definitions()
    except ValueError as error:
        print(f"[memory-sweep] configuration error: {error}", file=sys.stderr)
        return 1

    output_dir = repo_path(args.output_dir)
    trace_path = repo_path(DEFAULT_TRACE)
    workload_config_path = repo_path(DEFAULT_WORKLOAD_CONFIG)
    summary_path = output_dir / "summary.csv"
    comparison_path = output_dir / "comparison.md"
    combined_trace_path = output_dir / "trace.csv"

    output_dir.mkdir(parents=True, exist_ok=True)
    remove_workload_config(workload_config_path)

    rows = []
    case_trace_paths = []
    failed = False
    for case in CASES:
        print(f"[memory-sweep] running pattern={case['pattern']}")
        row, case_trace = run_case(case, args, output_dir, trace_path, workload_config_path)
        rows.append(row)
        if case_trace is not None:
            case_trace_paths.append((case["case_id"], case_trace))
        write_summary_csv(summary_path, rows)

        if row["status"] != "OK":
            failed = True
            print(
                f"[memory-sweep] pattern={case['pattern']} failed: {row['error']}",
                file=sys.stderr,
            )
            if not args.keep_going:
                break

    if not write_combined_trace(case_trace_paths, combined_trace_path):
        failed = True
        print("[memory-sweep] failed to write combined trace.csv", file=sys.stderr)

    write_comparison_report(rows, comparison_path)

    print(f"[memory-sweep] wrote {combined_trace_path}")
    print(f"[memory-sweep] wrote {summary_path}")
    print(f"[memory-sweep] wrote {comparison_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
