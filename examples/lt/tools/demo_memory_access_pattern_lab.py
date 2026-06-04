#!/usr/bin/env python3

import argparse
import csv
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROBOT = Path("examples/lt/lt.robot")
DEFAULT_OUTPUT_DIR = Path("examples/lt/results/memory_access_pattern_sweep")
SWEEP_RUNNER = Path("examples/lt/tools/run_memory_access_pattern_sweep.py")
DANGEROUS_CLEAN_PATHS = {
    REPO_ROOT.resolve(),
    (REPO_ROOT / "examples").resolve(),
    (REPO_ROOT / "examples" / "lt").resolve(),
    (REPO_ROOT / "examples" / "lt" / "results").resolve(),
}
EXPECTED_PATTERNS = ("sequential", "stride", "hotspot")
REQUIRED_METRIC_FIELDS = (
    "avg_latency_ns",
    "p50_latency_ns",
    "p95_latency_ns",
    "p99_latency_ns",
    "max_latency_ns",
    "bank_conflict_ratio_pct",
    "throughput_txn_per_us",
)
REQUIRED_SUMMARY_FIELDS = ("pattern", "status") + REQUIRED_METRIC_FIELDS


class DemoError(Exception):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Phase 16A memory access pattern MVP demo."
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
            "Demo output directory. Defaults to "
            "examples/lt/results/memory_access_pattern_sweep."
        ),
    )
    parser.add_argument(
        "--renode-test-cmd",
        default="renode-test",
        help="Command used to run Robot tests. Defaults to renode-test.",
    )
    return parser.parse_args()


def repo_path(path):
    return path if path.is_absolute() else REPO_ROOT / path


def display_path(path):
    path = Path(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def remove_path(path):
    if not path.exists():
        return
    if path.is_dir():
        resolved = path.resolve()
        if resolved in DANGEROUS_CLEAN_PATHS:
            raise DemoError(f"refusing to remove broad output directory: {path}")
        shutil.rmtree(path)
    else:
        path.unlink()


def run_command(command):
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise DemoError(
            f"failed to run command: {shlex.join(command)}\n"
            f"{error.__class__.__name__}: {error}"
        ) from error

    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        message = [
            f"command failed with exit code {result.returncode}:",
            shlex.join(command),
        ]
        if result.stderr:
            message.extend(("", "stderr:", result.stderr.strip()))
        raise DemoError("\n".join(message))

    return result


def read_summary(summary_path):
    if not summary_path.exists():
        raise DemoError(f"summary.csv not found: {display_path(summary_path)}")

    with summary_path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing = [
            field
            for field in REQUIRED_SUMMARY_FIELDS
            if field not in (reader.fieldnames or [])
        ]
        if missing:
            raise DemoError(
                "summary.csv missing required fields: " + ", ".join(missing)
            )
        rows = list(reader)

    by_pattern = {row.get("pattern"): row for row in rows}
    missing_patterns = [
        pattern for pattern in EXPECTED_PATTERNS if pattern not in by_pattern
    ]
    if missing_patterns:
        raise DemoError(
            "summary.csv missing MVP patterns: " + ", ".join(missing_patterns)
        )

    rows = [by_pattern[pattern] for pattern in EXPECTED_PATTERNS]

    failed = [row for row in rows if row.get("status") != "OK"]
    if failed:
        details = "; ".join(
            f"{row.get('pattern')}: {row.get('error') or row.get('status')}"
            for row in failed
        )
        raise DemoError(f"MVP sweep has failed cases: {details}")

    for row in rows:
        for field in REQUIRED_METRIC_FIELDS:
            if row.get(field) in (None, ""):
                raise DemoError(
                    f"summary.csv field {field} is empty for {row.get('pattern')}"
                )
            try:
                float(row[field])
            except (TypeError, ValueError):
                raise DemoError(
                    f"summary.csv field {field} is not numeric for "
                    f"{row.get('pattern')}"
                )

    return rows


def metric(row, field):
    try:
        return float(row.get(field, ""))
    except (TypeError, ValueError):
        return None


def format_metric(value, suffix=""):
    if value is None:
        return "NA"
    return f"{value:.3f}{suffix}"


def print_conclusions(rows):
    by_pattern = {row.get("pattern"): row for row in rows}
    baseline = by_pattern["sequential"]

    print("[demo] Phase 16A MVP conclusions")
    for pattern in ("sequential", "stride", "hotspot"):
        row = by_pattern[pattern]
        print(
            "  - "
            f"{pattern}: avg_latency={format_metric(metric(row, 'avg_latency_ns'), ' ns')}, "
            f"p99_latency={format_metric(metric(row, 'p99_latency_ns'), ' ns')}, "
            f"bank_conflict={format_metric(metric(row, 'bank_conflict_ratio_pct'), '%')}, "
            f"throughput={format_metric(metric(row, 'throughput_txn_per_us'), ' txn/us')}"
        )

    baseline_bank = metric(baseline, "bank_conflict_ratio_pct")
    for pattern in ("stride", "hotspot"):
        row = by_pattern[pattern]
        bank = metric(row, "bank_conflict_ratio_pct")
        delta = None if bank is None or baseline_bank is None else bank - baseline_bank
        print(
            "  - "
            f"{pattern} bank conflict delta vs sequential: "
            f"{format_metric(delta, ' pct')}"
        )


def main():
    args = parse_args()
    output_dir = repo_path(args.output_dir)
    remove_path(output_dir)

    command = [
        sys.executable,
        str(repo_path(SWEEP_RUNNER)),
        "--robot",
        str(repo_path(args.robot)),
        "--output-dir",
        str(output_dir),
        "--renode-test-cmd",
        args.renode_test_cmd,
        "--keep-going",
    ]
    run_command(command)

    trace_path = output_dir / "trace.csv"
    summary_path = output_dir / "summary.csv"
    comparison_path = output_dir / "comparison.md"
    for path in (trace_path, summary_path, comparison_path):
        if not path.exists():
            raise DemoError(f"expected output missing: {display_path(path)}")

    rows = read_summary(summary_path)

    print("[demo] outputs")
    print(f"  - trace: {display_path(trace_path)}")
    print(f"  - summary: {display_path(summary_path)}")
    print(f"  - comparison: {display_path(comparison_path)}")
    print_conclusions(rows)
    print("[demo] Phase 16A Memory Access Pattern MVP PASS")
    print(
        "[demo] scope: architecture-level SystemC/TLM memory access pattern lab; "
        "not a cycle-accurate or protocol-compliance model."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DemoError as error:
        print(f"[demo] ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
