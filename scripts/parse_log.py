#!/usr/bin/env python3
"""Extract SyzMini manager status counters into a traceable CSV file."""

import argparse
import csv
import re
from pathlib import Path

STATUS = re.compile(
    r"^(?P<date>\d{4}/\d{2}/\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"VMs\s+(?P<vms>\d+),\s+executed\s+(?P<executed>\d+),\s+"
    r"cover\s+(?P<cover>\d+),\s+signal\s+(?P<signal_current>\d+)/(?P<signal_total>\d+),\s+"
    r"crashes\s+(?P<crashes>\d+),\s+repro\s+(?P<repro>\d+),\s+"
    r"triageQLen\s+(?P<triage_queue>\d+)"
)
FIELDS = ["timestamp", "vms", "executed", "cover", "signal_current", "signal_total", "crashes", "repro", "triage_queue"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="manager.log from one run")
    parser.add_argument("-o", "--output", type=Path, help="CSV output; default is next to the log")
    args = parser.parse_args()
    if not args.log.is_file():
        parser.error(f"log file does not exist: {args.log}")
    output = args.output or args.log.with_name("metrics.csv")
    rows = []
    for line in args.log.read_text(encoding="utf-8", errors="replace").splitlines():
        match = STATUS.search(line)
        if not match:
            continue
        row = match.groupdict()
        rows.append({"timestamp": f"{row.pop('date')} {row.pop('time')}", **{k: int(v) for k, v in row.items()}})
    if not rows:
        raise SystemExit("No manager status lines found; check that this is the correct log format.")
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Parsed {len(rows)} status samples -> {output}")
    print(f"Last sample: executed={rows[-1]['executed']}, cover={rows[-1]['cover']}, crashes={rows[-1]['crashes']}")


if __name__ == "__main__":
    main()
