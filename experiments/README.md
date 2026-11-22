# SyzMini experiment records

This directory stores experiment protocols and results. Do not commit VM disk images,
SSH private keys, generated workdirs, or huge raw traces.

## Question for this week's experiment

Does the influence-matrix-enabled SyzMini run complete fuzzing work and produce
measurable coverage/crash signals under a fixed Linux 5.15 + QEMU setup?

This is an operational validation, not yet proof that SyzMini outperforms upstream
Syzkaller. A performance claim requires a controlled baseline and repeated runs.

## Fixed settings to record

- Repository commit and local modifications.
- Host OS, WSL2/kernel version, CPU model/core count and available memory.
- Linux guest kernel version and `.config` relevant options (KCOV, KASAN, debug info,
  network drivers).
- Go, GCC, QEMU and SyzMini versions.
- Image identity/checksum, influence-matrix path/checksum and syscall target.
- Manager settings: `procs`, VM count, VM CPU, VM memory, command line, duration.
- Workload/corpus source and any deviations from the paper.

Copy `metadata-template.json` into each run directory as `metadata.json`, then fill in
all values. Never put private keys or credentials in metadata.

## Procedure

1. Copy `configs/v515.env.example` to `configs/v515.env` and adjust local paths.
2. Run `scripts/check_env.sh`; keep its output in the experiment notes.
3. Start one run with `RUN_ID=syzmini-r1 scripts/run_syzmini.sh`.
4. After stopping the run, parse its log:

   `python3 scripts/parse_log.py experiments/results/syzmini-r1/manager.log`

5. Repeat as independent runs (`syzmini-r2`, `syzmini-r3`) with the same settings.
6. Summarize final counters:

   `python3 scripts/summarize_runs.py experiments/results/syzmini-r1/metrics.csv experiments/results/syzmini-r2/metrics.csv experiments/results/syzmini-r3/metrics.csv`

7. Commit concise metadata, CSV summaries, plots and analysis. Keep raw logs only if they
   remain reasonably sized and contain no sensitive data.

## Interpretation rules

- `executed` is the number of executed test programs, not branch coverage.
- `cover` is a coverage counter reported by SyzMini; it is not automatically a percentage.
- `signal_current/signal_total` are signal counters; report both values and do not label
  them as a percentage unless the implementation's semantics have been verified.
- `crashes` is the manager's crash count. A crash is not automatically a confirmed,
  unique kernel bug; inspect crash reports and reproduce/triage them.
- `repro` counts reproduced crashes according to the manager's status output.
- Compare runs at the same elapsed time or same execution budget. Do not compare a
  one-hour run with a substantially longer run as if they were equivalent.

## Paper comparison

Create a separate Paper-vs-Ours table only after matching the paper's metric and setting.
If hardware, kernel, duration, corpus, VM count, or other conditions differ, list each
as a deviation and explain it. Do not claim a paper result was reproduced from a single
successful fuzzing session.

## Traceable log parsing and regression checks

The parser reads manager logs one line at a time, so long fuzzing sessions do not
require loading the entire log and CSV into memory. Each newly generated CSV row
includes `source_line`, the 1-based line number in the original `manager.log`.
Keep that log alongside the CSV without editing it after parsing; the line number
and timestamp together locate the source status sample. Existing CSVs are not
rewritten automatically, and `summarize_runs.py` accepts the additional column.

The output path must differ from the input log (including aliases). Output is
written to a temporary file beside the destination and replaced only after a
successful parse. If no status samples are found, an existing CSV is preserved.
The output directory must already exist.

Run parser regression checks from the repository root with Python 3.10 or newer:

```sh
python3 -m unittest discover -s tests -v
```

These tests use synthetic counters to check traceability, input preservation,
failed-parse preservation, custom output paths and compatibility with the
mean/sample-standard-deviation summary. They are software checks, not evidence
of kernel fuzzing performance or independent experiment runs.
