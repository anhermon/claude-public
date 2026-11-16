"""Tests for transcript-based stage timing (scripts/stage_timing.py).

Run: python3 -m unittest discover -s plugins/skill-creator-plus/tests -v
"""
import datetime
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

PLUGIN = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKILL = os.path.join(PLUGIN, "skills", "skill-creator")
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
sys.path.insert(0, SKILL)

from scripts import stage_timing as st  # noqa: E402

BASE = 1_700_000_000.0


def iso(seconds):
    return datetime.datetime.fromtimestamp(BASE + seconds, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def prompt(t):
    return {"type": "user", "timestamp": iso(t), "message": {"role": "user", "content": "go"}}


def call(t, *uses, text=None, tokens=None, message_id=None):
    """One assistant message. uses are (tool_use_id, tool name, input dict)."""
    content = []
    if text:
        content.append({"type": "text", "text": text})
    content += [{"type": "tool_use", "id": i, "name": n, "input": inp} for i, n, inp in uses]
    message = {"role": "assistant", "content": content, "id": message_id or f"msg-{t}"}
    if tokens is not None:
        message["usage"] = {"output_tokens": tokens}
    return {"type": "assistant", "timestamp": iso(t), "message": message}


def result(t, *ids):
    return {"type": "user", "timestamp": iso(t), "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": i, "content": "ok"} for i in ids]}}


def bash(tool_id, command):
    return (tool_id, "Bash", {"command": command})


def by_name(run):
    return {s["name"]: s for s in run["stages"]}


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def reconciles(run):
    parts = (sum(s["duration_seconds"] or 0 for s in run["stages"]) + run["startup_seconds"]
             + run["handback_seconds"] + run["unattributed_seconds"])
    return abs(parts - run["wall_seconds"]) <= 1.0


class MarkerTest(unittest.TestCase):
    def test_bash_comment(self):
        found = st.extract_markers("# stage: collect-stats\npython3 collect.py", "Bash")
        self.assertEqual([(m["stage"], m["event"]) for m in found], [("collect-stats", "start")])

    def test_comment_must_be_a_whole_line(self):
        self.assertEqual(st.extract_markers("echo 'see # stage: x for details'", "Bash"), [])

    def test_text_note(self):
        found = st.extract_markers("Reading it now.\nstage: read-readme\n", "text")
        self.assertEqual([m["stage"] for m in found], ["read-readme"])

    def test_end_marker_closes(self):
        found = st.extract_markers("# stage: end", "Bash")
        self.assertEqual([(m["stage"], m["event"]) for m in found], [(None, "end")])

    def test_legacy_json_and_helper_forms(self):
        text = ('echo \'{"stage":"a","event":"start","t":1}\' >> s; '
                "m(){ python3 -c 'import time,json,sys;print(json.dumps({\"stage\":sys.argv[1],\"event\":sys.argv[2]}))' $1 $2 >> $S; }; "
                "m b start; ls; m b end; m c start")
        found = st.extract_markers(text, "Bash")
        self.assertEqual([(m["stage"], m["event"]) for m in found],
                         [("a", "start"), ("b", "start"), ("b", "end"), ("c", "start")])


class TranscriptTimelineTest(unittest.TestCase):
    def test_comment_marker_splits_model_and_tool_time(self):
        lines = [
            prompt(0),
            call(4, bash("t1", "# stage: collect-stats\npython3 collect.py"), tokens=50),
            result(10, "t1"),
            call(12, text="Done."),
        ]
        run = st.compute_transcript_run(lines)
        s = by_name(run)["collect-stats"]
        self.assertAlmostEqual(s["model_seconds"], 4, places=2)
        self.assertAlmostEqual(s["tool_seconds"], 6, places=2)
        self.assertAlmostEqual(s["duration_seconds"], 10, places=2)
        self.assertEqual(s["output_tokens"], 50)
        self.assertAlmostEqual(run["handback_seconds"], 2, places=2)
        self.assertAlmostEqual(run["startup_seconds"], 0, places=2)
        self.assertAlmostEqual(run["wall_seconds"], 12, places=2)
        self.assertTrue(reconciles(run))

    def test_stage_spans_several_calls_and_unmarked_call_inherits(self):
        lines = [
            prompt(0),
            call(2, bash("t1", "# stage: a\nls")), result(5, "t1"),
            call(9, bash("t2", "cat file")), result(10, "t2"),
            call(15, bash("t3", "# stage: b\nwrite")), result(16, "t3"),
            call(17, text="ok"),
        ]
        run = st.compute_transcript_run(lines)
        s = by_name(run)
        self.assertAlmostEqual(s["a"]["duration_seconds"], 10, places=2)
        self.assertEqual(s["a"]["intervals"], 2)
        self.assertAlmostEqual(s["a"]["model_seconds"], 2 + 4, places=2)
        self.assertAlmostEqual(s["b"]["model_seconds"], 5, places=2)
        self.assertAlmostEqual(s["b"]["tool_seconds"], 1, places=2)
        self.assertTrue(reconciles(run))

    def test_calls_before_the_first_stage_are_startup(self):
        lines = [
            prompt(0),
            call(3, bash("t0", "cat SKILL.md")), result(5, "t0"),
            call(7, bash("t1", "# stage: a\nls")), result(8, "t1"),
            call(9, bash("t2", "# stage: end\necho")), result(10, "t2"),
            call(12, text="bye"),
        ]
        run = st.compute_transcript_run(lines)
        self.assertAlmostEqual(run["startup_seconds"], 5, places=2)
        self.assertAlmostEqual(by_name(run)["a"]["duration_seconds"], 3, places=2)
        self.assertAlmostEqual(run["handback_seconds"], 4, places=2)
        self.assertTrue(reconciles(run))

    def test_stage_note_in_text_applies_to_non_bash_tool(self):
        lines = [
            prompt(0),
            call(3, ("r1", "Read", {"file_path": "README.md"}), text="stage: read-readme"),
            result(4, "r1"),
            call(5, text="done"),
        ]
        run = st.compute_transcript_run(lines)
        self.assertAlmostEqual(by_name(run)["read-readme"]["duration_seconds"], 4, places=2)

    def test_parallel_tool_calls_count_once(self):
        lines = [
            prompt(0),
            call(4, bash("t1", "# stage: a\nsleep 1"), bash("t2", "ls"), tokens=30),
            result(8, "t1"),
            result(10, "t2"),
            call(11, text="end"),
        ]
        run = st.compute_transcript_run(lines)
        s = by_name(run)["a"]
        self.assertAlmostEqual(s["model_seconds"], 4, places=2)
        self.assertAlmostEqual(s["tool_seconds"], 6, places=2)
        self.assertTrue(reconciles(run))

    def test_one_message_split_over_lines_is_one_call(self):
        first = call(4, bash("t1", "# stage: a\nls"), message_id="m1", tokens=20)
        second = call(4.2, bash("t2", "pwd"), message_id="m1", tokens=20)
        run = st.compute_transcript_run([prompt(0), first, second, result(6, "t1", "t2"), call(7, text="x")])
        s = by_name(run)["a"]
        self.assertAlmostEqual(s["model_seconds"], 4.2, places=2)
        self.assertEqual(s["output_tokens"], 20)
        self.assertTrue(reconciles(run))

    def test_missing_tool_result_is_unattributed_and_reported(self):
        lines = [
            prompt(0),
            call(2, bash("t1", "# stage: a\nls")), result(4, "t1"),
            call(6, bash("t2", "hang")),
            call(20, text="gave up"),
        ]
        run = st.compute_transcript_run(lines)
        self.assertGreaterEqual(run["unattributed_seconds"], 13)
        self.assertTrue(any("t2" in g and "tool_result" in g for g in run["gaps"]))
        self.assertTrue(reconciles(run))

    def test_legacy_marks_in_tool_input_with_sidecar_timestamps(self):
        command = ("m(){ python3 -c 'import json,sys;print(json.dumps({\"stage\":sys.argv[1]}))' $1 $2 >> $S; }; "
                   "m a start; ls; m a end; m b start; make; m b end")
        lines = [prompt(0), call(10, bash("t1", command)), result(40, "t1"), call(41, text="x")]
        sidecar = [
            {"stage": "a", "event": "start", "t": BASE + 12}, {"stage": "a", "event": "end", "t": BASE + 20},
            {"stage": "b", "event": "start", "t": BASE + 30}, {"stage": "b", "event": "end", "t": BASE + 38},
        ]
        run = st.compute_transcript_run(lines, sidecar_marks=sidecar)
        s = by_name(run)
        # a stage owns the time from its own start mark to the next stage's start mark
        self.assertAlmostEqual(s["a"]["tool_seconds"], 20, places=2)
        self.assertAlmostEqual(s["b"]["tool_seconds"], 10, places=2)
        self.assertAlmostEqual(s["a"]["model_seconds"] + s["b"]["model_seconds"], 10, places=2)
        self.assertTrue(reconciles(run))

    def test_legacy_multi_stage_call_without_sidecar_splits_evenly_and_says_so(self):
        command = "m(){ python3 -c 'import json,sys;print(json.dumps({\"stage\":sys.argv[1]}))' $1 $2 >> $S; }; m a start; ls; m a end; m b start; make; m b end"
        lines = [prompt(0), call(10, bash("t1", command)), result(30, "t1"), call(31, text="x")]
        run = st.compute_transcript_run(lines)
        s = by_name(run)
        self.assertAlmostEqual(s["a"]["tool_seconds"], 10, places=2)
        self.assertAlmostEqual(s["b"]["tool_seconds"], 10, places=2)
        self.assertTrue(any("split evenly" in g for g in run["gaps"]))

    def test_reconciliation_check_raises_when_off(self):
        run = st.compute_transcript_run([prompt(0), call(2, bash("t1", "# stage: a\nls")), result(5, "t1"), call(6, text="x")])
        st.check_reconciliation(run)
        run["wall_seconds"] += 5
        with self.assertRaises(ValueError):
            st.check_reconciliation(run)

    def test_empty_transcript_does_not_raise(self):
        run = st.compute_transcript_run([])
        self.assertEqual(run["stages"], [])
        self.assertTrue(run["gaps"])


class RealRunFixtureTest(unittest.TestCase):
    """A trimmed, anonymized transcript of a real run that batched its marks into two commands."""

    def setUp(self):
        self.lines = read_jsonl(os.path.join(FIXTURES, "batched_marks_transcript.jsonl"))
        self.marks = read_jsonl(os.path.join(FIXTURES, "batched_marks_stages.jsonl"))
        self.run = st.compute_transcript_run(self.lines, sidecar_marks=self.marks)

    def test_report_writing_includes_the_generation_window(self):
        report = by_name(self.run)["write-report"]
        self.assertGreaterEqual(report["duration_seconds"], 30)
        # the heredoc is written by the model before any mark runs: model time must be there
        self.assertGreater(report["model_seconds"], 5)
        self.assertGreater(report["tool_seconds"], 10)

    def test_little_is_unattributed(self):
        self.assertLess(self.run["unattributed_seconds"], 0.1 * self.run["wall_seconds"])
        self.assertLess(self.run["unaccounted_seconds"], 0.1 * self.run["wall_seconds"])

    def test_total_reconciles(self):
        self.assertTrue(reconciles(self.run), self.run)
        st.check_reconciliation(self.run)
        self.assertAlmostEqual(self.run["wall_seconds"], 126.6, delta=0.5)

    def test_every_stage_has_a_model_tool_split_and_tokens(self):
        for name in ("read-readme", "collect-stats", "write-observations", "write-report", "check-report"):
            s = by_name(self.run)[name]
            self.assertIsNotNone(s["model_seconds"], name)
            self.assertIsNotNone(s["tool_seconds"], name)
            self.assertAlmostEqual(s["model_seconds"] + s["tool_seconds"], s["duration_seconds"], places=2)
        self.assertGreater(by_name(self.run)["write-report"]["output_tokens"], 1000)

    def test_without_sidecar_the_batched_call_is_still_attributed(self):
        run = st.compute_transcript_run(self.lines)
        self.assertTrue(reconciles(run))
        self.assertLess(run["unattributed_seconds"], 0.1 * run["wall_seconds"])


class RunDirectoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def make_run(self, name="run-1", timing=None, transcript_at=None, marks=None):
        run_dir = os.path.join(self.tmp, name)
        os.makedirs(run_dir)
        if timing is not None:
            with open(os.path.join(run_dir, "timing.json"), "w") as f:
                json.dump(timing, f)
        if transcript_at:
            shutil.copy(os.path.join(FIXTURES, "batched_marks_transcript.jsonl"), transcript_at(run_dir))
        if marks:
            write_jsonl(os.path.join(run_dir, "stages.jsonl"), marks)
        return Path(run_dir)

    def test_find_transcript_by_relative_path_in_timing_json(self):
        def put(run_dir):
            os.makedirs(os.path.join(run_dir, "logs"))
            return os.path.join(run_dir, "logs", "agent.jsonl")
        run_dir = self.make_run(timing={"transcript_path": "logs/agent.jsonl"}, transcript_at=put)
        self.assertEqual(st.find_transcript(run_dir), run_dir / "logs" / "agent.jsonl")

    def test_find_transcript_by_absolute_path(self):
        other = os.path.join(self.tmp, "elsewhere.jsonl")
        shutil.copy(os.path.join(FIXTURES, "batched_marks_transcript.jsonl"), other)
        run_dir = self.make_run(timing={"transcript_path": other})
        self.assertEqual(st.find_transcript(run_dir), Path(other))

    def test_find_transcript_by_agent_id_under_home(self):
        home = Path(self.tmp) / "home"
        sub = home / ".claude" / "projects" / "proj" / "sess" / "subagents"
        sub.mkdir(parents=True)
        shutil.copy(os.path.join(FIXTURES, "batched_marks_transcript.jsonl"), sub / "agent-abc123.jsonl")
        run_dir = self.make_run(timing={"agent_id": "abc123"})
        self.assertEqual(st.find_transcript(run_dir, home=home), sub / "agent-abc123.jsonl")

    def test_find_transcript_default_name_and_none(self):
        run_dir = self.make_run(transcript_at=lambda d: os.path.join(d, "transcript.jsonl"))
        self.assertEqual(st.find_transcript(run_dir), run_dir / "transcript.jsonl")
        self.assertIsNone(st.find_transcript(self.make_run("run-2")))

    def test_analyze_run_prefers_transcript_and_falls_back_to_marks(self):
        with_transcript = self.make_run(transcript_at=lambda d: os.path.join(d, "transcript.jsonl"),
                                        marks=read_jsonl(os.path.join(FIXTURES, "batched_marks_stages.jsonl")))
        self.assertEqual(st.analyze_run(with_transcript, [])["source"], "transcript")
        legacy = self.make_run("run-2", timing={"total_duration_seconds": 100}, marks=[
            {"stage": "a", "event": "start", "t": 100.0}, {"stage": "a", "event": "end", "t": 110.0}])
        r = st.analyze_run(legacy, [])
        self.assertEqual(r["source"], "marks")
        self.assertIsNone(by_name(r)["a"].get("model_seconds"))
        self.assertIsNone(st.analyze_run(self.make_run("run-3"), []))

    def test_unreadable_transcript_falls_back_with_a_gap(self):
        run_dir = self.make_run(marks=[{"stage": "a", "event": "start", "t": 1.0}, {"stage": "a", "event": "end", "t": 2.0}])
        (run_dir / "transcript.jsonl").write_text("not json\n")
        r = st.analyze_run(run_dir, [])
        self.assertEqual(r["source"], "marks")
        self.assertTrue(any("transcript" in g for g in r["gaps"]))


class AggregateAndChartTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def iteration(self, with_transcript=True):
        it = Path(self.tmp) / "iteration-1"
        runs = []
        for n in (1, 2):
            run_dir = it / "case" / "with_skill" / f"run-{n}"
            os.makedirs(run_dir)
            if with_transcript:
                shutil.copy(os.path.join(FIXTURES, "batched_marks_transcript.jsonl"), run_dir / "transcript.jsonl")
            shutil.copy(os.path.join(FIXTURES, "batched_marks_stages.jsonl"), run_dir / "stages.jsonl")
            runs.append(("with_skill", f"case/with_skill/run-{n}", run_dir))
        return it, runs

    def test_aggregate_has_model_tool_startup_handback(self):
        it, runs = self.iteration()
        agg = st.build_stage_timing(it, runs)
        self.assertEqual(agg["source"], "transcript")
        cfg = agg["configurations"]["with_skill"]
        row = cfg["stages"]["write-report"]
        self.assertGreater(row["model_seconds"]["mean"], 5)
        self.assertGreater(row["tool_seconds"]["mean"], 10)
        self.assertGreater(row["output_tokens"]["mean"], 1000)
        for key in ("startup_seconds", "handback_seconds", "unaccounted_seconds", "total_seconds"):
            self.assertIsNotNone(cfg[key], key)

    def test_svg_stacks_model_and_tool_with_a_legend_and_keeps_theme(self):
        it, runs = self.iteration()
        agg = st.build_stage_timing(it, runs)
        svg = st.render_waterfall_svg(agg, None, standalone=True)
        ET.fromstring(svg)
        self.assertIn("model", svg)
        self.assertIn("tool", svg)
        self.assertIn('class="legend"', svg)
        self.assertIn("prefers-color-scheme: dark", svg)
        self.assertIn("startup", svg)
        self.assertIn("handback", svg)
        self.assertNotIn("shell-only marks", svg)

    def test_markdown_table_has_model_and_tool_columns(self):
        it, runs = self.iteration()
        table = st.markdown_table(st.build_stage_timing(it, runs))
        self.assertIn("model", table)
        self.assertIn("tool", table)
        self.assertIn("unattributed", table)

    def test_marks_only_chart_is_labelled(self):
        it, runs = self.iteration(with_transcript=False)
        agg = st.build_stage_timing(it, runs)
        self.assertEqual(agg["source"], "marks")
        label = "shell-only marks: model time not attributed"
        self.assertIn(label, st.render_waterfall_svg(agg))
        self.assertIn(label, st.markdown_table(agg))


if __name__ == "__main__":
    unittest.main()
