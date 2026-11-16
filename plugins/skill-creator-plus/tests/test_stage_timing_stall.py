"""Tests for host-stall detection in stage timing (scripts/stage_timing.py).

Run: python3 -m unittest discover -s plugins/skill-creator-plus/tests -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from test_stage_timing_transcript import bash, call, prompt, result, st, write_jsonl  # noqa: E402


def run_lines(gap, start=0):
    """A run: stage a (10s tool), an idle gap of `gap` seconds, stage b (10s tool), handback."""
    t = start + 12
    return [prompt(start), call(start + 2, bash("t1", "# stage: a\nls")), result(t, "t1"),
            call(t + gap, bash("t2", "# stage: b\nmake")), result(t + gap + 10, "t2"),
            call(t + gap + 12, text="done")]


def make(root, shapes):
    it = Path(root) / "iteration-1"
    runs = []
    for n, lines in shapes.items():
        run_dir = it / "case" / "with_skill" / f"run-{n}"
        write_jsonl(str(run_dir / "transcript.jsonl"), lines)
        runs.append(("with_skill", f"case/with_skill/run-{n}", run_dir))
    return it, runs


class HostStallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def build(self, shapes):
        it, runs = make(self.tmp, shapes)
        agg = st.build_stage_timing(it, runs)
        per_run = [json.loads((r[2] / "stage_timing.json").read_text()) for r in runs]
        return agg, per_run

    def test_overlapping_gap_is_booked_to_host_stall_in_both_runs(self):
        agg, per_run = self.build({1: run_lines(800), 2: run_lines(800, 3)})
        for run in per_run:
            self.assertAlmostEqual(run["host_stall_seconds"], 800, delta=1)
            rows = {s["name"]: s for s in run["stages"]}
            self.assertLess(rows["a"]["duration_seconds"], 20)
            self.assertLess(rows["b"]["duration_seconds"], 20)
            self.assertEqual(len(run["stalls"]), 1)
            self.assertEqual(run["stalls"][0]["shared_with_runs"], 1)
            st.check_reconciliation(run)
        cfg = agg["configurations"]["with_skill"]
        self.assertAlmostEqual(cfg["host_stall_seconds"]["mean"], 800, delta=1)
        table = st.markdown_table(agg)
        self.assertIn("| host stall |", table)
        self.assertIn("outside the skill", table)
        svg = st.render_waterfall_svg(agg)
        self.assertIn("host stall (outside skill)", svg)

    def test_single_run_gap_stays_in_stage_and_is_flagged(self):
        agg, per_run = self.build({1: run_lines(800), 2: run_lines(5)})
        long_run, short_run = per_run
        self.assertEqual(long_run["host_stall_seconds"], 0)
        self.assertEqual(long_run["stalls"], [])
        rows = {s["name"]: s for s in long_run["stages"]}
        self.assertGreater(rows["a"]["duration_seconds"] + rows["b"]["duration_seconds"], 800)
        self.assertTrue(any("long single-run gap" in g for g in long_run["gaps"]))
        st.check_reconciliation(long_run)
        self.assertEqual(short_run["host_stall_seconds"], 0)

    def test_gaps_below_threshold_are_unchanged(self):
        agg, per_run = self.build({1: run_lines(100), 2: run_lines(100)})
        for run in per_run:
            self.assertEqual(run["host_stall_seconds"], 0)
            self.assertFalse(any("long single-run gap" in g for g in run["gaps"]))
            rows = {s["name"]: s for s in run["stages"]}
            self.assertGreater(rows["a"]["duration_seconds"] + rows["b"]["duration_seconds"], 100)

    def test_non_overlapping_long_gaps_are_not_stalls(self):
        agg, per_run = self.build({1: run_lines(800), 2: run_lines(800, 5000)})
        for run in per_run:
            self.assertEqual(run["host_stall_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
