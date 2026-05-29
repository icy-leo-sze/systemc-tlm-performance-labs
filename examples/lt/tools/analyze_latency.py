#!/usr/bin/env python3

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path


DEFAULT_TRACE = Path(__file__).resolve().parents[1] / "results" / "latency_trace.csv"

REQUIRED_FIELDS = (
    "initiator_id",
    "target_id",
    "command",
    "address",
    "data",
    "start_time_ns",
    "delay_ns",
    "end_time_ns",
    "decoded_port",
    "masked_address",
    "data_length",
    "response_status",
)

FLOAT_FIELDS = ("start_time_ns", "delay_ns", "end_time_ns")
INT_FIELDS = ("data_length", "decoded_port")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate an architecture-oriented latency report for examples/lt."
    )
    parser.add_argument(
        "--trace",
        default=DEFAULT_TRACE,
        type=Path,
        help=f"CSV trace path. Defaults to {DEFAULT_TRACE}",
    )
    return parser.parse_args()


def parse_hex(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return int(text, 16)
    except ValueError:
        return None


def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def load_rows(trace_path):
    if not trace_path.exists():
        print(f"error: CSV trace not found: {trace_path}", file=sys.stderr)
        print(
            "hint: run `renode-test examples/lt/lt.robot` first.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    with trace_path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        missing_fields = [field for field in REQUIRED_FIELDS if field not in fieldnames]
        if missing_fields:
            print(
                "error: CSV trace is missing required fields: "
                + ", ".join(missing_fields),
                file=sys.stderr,
            )
            raise SystemExit(1)

        rows = []
        for row_number, row in enumerate(reader, start=2):
            row["_row_number"] = row_number

            for field in FLOAT_FIELDS:
                row[field] = parse_float(row.get(field))

            for field in INT_FIELDS:
                row[field] = parse_int(row.get(field))

            rows.append(row)

    return rows


def format_number(value):
    if value is None:
        return "NA"
    return f"{value:.3f}"


def format_hex(value):
    if value is None:
        return "NA"
    return f"0x{value:016X}"


def summarize_numeric(rows, group_keys):
    groups = defaultdict(list)
    for row in rows:
        delay = row.get("delay_ns")
        if delay is None:
            continue

        key = tuple(row.get(group_key, "") for group_key in group_keys)
        groups[key].append(delay)

    summary_rows = []
    for key, values in sorted(groups.items(), key=lambda item: tuple(str(v) for v in item[0])):
        summary_rows.append(
            list(key)
            + [
                len(values),
                format_number(sum(values) / len(values)),
                format_number(min(values)),
                format_number(max(values)),
            ]
        )

    return summary_rows


def print_table(title, headers, rows):
    print(f"\n== {title} ==")
    if not rows:
        print("(none)")
        return

    string_rows = [[str(value) for value in row] for row in rows]
    widths = [
        max(len(str(header)), *(len(row[index]) for row in string_rows))
        for index, header in enumerate(headers)
    ]

    header_line = "  ".join(str(header).ljust(widths[index]) for index, header in enumerate(headers))
    divider = "  ".join("-" * width for width in widths)
    print(header_line)
    print(divider)

    for row in string_rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def print_overview(rows):
    starts = [row["start_time_ns"] for row in rows if row["start_time_ns"] is not None]
    ends = [row["end_time_ns"] for row in rows if row["end_time_ns"] is not None]
    delays = [row["delay_ns"] for row in rows if row["delay_ns"] is not None]

    first_start = min(starts) if starts else None
    last_end = max(ends) if ends else None
    observed_time = last_end - first_start if first_start is not None and last_end is not None else None
    avg_delay = sum(delays) / len(delays) if delays else None

    print_table(
        "Overview",
        ("metric", "value"),
        (
            ("total_transactions", len(rows)),
            ("first_start_time_ns", format_number(first_start)),
            ("last_end_time_ns", format_number(last_end)),
            ("total_observed_time_ns", format_number(observed_time)),
            ("avg_delay_ns", format_number(avg_delay)),
            ("min_delay_ns", format_number(min(delays) if delays else None)),
            ("max_delay_ns", format_number(max(delays) if delays else None)),
        ),
    )


def count_by(rows, field):
    counts = defaultdict(int)
    for row in rows:
        counts[row.get(field, "")] += 1
    return [[key, count] for key, count in sorted(counts.items(), key=lambda item: str(item[0]))]


def print_address_range_summary(rows):
    groups = defaultdict(list)
    for row in rows:
        address = parse_hex(row.get("address"))
        if address is None:
            continue
        groups[row.get("target_id", "")].append(address)

    table_rows = []
    for target_id, addresses in sorted(groups.items(), key=lambda item: str(item[0])):
        table_rows.append(
            [
                target_id,
                format_hex(min(addresses)),
                format_hex(max(addresses)),
                len(addresses),
            ]
        )

    print_table(
        "Address Range Summary By target_id",
        ("target_id", "min_address", "max_address", "count"),
        table_rows,
    )


def print_data_length_summary(rows):
    print_table(
        "Data Length Summary",
        ("data_length", "count"),
        count_by(rows, "data_length"),
    )


def sanity_row(row):
    return [
        row.get("_row_number", ""),
        row.get("initiator_id", ""),
        row.get("target_id", ""),
        row.get("command", ""),
        row.get("address", ""),
        row.get("data_length", ""),
        format_number(row.get("start_time_ns")),
        format_number(row.get("end_time_ns")),
        format_number(row.get("delay_ns")),
        row.get("response_status", ""),
    ]


def print_sanity_block(title, rows):
    print_table(
        title,
        (
            "csv_row",
            "initiator_id",
            "target_id",
            "command",
            "address",
            "data_length",
            "start_time_ns",
            "end_time_ns",
            "delay_ns",
            "response_status",
        ),
        [sanity_row(row) for row in rows[:20]],
    )
    if len(rows) > 20:
        print(f"... {len(rows) - 20} more rows omitted")


def print_sanity_checks(rows):
    checks = (
        (
            "Sanity: response_status != TLM_OK_RESPONSE",
            [row for row in rows if row.get("response_status") != "TLM_OK_RESPONSE"],
        ),
        (
            "Sanity: data_length != 4",
            [row for row in rows if row.get("data_length") != 4],
        ),
        (
            "Sanity: end_time_ns < start_time_ns",
            [
                row
                for row in rows
                if row.get("end_time_ns") is not None
                and row.get("start_time_ns") is not None
                and row["end_time_ns"] < row["start_time_ns"]
            ],
        ),
        (
            "Sanity: delay_ns < 0",
            [row for row in rows if row.get("delay_ns") is not None and row["delay_ns"] < 0],
        ),
    )

    for title, failing_rows in checks:
        if failing_rows:
            print_sanity_block(title, failing_rows)
        else:
            print_table(title, ("status",), (("OK",),))


def timeline_row(row):
    return [
        format_number(row.get("start_time_ns")),
        format_number(row.get("end_time_ns")),
        row.get("initiator_id", ""),
        row.get("target_id", ""),
        row.get("command", ""),
        row.get("address", ""),
        row.get("masked_address", ""),
        row.get("data", ""),
        format_number(row.get("delay_ns")),
        row.get("response_status", ""),
    ]


def print_timeline(rows, title):
    print_table(
        title,
        (
            "start_time_ns",
            "end_time_ns",
            "initiator_id",
            "target_id",
            "command",
            "address",
            "masked_address",
            "data",
            "delay_ns",
            "response_status",
        ),
        [timeline_row(row) for row in rows],
    )


def timeline_sort_key(row):
    start = row.get("start_time_ns")
    end = row.get("end_time_ns")
    return (
        start if start is not None else float("inf"),
        end if end is not None else float("inf"),
        row.get("_row_number", 0),
    )


def main():
    args = parse_args()
    rows = load_rows(args.trace)
    sorted_rows = sorted(rows, key=timeline_sort_key)

    print(f"Trace: {args.trace}")
    print_overview(rows)
    print_table(
        "By initiator_id",
        ("initiator_id", "count", "avg_delay_ns", "min_delay_ns", "max_delay_ns"),
        summarize_numeric(rows, ("initiator_id",)),
    )
    print_table(
        "By target_id, command",
        ("target_id", "command", "count", "avg_delay_ns", "min_delay_ns", "max_delay_ns"),
        summarize_numeric(rows, ("target_id", "command")),
    )
    print_table(
        "By initiator_id, target_id, command",
        (
            "initiator_id",
            "target_id",
            "command",
            "count",
            "avg_delay_ns",
            "min_delay_ns",
            "max_delay_ns",
        ),
        summarize_numeric(rows, ("initiator_id", "target_id", "command")),
    )
    print_table("By response_status", ("response_status", "count"), count_by(rows, "response_status"))
    print_table("By decoded_port", ("decoded_port", "count"), count_by(rows, "decoded_port"))
    print_address_range_summary(rows)
    print_data_length_summary(rows)
    print_sanity_checks(rows)
    print_timeline(sorted_rows[:10], "First 10 Timeline Rows")
    print_timeline(sorted_rows[-10:], "Last 10 Timeline Rows")


if __name__ == "__main__":
    main()
