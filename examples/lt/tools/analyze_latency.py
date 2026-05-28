#!/usr/bin/env python3
import csv
from collections import defaultdict
from pathlib import Path

TRACE = Path("examples/lt/results/latency_trace.csv")

def main():
    rows = []
    with TRACE.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["delay_ns"] = float(r["delay_ns"])
            r["start_time_ns"] = float(r["start_time_ns"])
            r["end_time_ns"] = float(r["end_time_ns"])
            rows.append(r)

    print("== total ==")
    print(len(rows))

    def group_by(keys):
        cnt = defaultdict(int)
        total = defaultdict(float)
        for r in rows:
            k = tuple(r[x] for x in keys)
            cnt[k] += 1
            total[k] += r["delay_ns"]
        for k in sorted(cnt):
            print(",".join(k), "count=", cnt[k], "avg_delay_ns=", total[k] / cnt[k])

    print("\n== by initiator ==")
    group_by(["initiator_id"])

    print("\n== by target,command ==")
    group_by(["target_id", "command"])

    print("\n== by initiator,target,command ==")
    group_by(["initiator_id", "target_id", "command"])

    print("\n== first 10 timeline rows ==")
    for r in rows[:10]:
        print(
            r["start_time_ns"],
            r["initiator_id"],
            "->",
            r["target_id"],
            r["command"],
            r["address"],
            "delay=",
            r["delay_ns"],
            "end=",
            r["end_time_ns"],
        )

if __name__ == "__main__":
    main()
