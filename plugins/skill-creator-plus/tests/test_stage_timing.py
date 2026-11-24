"""Tests for scripts/stage_timing.py and its hooks into the benchmark and the viewer.

Run: python3 -m unittest discover -s plugins/skill-creator-plus/tests -v
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

PLUGIN = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKILL = os.path.join(PLUGIN, "skills", "skill-creator")
sys.path.insert(0, SKILL)

from scripts import stage_timing as st  # noqa: E402


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def read_text(path):
    with open(path) as f:
        return f.read()


def write_marks(run_dir, marks):
    """marks: (stage, event, t) tuples; a str is written as a raw line."""
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "stages.jsonl"), "w") as f:
        for mark in marks:
            f.write(mark if isinstance(mark, str) else json.dumps({"stage": mark[0], "event": mark[1], "t": mark[2]}))
            f.write("\n")


def compute(marks, known=("a", "b"), total=None):
    parsed = [{"stage": s, "event": e, "t": float(t), "order": i} for i, (s, e, t) in enumerate(marks)]
    return st.compute_run(parsed, [], list(known), total)


def by_name(result):
    return {s["name"]: s for s in result["stages"]}


class ComputeRunTest(unittest.TestCase):
    def test_balanced_marks(self):
        r = compute([("a", "start", 100), ("a", "end", 110), ("b", "start", 110), ("b", "end", 125)], total=30)
        s = by_name(r)
        self.assertEqual(s["a"]["duration_seconds"], 10)
        self.assertEqual(s["a"]["start_offset_seconds"], 0)
        self.assertEqual(s["b"]["duration_seconds"], 15)
        self.assertEqual(s["b"]["start_offset_seconds"], 10)
        self.assertEqual(r["accounted_seconds"], 25)
        self.assertEqual(r["unaccounted_seconds"], 5)
        self.assertEqual(r["gaps"], [])

    def test_missing_end_is_a_gap_not_a_crash(self):
        r = compute([("a", "start", 100), ("a", "end", 104), ("b", "start", 104)])
        s = by_name(r)
        self.assertIsNone(s["b"]["duration_seconds"])
        self.assertEqual(s["a"]["duration_seconds"], 4)
        self.assertTrue(any("b has no end mark" in g for g in r["gaps"]))

    def test_end_without_start_and_double_start(self):
        r = compute([("a", "end", 99), ("a", "start", 100), ("a", "start", 102), ("a", "end", 105)])
        self.assertEqual(by_name(r)["a"]["duration_seconds"], 5)
        self.assertTrue(any("without a start" in g for g in r["gaps"]))
        self.assertTrue(any("started again" in g for g in r["gaps"]))

    def test_nesting_counts_time_once(self):
        r = compute([("a", "start", 0), ("b", "start", 2), ("b", "end", 6), ("a", "end", 10)], total=10)
        s = by_name(r)
        self.assertEqual(s["a"]["duration_seconds"], 10)
        self.assertEqual(s["b"]["duration_seconds"], 4)
        self.assertEqual(r["accounted_seconds"], 10)
        self.assertEqual(r["unaccounted_seconds"], 0)
        self.assertTrue(any("b nested in stage a" in g for g in r["gaps"]))

    def test_partial_overlap(self):
        r = compute([("a", "start", 0), ("b", "start", 5), ("a", "end", 8), ("b", "end", 12)], total=12)
        self.assertEqual(r["accounted_seconds"], 12)
        self.assertTrue(any("b overlaps stage a" in g for g in r["gaps"]))

    def test_unaccounted_time_and_overcount(self):
        r = compute([("a", "start", 0), ("a", "end", 6)], total=20)
        self.assertEqual(r["unaccounted_seconds"], 14)
        over = compute([("a", "start", 0), ("a", "end", 30)], total=10)
        self.assertEqual(over["unaccounted_seconds"], 0)
        self.assertTrue(any("more than" in g for g in over["gaps"]))

    def test_no_total_leaves_unaccounted_unknown(self):
        r = compute([("a", "start", 0), ("a", "end", 6)])
        self.assertIsNone(r["unaccounted_seconds"])

    def test_unknown_stage_is_kept_and_flagged(self):
        r = compute([("zzz", "start", 0), ("zzz", "end", 2)])
        self.assertEqual(by_name(r)["zzz"]["duration_seconds"], 2)
        self.assertTrue(any("not listed" in g for g in r["gaps"]))

    def test_marks_out_of_order_are_sorted_by_time(self):
        r = compute([("a", "end", 10), ("a", "start", 4)])
        self.assertEqual(by_name(r)["a"]["duration_seconds"], 6)

    def test_repeated_stage_sums_intervals(self):
        r = compute([("a", "start", 0), ("a", "end", 2), ("a", "start", 5), ("a", "end", 8)])
        self.assertEqual(by_name(r)["a"]["duration_seconds"], 5)
        self.assertEqual(by_name(r)["a"]["intervals"], 2)


class ParseMarksTest(unittest.TestCase):
    def test_bad_lines_are_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_marks(tmp, [("a", "start", 1), "not json", '{"stage": "a", "event": "end"}', ("a", "end", 3)])
            marks, gaps = st.parse_marks(Path(tmp) / "stages.jsonl")
        self.assertEqual([m["event"] for m in marks], ["start", "end"])
        self.assertEqual(len(gaps), 2)

    def test_missing_file(self):
        self.assertEqual(st.parse_marks(Path("/nonexistent/stages.jsonl")), ([], []))


class Fixture:
    """An iteration with two test cases, two runs of with_skill and one of without_skill each."""

    def __init__(self, root, with_skill_durations=((10, 20), (12, 22)), baseline=(15, 30)):
        self.root = root
        write_json(os.path.join(root, "stages.json"), {"stages": [
            {"name": "read", "description": "read the input"},
            {"name": "build", "description": "build the output"},
        ]})
        for case in ("case-one", "case-two"):
            write_json(os.path.join(root, case, "eval_metadata.json"), {"eval_name": case, "prompt": "p", "assertions": []})
            for i, (read, build) in enumerate(with_skill_durations, start=1):
                self.run(case, "with_skill", i, read, build)
            self.run(case, "without_skill", None, *baseline)

    def run(self, case, config, number, read, build):
        run_dir = os.path.join(self.root, case, config, *([f"run-{number}"] if number else []))
        write_json(os.path.join(run_dir, "grading.json"), {
            "summary": {"pass_rate": 1.0, "passed": 1, "failed": 0, "total": 1},
            "expectations": [{"text": "t", "passed": True, "evidence": "e"}],
        })
        write_json(os.path.join(run_dir, "timing.json"), {"total_tokens": 10, "total_duration_seconds": read + build + 3})
        os.makedirs(os.path.join(run_dir, "outputs"), exist_ok=True)
        write_marks(run_dir, [
            ("read", "start", 1000), ("read", "end", 1000 + read),
            ("build", "start", 1000 + read), ("build", "end", 1000 + read + build),
        ])


class AggregateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_aggregation_mean_and_stddev(self):
        it = os.path.join(self.tmp, "iteration-1")
        Fixture(it)
        from scripts.aggregate_benchmark import generate_benchmark, generate_markdown
        benchmark = generate_benchmark(Path(it), "demo")
        agg = benchmark["stage_timing"]
        with_skill = agg["configurations"]["with_skill"]
        read = with_skill["stages"]["read"]
        # four runs: 10, 12, 10, 12
        self.assertEqual(read["duration_seconds"]["mean"], 11)
        self.assertAlmostEqual(read["duration_seconds"]["stddev"], 1.1547, places=3)
        self.assertEqual(read["runs"], 4)
        self.assertEqual(with_skill["stages"]["build"]["start_offset_seconds"]["mean"], 11)
        self.assertEqual(with_skill["runs"], 4)
        self.assertEqual(agg["configurations"]["without_skill"]["stages"]["build"]["duration_seconds"]["mean"], 30)
        self.assertEqual(with_skill["unaccounted_seconds"]["mean"], 3)
        self.assertEqual([s["name"] for s in agg["stages"]], ["read", "build"])
        json.dumps(benchmark)  # the run directories must not leak into the JSON
        # per-run file
        per_run = json.loads(read_text(os.path.join(it, "case-one", "with_skill", "run-1", "stage_timing.json")))
        self.assertEqual(per_run["unaccounted_seconds"], 3)
        self.assertIn("## Stage Timing", generate_markdown(benchmark))

    def test_runs_without_marks_are_reported(self):
        it = os.path.join(self.tmp, "iteration-1")
        Fixture(it)
        os.remove(os.path.join(it, "case-one", "without_skill", "stages.jsonl"))
        from scripts.aggregate_benchmark import generate_benchmark
        agg = generate_benchmark(Path(it), "demo")["stage_timing"]
        self.assertEqual(agg["configurations"]["without_skill"]["runs"], 1)
        self.assertEqual(agg["configurations"]["without_skill"]["runs_total"], 2)
        self.assertTrue(any("1 of 2 runs" in g["issue"] for g in agg["gaps"]))

    def test_no_marks_means_no_stage_section(self):
        it = os.path.join(self.tmp, "iteration-1")
        Fixture(it)
        for root, _, files in os.walk(it):
            if "stages.jsonl" in files:
                os.remove(os.path.join(root, "stages.jsonl"))
        from scripts.aggregate_benchmark import generate_benchmark
        self.assertNotIn("stage_timing", generate_benchmark(Path(it), "demo"))


class SvgTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def aggregate(self, name, **kwargs):
        it = os.path.join(self.tmp, name)
        Fixture(it, **kwargs)
        return Path(it), st.build_stage_timing(Path(it), [
            (c, f"{case}/{c}", Path(d))
            for case in ("case-one", "case-two")
            for c, d in (
                [("with_skill", os.path.join(it, case, "with_skill", f"run-{n}")) for n in (1, 2)]
                + [("without_skill", os.path.join(it, case, "without_skill"))]
            )
        ])

    def test_svg_is_well_formed_with_previous(self):
        _, current = self.aggregate("iteration-2")
        _, previous = self.aggregate("iteration-1", with_skill_durations=((20, 40),))
        for standalone in (True, False):
            svg = st.render_waterfall_svg(current, previous, standalone=standalone)
            root = ET.fromstring(svg)
            self.assertTrue(root.tag.endswith("svg"))
            self.assertIn("viewBox", root.attrib)
            self.assertIn("(previous iteration)", svg)
            # 3 panels x 2 stages = 6 bars
            self.assertEqual(len(re.findall(r"<rect [^>]*fill=", svg)), 6)
        self.assertIn("prefers-color-scheme", st.render_waterfall_svg(current, None, standalone=True))
        self.assertNotIn("prefers-color-scheme", st.render_waterfall_svg(current, None))

    def test_svg_escapes_names(self):
        agg = {
            "stages": [{"name": "a<b&c", "description": ""}],
            "configurations": {"with_skill": {
                "runs": 1, "runs_total": 1,
                "stages": {"a<b&c": {
                    "duration_seconds": {"mean": 2, "stddev": 0, "min": 2, "max": 2},
                    "start_offset_seconds": {"mean": 0, "stddev": 0, "min": 0, "max": 0}, "runs": 1}},
                "total_seconds": None, "unaccounted_seconds": None}},
            "gaps": [],
        }
        ET.fromstring(st.render_waterfall_svg(agg))

    def test_empty_svg_is_well_formed(self):
        ET.fromstring(st.render_waterfall_svg({"stages": [], "configurations": {}, "gaps": []}))

    def test_write_artifacts_finds_previous_iteration(self):
        _, previous = self.aggregate("iteration-1", with_skill_durations=((20, 40),))
        it, current = self.aggregate("iteration-2")
        Path(self.tmp, "iteration-1", "stage_timing.json").write_text(json.dumps(previous))
        paths = st.write_artifacts(it, current)
        self.assertEqual({p.name for p in paths}, {"stage_timing.json", "waterfall.svg"})
        svg = (it / "waterfall.svg").read_text()
        ET.fromstring(svg)
        self.assertIn("previous iteration", svg)


class EndToEndTest(unittest.TestCase):
    def test_cli_benchmark_and_static_viewer_hold_the_waterfall(self):
        with tempfile.TemporaryDirectory() as tmp:
            Fixture(os.path.join(tmp, "iteration-1"), with_skill_durations=((20, 40),))
            subprocess.run([sys.executable, "-m", "scripts.aggregate_benchmark", os.path.join(tmp, "iteration-1")],
                           cwd=SKILL, check=True, capture_output=True)
            it = os.path.join(tmp, "iteration-2")
            Fixture(it)
            subprocess.run([sys.executable, "-m", "scripts.aggregate_benchmark", it, "--skill-name", "demo"],
                           cwd=SKILL, check=True, capture_output=True)
            # also works as a plain script, as the docs of aggregate_benchmark.py show
            subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "aggregate_benchmark.py"), it],
                           cwd=tmp, check=True, capture_output=True)
            self.assertTrue(os.path.exists(os.path.join(it, "waterfall.svg")))
            self.assertIn("## Stage Timing", read_text(os.path.join(it, "benchmark.md")))
            self.assertIn("stage_timing", json.loads(read_text(os.path.join(it, "benchmark.json"))))

            html_path = os.path.join(tmp, "review.html")
            subprocess.run([sys.executable, os.path.join(SKILL, "eval-viewer", "generate_review.py"), it,
                            "--skill-name", "demo", "--benchmark", os.path.join(it, "benchmark.json"),
                            "--previous-workspace", os.path.join(tmp, "iteration-1"), "--static", html_path],
                           check=True, capture_output=True)
            html = read_text(html_path)
            match = re.search(r"const EMBEDDED_DATA = (\{.*\});\n", html)
            data = json.loads(match.group(1))
            chart = data["stage_chart"]
            self.assertIn("with_skill", chart["stage_timing"]["configurations"])
            self.assertIsNotNone(chart["previous_stage_timing"])
            ET.fromstring(chart["svg"])
            self.assertIn("(previous iteration)", chart["svg"])
            self.assertIn("stageChart.svg", html)
            self.assertNotIn("cdn.sheetjs", chart["svg"])

            # the standalone command
            out = subprocess.run([sys.executable, "-m", "scripts.stage_timing", it], cwd=SKILL, check=True, capture_output=True, text=True)
            self.assertIn("waterfall.svg", out.stdout)

    def test_cli_without_marks_exits_with_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            it = os.path.join(tmp, "iteration-1")
            Fixture(it)
            for root, _, files in os.walk(it):
                if "stages.jsonl" in files:
                    os.remove(os.path.join(root, "stages.jsonl"))
            r = subprocess.run([sys.executable, "-m", "scripts.stage_timing", it], cwd=SKILL, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("no stage timing", r.stderr)


if __name__ == "__main__":
    unittest.main()
