#!/usr/bin/env python3
"""Summarize final counters from at least three run metrics CSV files."""

import argparse
import csv
import statistics
from pathlib import Path

METRICS = ("executed", "cover", "signal_current", "signal_total", "crashes", "repro")


def final_row(path: Path) -> dict[str, int]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise SystemExit(f"No data rows in {path}")
    return {metric: int(rows[-1][metric]) for metric in METRICS}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="+", type=Path, help="metrics.csv from separate runs")
    args = parser.parse_args()
    if len(args.csv) < 3:
        parser.error("at least three independent runs are required by the course replication criteria")
    results = [final_row(path) for path in args.csv]
    print(f"Runs: {len(results)}")
    print("Metric             mean             sample_stddev")
    for metric in METRICS:
        values = [row[metric] for row in results]
        print(f"{metric:16s} {statistics.mean(values):14.2f} {statistics.stdev(values):18.2f}")
    print("\nNote: compare runs only when duration, VM count, CPU/memory, kernel, workload and other settings are equivalent.")


if __name__ == "__main__":
    main()
