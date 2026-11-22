#!/usr/bin/env python3
"""Extract SyzMini manager status counters into a traceable CSV file."""

import argparse
import csv
import re
import os
import tempfile
from pathlib import Path

STATUS = re.compile(
    r"^(?P<date>\d{4}/\d{2}/\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"VMs\s+(?P<vms>\d+),\s+executed\s+(?P<executed>\d+),\s+"
    r"cover\s+(?P<cover>\d+),\s+signal\s+(?P<signal_current>\d+)/(?P<signal_total>\d+),\s+"
    r"crashes\s+(?P<crashes>\d+),\s+repro\s+(?P<repro>\d+),\s+"
    r"triageQLen\s+(?P<triage_queue>\d+)"
)
FIELDS = ["source_line", "timestamp", "vms", "executed", "cover", "signal_current", "signal_total", "crashes", "repro", "triage_queue"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="manager.log from one run")
    parser.add_argument("-o", "--output", type=Path, help="CSV output; default is next to the log")
    args = parser.parse_args()
    if not args.log.is_file():
        parser.error(f"log file does not exist: {args.log}")
    output = args.output or args.log.with_name("metrics.csv")
    # resolve() catches relative paths/symlinks; samefile() also catches hard links.
    if output.resolve() == args.log.resolve() or (
        output.exists() and output.samefile(args.log)
    ):
        parser.error("output must not refer to the input log")
    temporary = None
    count = 0
    last = None
    try:
        # Write beside the destination, then atomically replace only after success.
        # An empty/unrecognized log must not destroy an existing metrics CSV.
        with args.log.open(encoding="utf-8", errors="replace") as source:
            with tempfile.NamedTemporaryFile(
                mode="w", newline="", encoding="utf-8",
                dir=output.parent, prefix=f".{output.name}.", suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                for line_number, line in enumerate(source, start=1):
                    match = STATUS.search(line)
                    if not match:
                        continue
                    row = match.groupdict()
                    last = {
                        "source_line": line_number,
                        "timestamp": f"{row.pop('date')} {row.pop('time')}",
                        **{k: int(v) for k, v in row.items()},
                    }
                    writer.writerow(last)
                    count += 1
        if not count:
            parser.error("No manager status lines found; check that this is the correct log format.")
        os.replace(temporary, output)
    except OSError as error:
        parser.error(str(error))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Parsed {count} status samples -> {output}")
    print(f"Last sample: executed={last['executed']}, cover={last['cover']}, crashes={last['crashes']}")



if __name__ == "__main__":
    main()
