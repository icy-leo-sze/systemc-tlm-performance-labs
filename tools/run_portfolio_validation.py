#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import argparse
import csv
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


SCHEMA_VERSION = "p0.1"


@dataclass(frozen=True)
class CsvOutputCheck:
    path: Path
    min_rows: int
    claim_boundary: str
    schema_version: str


@dataclass(frozen=True)
class TextOutputCheck:
    path: Path
    required_fragments: Tuple[str, ...]
    case_sensitive: bool = False


@dataclass(frozen=True)
class ProjectCheck:
    name: str
    command: List[str]
    pass_markers: List[str]
    project_labels: List[str]
    build_command: Optional[List[str]] = None
    csv_outputs: Tuple[CsvOutputCheck, ...] = ()
    text_outputs: Tuple[TextOutputCheck, ...] = ()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Project P portfolio evidence validation harness."
    )
    parser.add_argument(
        "--at-build-dir",
        default="build-at",
        help="Existing AT CMake build directory. The harness does not configure or build it.",
    )
    parser.add_argument(
        "--skip-lt",
        action="store_true",
        help="Skip Project K/L LT validation.",
    )
    parser.add_argument(
        "--skip-at",
        action="store_true",
        help="Skip Project AT-1/AT-2/AT-3/AT-4 validation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print validation commands without running demos or checking PASS markers.",
    )
    return parser.parse_args()


def format_command(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def cmake_build_command(build_dir: str, target: str) -> List[str]:
    return ["cmake", "--build", build_dir, "--target", target, "-j"]


def build_checks(args: argparse.Namespace) -> List[ProjectCheck]:
    python = sys.executable
    checks: List[ProjectCheck] = []

    if not args.skip_at:
        checks.extend(
            [
                ProjectCheck(
                    name="Project AT-1",
                    project_labels=["AT-1"],
                    build_command=cmake_build_command(
                        args.at_build_dir,
                        "project_at1_four_phase_memory_timing",
                    ),
                    command=[
                        python,
                        "examples/at/tools/demo_project_at1_four_phase_memory_timing.py",
                        "--build-dir",
                        args.at_build_dir,
                        "--no-build",
                    ],
                    pass_markers=[
                        "Project AT-1 Four-Phase AT Memory Transaction Timing Lab PASS",
                    ],
                ),
                ProjectCheck(
                    name="Project AT-2",
                    project_labels=["AT-2"],
                    build_command=cmake_build_command(
                        args.at_build_dir,
                        "project_at2_multi_initiator_arbitration",
                    ),
                    command=[
                        python,
                        "examples/at/tools/demo_project_at2_multi_initiator_arbitration.py",
                        "--build-dir",
                        args.at_build_dir,
                        "--no-build",
                    ],
                    pass_markers=[
                        "Project AT-2 Multi-Initiator AT Arbitration and Contention Lab PASS",
                    ],
                ),
                ProjectCheck(
                    name="Project AT-3",
                    project_labels=["AT-3"],
                    build_command=cmake_build_command(
                        args.at_build_dir,
                        "project_at3_qos_sensitivity_sla",
                    ),
                    command=[
                        python,
                        "examples/at/tools/demo_project_at3_qos_sensitivity_sla.py",
                        "--build-dir",
                        args.at_build_dir,
                        "--no-build",
                    ],
                    pass_markers=[
                        "Project AT-3 QoS Sensitivity and SLA Violation Lab PASS",
                    ],
                ),
                ProjectCheck(
                    name="Project AT-4",
                    project_labels=["AT-4"],
                    build_command=cmake_build_command(
                        args.at_build_dir,
                        "project_at4_cache_mshr_pressure",
                    ),
                    command=[
                        python,
                        "examples/at/tools/demo_at4_cache_mshr_pressure.py",
                        "--at-build-dir",
                        args.at_build_dir,
                    ],
                    pass_markers=[
                        "Project AT-4 Cache-like Shared Resource and MSHR Pressure Lab PASS",
                        "cases=7",
                        "initiators=3",
                        "claim_boundary=PASS",
                        "schema_version=at4.0",
                    ],
                    csv_outputs=(
                        CsvOutputCheck(
                            path=Path(
                                "examples/at/results/"
                                "project_at4_cache_mshr_pressure/"
                                "project_at4_summary.csv"
                            ),
                            min_rows=21,
                            claim_boundary="PASS",
                            schema_version="at4.0",
                        ),
                        CsvOutputCheck(
                            path=Path(
                                "examples/at/results/"
                                "project_at4_cache_mshr_pressure/"
                                "project_at4_policy_sweep.csv"
                            ),
                            min_rows=7,
                            claim_boundary="PASS",
                            schema_version="at4.0",
                        ),
                        CsvOutputCheck(
                            path=Path(
                                "examples/at/results/"
                                "project_at4_cache_mshr_pressure/"
                                "project_at4_recommendations.csv"
                            ),
                            min_rows=7,
                            claim_boundary="PASS",
                            schema_version="at4.0",
                        ),
                    ),
                    text_outputs=(
                        TextOutputCheck(
                            path=Path(
                                "examples/at/results/"
                                "project_at4_cache_mshr_pressure/"
                                "project_at4_report.md"
                            ),
                            required_fragments=(
                                "Claim boundary",
                                "MSHR",
                                "interference",
                                "diminishing",
                            ),
                        ),
                    ),
                ),
            ]
        )

    if not args.skip_lt:
        checks.append(
            ProjectCheck(
                name="Project K/L",
                project_labels=["K", "L"],
                command=[
                    python,
                    "examples/lt/tools/demo_project_k_workload_bottleneck_lab.py",
                    "--no-build",
                ],
                pass_markers=[
                    "Project K Workload-Aware Memory Bottleneck Characterization MVP PASS",
                    "Project L Evidence-Driven Memory Architecture Recommendation Lab PASS",
                ],
            )
        )

    return checks


def print_failure_output(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout:
        print("[stdout]")
        print(result.stdout.rstrip())
    if result.stderr:
        print("[stderr]")
        print(result.stderr.rstrip())


def run_command(
    root: Path, command: Sequence[str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def validate_csv_output(root: Path, check: CsvOutputCheck) -> List[str]:
    full_path = root / check.path
    errors: List[str] = []

    if not full_path.exists():
        return [f"missing file: {check.path}"]

    with full_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]

    if len(rows) < check.min_rows:
        errors.append(
            f"{check.path}: expected at least {check.min_rows} data rows, "
            f"found {len(rows)}"
        )

    for column, expected in (
        ("claim_boundary", check.claim_boundary),
        ("schema_version", check.schema_version),
    ):
        bad_values = sorted(
            {
                row.get(column, "")
                for row in rows
                if row.get(column, "") != expected
            }
        )
        if bad_values:
            errors.append(
                f"{check.path}: column {column} expected {expected}, "
                f"found {bad_values}"
            )

    return errors


def validate_text_output(root: Path, check: TextOutputCheck) -> List[str]:
    full_path = root / check.path
    if not full_path.exists():
        return [f"missing file: {check.path}"]

    text = full_path.read_text(encoding="utf-8")
    haystack = text if check.case_sensitive else text.lower()
    missing = []
    for fragment in check.required_fragments:
        needle = fragment if check.case_sensitive else fragment.lower()
        if needle not in haystack:
            missing.append(fragment)

    if missing:
        return [f"{check.path}: missing text fragment(s): {', '.join(missing)}"]
    return []


def validate_outputs(root: Path, check: ProjectCheck) -> List[str]:
    errors: List[str] = []
    for csv_output in check.csv_outputs:
        errors.extend(validate_csv_output(root, csv_output))
    for text_output in check.text_outputs:
        errors.extend(validate_text_output(root, text_output))
    return errors


def run_check(root: Path, check: ProjectCheck) -> bool:
    print(f"[project-p] START {check.name}")
    if check.build_command is not None:
        print(f"[project-p] BUILD {check.name}: {format_command(check.build_command)}")
        build_result = run_command(root, check.build_command)
        if build_result.returncode != 0:
            print(f"[project-p] FAIL {check.name}: build returncode={build_result.returncode}")
            print_failure_output(build_result)
            return False

    result = run_command(root, check.command)

    combined_output = result.stdout + result.stderr
    missing_markers = [
        marker for marker in check.pass_markers if marker not in combined_output
    ]

    if result.returncode != 0:
        print(f"[project-p] FAIL {check.name}: returncode={result.returncode}")
        print_failure_output(result)
        return False

    if missing_markers:
        print(f"[project-p] FAIL {check.name}: missing PASS marker(s)")
        for marker in missing_markers:
            print(f"  missing: {marker}")
        print_failure_output(result)
        return False

    output_errors = validate_outputs(root, check)
    if output_errors:
        print(f"[project-p] FAIL {check.name}: output validation failed")
        for error in output_errors:
            print(f"  {error}")
        print_failure_output(result)
        return False

    print(f"[project-p] PASS {check.name}")
    return True


def main() -> int:
    args = parse_args()
    root = repo_root()
    checks = build_checks(args)

    if not checks:
        print("[project-p] No projects selected. Use default options or remove skip flags.")
        return 2

    if args.dry_run:
        for check in checks:
            if check.build_command is not None:
                print(
                    f"[project-p] DRY-RUN {check.name}: "
                    f"{format_command(check.build_command)}"
                )
            print(f"[project-p] DRY-RUN {check.name}: {format_command(check.command)}")
        print("Portfolio Evidence Pack DRY-RUN")
        print("schema_version=p0.1")
        return 0

    passed_labels: List[str] = []
    for check in checks:
        if not run_check(root, check):
            print("Portfolio Evidence Pack FAIL")
            print(f"failed_project={check.name}")
            print(f"schema_version={SCHEMA_VERSION}")
            return 1
        passed_labels.extend(check.project_labels)

    print("Portfolio Evidence Pack PASS")
    print(f"projects={','.join(passed_labels)}")
    print("claim_boundary=PASS")
    print(f"schema_version={SCHEMA_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
