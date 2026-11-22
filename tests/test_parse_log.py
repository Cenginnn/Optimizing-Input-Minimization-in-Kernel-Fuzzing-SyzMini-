"""Regression tests with synthetic log lines; these are not fuzzing results.

Run from the repository root: python3 -m unittest discover -s tests -v
"""
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARSER = ROOT / "scripts" / "parse_log.py"
SUMMARY = ROOT / "scripts" / "summarize_runs.py"


def status(executed=10):
    return (
        f"2026/11/22 12:00:00 VMs 1, executed {executed}, cover 20, "
        "signal 3/4, crashes 0, repro 0, triageQLen 0\n"
    )


class ParseLogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / "manager.log"
        self.output = self.root / "metrics.csv"

    def run_parser(self, *options):
        return subprocess.run(
            [sys.executable, str(PARSER), str(self.log), *map(str, options)],
            capture_output=True, text=True,
        )

    def test_traceable_rows_and_final_counters(self):
        self.log.write_text("boot message\n" + status() + "noise\n" + status(30))
        result = self.run_parser()
        self.assertEqual(result.returncode, 0, result.stderr)
        with self.output.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([r["source_line"] for r in rows], ["2", "4"])
        self.assertEqual([r["executed"] for r in rows], ["10", "30"])
        self.assertEqual(rows[0]["timestamp"], "2026/11/22 12:00:00")
        self.assertIn("Parsed 2 status samples", result.stdout)
        self.assertIn("executed=30", result.stdout)

    def test_input_cannot_be_overwritten(self):
        content = status()
        self.log.write_text(content)
        result = self.run_parser("-o", self.log)
        self.assertEqual(result.returncode, 2)
        self.assertIn("input log", result.stderr)
        self.assertEqual(self.log.read_text(), content)

    def test_path_alias_cannot_overwrite_input(self):
        self.log.write_text(status())
        nested = self.root / "nested"
        nested.mkdir()
        result = self.run_parser("-o", nested / ".." / self.log.name)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.log.read_text(), status())

    def test_unrecognized_log_preserves_existing_csv(self):
        self.log.write_text("no status samples\n")
        self.output.write_text("existing results\n")
        result = self.run_parser()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.output.read_text(), "existing results\n")
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_empty_log_creates_no_csv(self):
        self.log.write_text("")
        self.assertNotEqual(self.run_parser().returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_custom_output_and_invalid_utf8_noise(self):
        self.log.write_bytes(b"noise: \\xff\n".replace(b"\\xff", bytes([255])) + status().encode())
        custom = self.root / "custom.csv"
        result = self.run_parser("-o", custom)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(custom.exists())
        self.assertFalse(self.output.exists())

    def test_missing_destination_directory(self):
        self.log.write_text(status())
        result = self.run_parser("-o", self.root / "missing" / "metrics.csv")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.log.read_text(), status())

    def test_summary_accepts_source_line_column(self):
        paths = []
        for index in range(3):
            self.log.write_text(status((index + 1) * 10))
            path = self.root / f"run{index}.csv"
            result = self.run_parser("-o", path)
            self.assertEqual(result.returncode, 0, result.stderr)
            paths.append(path)
        result = subprocess.run(
            [sys.executable, str(SUMMARY), *map(str, paths)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[2].split(),
                         ["executed", "20.00", "10.00"])


if __name__ == "__main__":
    unittest.main()
