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
DEFAULT_OUTPUT_DIR = Path("examples/lt/results/sweep")
TRACE = Path("examples/lt/results/latency_trace.csv")
WORKLOAD_CONFIG = Path("examples/lt/results/workload_config.env")
ANALYSIS = Path("examples/lt/results/analysis.txt")
ANALYZER = Path("examples/lt/tools/analyze_latency.py")
SWEEP_RUNNER = Path("examples/lt/tools/run_workload_sweep.py")
DANGEROUS_CLEAN_PATHS = {
    REPO_ROOT.resolve(),
    (REPO_ROOT / "examples").resolve(),
    (REPO_ROOT / "examples" / "lt").resolve(),
    (REPO_ROOT / "examples" / "lt" / "results").resolve(),
}

BASELINE_CASE = "baseline_dual_initiator_current_default"
SINGLE_CASE = "single_initiator_101_current_default"
TARGET201_CASE = "dual_initiator_target201_hotspot"
TARGET202_CASE = "dual_initiator_target202_hotspot"
STRIDE16_CASE = "dual_initiator_stride_16_current_default"


class DemoError(Exception):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the one-command demo for examples/lt performance lab."
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
        help="Continue sweep cases after a failure.",
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


def run_command(command, *, stdout_path=None):
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

    if stdout_path is not None:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text(result.stdout or "", encoding="utf-8")

    if result.returncode != 0:
        message = [
            f"command failed with exit code {result.returncode}:",
            shlex.join(command),
        ]
        if result.stderr:
            message.extend(("", "stderr:", result.stderr.strip()))
        if result.stdout and stdout_path is None:
            message.extend(("", "stdout:", result.stdout.strip()))
        raise DemoError("\n".join(message))

    return result


def read_summary_rows(summary_path):
    if not summary_path.exists():
        raise DemoError(f"summary.csv not found: {display_path(summary_path)}")

    try:
        with summary_path.open(newline="") as csv_file:
            return list(csv.DictReader(csv_file))
    except (OSError, csv.Error) as error:
        raise DemoError(f"failed to read summary.csv: {error}") from error


def rows_by_case(rows):
    return {row.get("case_name", ""): row for row in rows}


def metric(row, field):
    if row is None:
        return None
    value = row.get(field)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def case_status(row):
    if row is None:
        return "missing"
    if row.get("status") != "PASS":
        error = row.get("error") or "no error detail"
        return f"status={row.get('status', 'UNKNOWN')} ({error})"
    return ""


def format_ns(value):
    return "missing" if value is None else f"{value:.3f} ns"


def format_pct(value):
    return "missing" if value is None else f"{value:.3f}%"


def format_delta(value, unit):
    if value is None:
        return "missing"
    return f"{value:+.3f} {unit}"


def print_metric_conclusions(summary_path):
    rows = rows_by_case(read_summary_rows(summary_path))
    baseline = rows.get(BASELINE_CASE)
    single = rows.get(SINGLE_CASE)
    target201 = rows.get(TARGET201_CASE)
    target202 = rows.get(TARGET202_CASE)
    stride16 = rows.get(STRIDE16_CASE)

    print("[demo] architecture conclusions")

    baseline_queue = metric(baseline, "avg_queue_delay_ns")
    single_queue = metric(single, "avg_queue_delay_ns")
    single_status = case_status(single) or case_status(baseline)
    if single_status:
        print(f"  - single initiator queue delay: unavailable ({single_status})")
    else:
        delta = None
        if baseline_queue is not None and single_queue is not None:
            delta = single_queue - baseline_queue
        print(
            "  - single initiator queue delay: "
            f"{format_ns(single_queue)} vs baseline {format_ns(baseline_queue)} "
            f"({format_delta(delta, 'ns')})"
        )

    target201_status = case_status(target201)
    target201_delay = metric(target201, "avg_delay_ns")
    if target201_status:
        print(f"  - target201 hotspot avg delay: unavailable ({target201_status})")
    else:
        print(f"  - target201 hotspot avg delay: {format_ns(target201_delay)}")

    target202_status = case_status(target202)
    target202_delay = metric(target202, "avg_delay_ns")
    if target202_status:
        print(f"  - target202 hotspot avg delay: unavailable ({target202_status})")
    else:
        print(f"  - target202 hotspot avg delay: {format_ns(target202_delay)}")

    baseline_bank = metric(baseline, "bank_conflict_ratio_pct")
    stride16_bank = metric(stride16, "bank_conflict_ratio_pct")
    stride_status = case_status(stride16) or case_status(baseline)
    if stride_status:
        print(f"  - stride16 bank conflict ratio: unavailable ({stride_status})")
    else:
        delta = None
        if baseline_bank is not None and stride16_bank is not None:
            delta = stride16_bank - baseline_bank
        print(
            "  - stride16 bank conflict ratio: "
            f"{format_pct(stride16_bank)} vs baseline {format_pct(baseline_bank)} "
            f"({format_delta(delta, 'pct points')})"
        )


def clean_outputs(output_dir):
    print("[demo] cleaning old outputs")
    for path in (repo_path(TRACE), repo_path(WORKLOAD_CONFIG), repo_path(ANALYSIS), output_dir):
        remove_path(path)
    repo_path(TRACE).parent.mkdir(parents=True, exist_ok=True)


def run_demo(args):
    robot = repo_path(args.robot)
    output_dir = repo_path(args.output_dir)
    trace = repo_path(TRACE)
    analysis = repo_path(ANALYSIS)
    summary = output_dir / "summary.csv"
    comparison = output_dir / "comparison.md"

    clean_outputs(output_dir)

    print("[demo] running renode-test")
    renode_command = shlex.split(args.renode_test_cmd) + [str(robot)]
    run_command(renode_command)

    if not trace.exists():
        raise DemoError(f"trace was not generated: {display_path(trace)}")

    print("[demo] running analyzer")
    analyze_command = [
        sys.executable,
        str(repo_path(ANALYZER)),
        "--trace",
        str(trace),
    ]
    run_command(analyze_command, stdout_path=analysis)

    print("[demo] running workload sweep")
    sweep_command = [
        sys.executable,
        str(repo_path(SWEEP_RUNNER)),
        "--robot",
        str(robot),
        "--output-dir",
        str(output_dir),
        "--renode-test-cmd",
        args.renode_test_cmd,
    ]
    if args.keep_going:
        sweep_command.append("--keep-going")
    run_command(sweep_command)

    print(f"[demo] wrote {display_path(trace)}")
    print(f"[demo] wrote {display_path(analysis)}")
    print(f"[demo] wrote {display_path(summary)}")
    print(f"[demo] wrote {display_path(comparison)}")

    print_metric_conclusions(summary)


def main():
    args = parse_args()
    try:
        run_demo(args)
    except DemoError as error:
        print(f"[demo] ERROR: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"[demo] ERROR: {error.__class__.__name__}: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("[demo] interrupted", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
