#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence


SCHEMA_VERSION = "p0.1"


@dataclass(frozen=True)
class ProjectCheck:
    name: str
    command: List[str]
    pass_markers: List[str]
    project_labels: List[str]


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
        help="Skip Project AT-1/AT-2/AT-3 validation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print validation commands without running demos or checking PASS markers.",
    )
    return parser.parse_args()


def format_command(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def build_checks(args: argparse.Namespace) -> List[ProjectCheck]:
    python = sys.executable
    checks: List[ProjectCheck] = []

    if not args.skip_at:
        checks.extend(
            [
                ProjectCheck(
                    name="Project AT-1",
                    project_labels=["AT-1"],
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


def run_check(root: Path, check: ProjectCheck) -> bool:
    print(f"[project-p] START {check.name}")
    result = subprocess.run(
        check.command,
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

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
