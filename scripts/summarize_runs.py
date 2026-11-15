#!/usr/bin/env python3
"""Summarize final counters from at least three run metrics CSV files.

Inputs must refer to distinct files from independent, equivalently configured runs.
Path checks cannot establish experimental independence; keep run metadata and logs.
"""

import argparse
import csv
import statistics
from pathlib import Path

METRICS = ("executed", "cover", "signal_current", "signal_total", "crashes", "repro")


def final_row(path: Path) -> dict[str, int]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        missing = set(METRICS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        last = None
        for line_number, row in enumerate(reader, start=2):
            last = {}
            for metric in METRICS:
                raw = row.get(metric)
                if raw is None or not raw.strip().isascii() or not raw.strip().isdecimal():
                    raise ValueError(
                        f"{path}:{line_number}: {metric} must be a non-negative integer; got {raw!r}"
                    )
                last[metric] = int(raw)
    if last is None:
        raise ValueError(f"No data rows in {path}")
    return last


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="+", type=Path, help="metrics.csv from separate runs")
    args = parser.parse_args()
    if len(args.csv) < 3:
        parser.error("at least three independent runs are required by the course replication criteria")
    try:
        paths = []
        for path in args.csv:
            if any(path.samefile(previous) for previous in paths):
                raise ValueError(f"Duplicate run input: {path}; provide separate independent runs")
            # Validate even the first input before accepting it.
            if not path.is_file():
                raise ValueError(f"Run CSV is not a file: {path}")
            paths.append(path)
        results = [final_row(path) for path in paths]
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))
    print(f"Runs: {len(results)}")
    print("Metric             mean             sample_stddev")
    for metric in METRICS:
        values = [row[metric] for row in results]
        print(f"{metric:16s} {statistics.mean(values):14.2f} {statistics.stdev(values):18.2f}")
    print("\nNote: compare runs only when duration, VM count, CPU/memory, kernel, workload and other settings are equivalent.")


if __name__ == "__main__":
    main()

