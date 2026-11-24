"""Regression tests for what the stage table, chart and viewer show (scripts/stage_timing.py).

Run: python3 -m unittest discover -s plugins/skill-creator-plus/tests -v
"""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from test_stage_timing_transcript import (  # noqa: E402
    PLUGIN, SKILL, bash, call, prompt, result, st, write_jsonl,
)


def make_iteration(root):
    """Two runs that declare stage names beyond the two listed in stages.json (`x` and `y` are off-list)."""
    it = Path(root) / "iteration-1"
    it.mkdir()
    (it / "stages.json").write_text(json.dumps({"stages": [
        {"name": "a", "description": "listed and used"}, {"name": "never-used", "description": "listed, no time"}]}))
    shapes = {
        1: [prompt(0), call(2, bash("t1", "# stage: a\nls")), result(12, "t1"),
            call(14, bash("t2", "# stage: x\nmake")), result(24, "t2"), call(30, text="done")],
        2: [prompt(0), call(2, bash("t1", "# stage: a\nls")), result(8, "t1"),
            call(10, bash("t2", "# stage: y\nmake")), result(40, "t2"), call(44, text="done")],
    }
    runs = []
    for n, lines in shapes.items():
        run_dir = it / "case" / "with_skill" / f"run-{n}"
        write_jsonl(str(run_dir / "transcript.jsonl"), lines)
        wall = 30 if n == 1 else 44
        (run_dir / "timing.json").write_text(json.dumps({"total_duration_seconds": wall + 2.0}))
        runs.append(("with_skill", f"case/with_skill/run-{n}", run_dir))
    return it, runs


class DisplayTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.it, self.runs = make_iteration(self.tmp)
        self.agg = st.build_stage_timing(self.it, self.runs)
        self.cfg = self.agg["configurations"]["with_skill"]

    # 1. every stage with time is shown, in first-seen order, off-list ones flagged, n per stage, rows add up
    def test_every_timed_stage_is_listed_in_first_seen_order(self):
        self.assertEqual([s["name"] for s in self.agg["stages"]], ["a", "x", "y"])
        flags = {s["name"]: s["in_stages_json"] for s in self.agg["stages"]}
        self.assertEqual(flags, {"a": True, "x": False, "y": False})
        self.assertEqual({n: self.cfg["stages"][n]["runs"] for n in "axy"}, {"a": 2, "x": 1, "y": 1})

    def test_markdown_flags_off_list_stages_and_states_n(self):
        table = st.markdown_table(self.agg)
        self.assertIn("| x *(not in stages.json)* |", table)
        self.assertIn("| y *(not in stages.json)* |", table)
        self.assertNotIn("| a *(not in stages.json)*", table)
        self.assertNotIn("never-used", table)
        self.assertRegex(table, r"\| x [^\n]*n=1 of 2")
        self.assertRegex(table, r"\| a [^\n]*n=2 of 2")

    def test_total_row_equals_mean_wall_time_and_rows_add_up(self):
        total = self.cfg["total_seconds"]["mean"]
        self.assertAlmostEqual(total, 37.0, places=2)
        rows = sum(s["per_run_seconds"] for s in self.cfg["stages"].values())
        rows += sum((self.cfg[k] or {"mean": 0})["mean"] for k in ("startup_seconds", "handback_seconds", "unaccounted_seconds"))
        self.assertAlmostEqual(rows, total, delta=0.05)
        table = st.markdown_table(self.agg)
        self.assertIn("| total (transcript wall) | 37.0s", table)
        self.assertRegex(table, r"rows add up to 37\.0s")

    # 2. one labelled basis: transcript wall time, with the notification duration beside it
    def test_both_time_bases_are_labelled(self):
        self.assertAlmostEqual(self.cfg["notification_seconds"]["mean"], 39.0, places=2)
        table = st.markdown_table(self.agg)
        self.assertIn("transcript wall", table)
        self.assertIn("notification duration", table)
        self.assertIn("39.0s", table)
        svg = st.render_waterfall_svg(self.agg)
        self.assertIn("transcript wall 37.0s", svg)
        self.assertIn("notification duration 39.0s", svg)

    def test_no_second_basis_when_they_agree(self):
        for _, _, run_dir in self.runs:
            (run_dir / "timing.json").unlink()
        table = st.markdown_table(st.build_stage_timing(self.it, self.runs))
        self.assertNotIn("notification duration", table)

    # 4. startup and handback are rows in the chart with their seconds
    def test_chart_labels_startup_and_handback_with_seconds(self):
        svg = st.render_waterfall_svg(self.agg)
        handback = self.cfg["handback_seconds"]["mean"]
        self.assertGreater(handback, 3)
        self.assertRegex(svg, r">handback</text>")
        self.assertIn(f"{handback:.1f}s", svg)
        self.assertRegex(svg, r">startup</text>")
        self.assertIn("* not in stages.json", svg)
        self.assertRegex(svg, r">x\*</text>")

    # one definition: the chart label for a stage is the table's per-run mean, with coverage when partial
    def test_chart_label_equals_table_value_for_a_stage_in_some_runs(self):
        svg = st.render_waterfall_svg(self.agg)
        table = st.markdown_table(self.agg)
        for name, label_runs in (("x", "1/2 runs"), ("y", "1/2 runs"), ("a", None)):
            row = self.cfg["stages"][name]
            value = f"{row['per_run_seconds']:.1f}s"
            self.assertRegex(table, rf"\| {name} [^\n]*{re.escape(value)} per run \(n={row['runs']} of 2")
            texts = re.findall(r'<text class="muted"[^>]*>([^<]*)</text>', svg)
            labels = [t for t in texts if t.startswith(value)]
            self.assertTrue(labels, f"no chart label starting with {value} for {name}: {texts}")
            if label_runs:
                self.assertIn(f"{value} \u00b7 {label_runs}", labels)
            else:
                self.assertIn(f"{value} \u00b1 {row['duration_seconds']['stddev']:.1f}", labels)
                self.assertFalse([t for t in labels if "runs" in t])
        # x is in one run of two: the when-present mean (10.0s) must not be what the chart shows
        self.assertNotAlmostEqual(self.cfg["stages"]["x"]["duration_seconds"]["mean"], self.cfg["stages"]["x"]["per_run_seconds"])
        self.assertNotIn(f"{self.cfg['stages']['x']['duration_seconds']['mean']:.1f}s \u00b1", svg)

    def test_chart_bars_sum_to_per_run_totals(self):
        svg = st.render_waterfall_svg(self.agg)
        self.assertIn(f"{self.cfg['stages']['x']['per_run_seconds']:.1f}s", svg)
        self.assertIn("per-run mean", svg)

    # 3. the executor prompt carries the exact allowed names
    def test_skill_md_pastes_allowed_names_into_the_executor_prompt(self):
        text = Path(SKILL, "SKILL.md").read_text()
        self.assertIn("Allowed stage names", text)
        self.assertRegex(text, r"(?s)Allowed stage names.{0,400}stages\.json")
        self.assertRegex(text, r"(?i)only these names")
        self.assertIn("other", text)

    def test_viewer_table_lists_all_stages_with_total_and_flags(self):
        html = Path(SKILL, "eval-viewer", "viewer.html").read_text()
        self.assertIn("not in stages.json", html)
        self.assertIn("in_stages_json", html)
        self.assertIn("<td>total</td>", html)

    def test_readme_describes_transcript_markers(self):
        text = Path(PLUGIN, "README.md").read_text()
        self.assertIn("# stage:", text)
        self.assertNotIn("appends start/end marks", text)
        self.assertNotIn("Each run appends", text)


if __name__ == "__main__":
    unittest.main()
