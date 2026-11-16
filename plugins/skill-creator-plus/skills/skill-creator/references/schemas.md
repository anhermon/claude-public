# Schemas

This document defines the file formats used by skill-creator.

---

## Test cases (`evals/<case-name>/`)

Each test is a folder under `evals/` in the skill directory, in the layout `claude plugin eval` reads (the tree is in SKILL.md, under Test Cases). Always write new tests this way. You never need the CLI to use them.

**Case name**: the folder name. Lowercase letters, digits and hyphens, starting with a letter; a few words on what the test checks. Don't use `results`, `mocks` or `node_modules` (the CLI keeps those names for itself), `files` (older tests keep their input files in `evals/files/`), or `true`, `false` or `null` (they don't read as text in `case.yaml`).

**prompt.md**: a settings block, copied as is, then the prompt exactly as the user would type it.

```markdown
---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

User's task prompt
```

- Only the CLI uses the settings: `max_turns` and `timeout_seconds` cap a run, `allowed_tools` is what the run may ask for, `tags` let the user filter. An unknown key there makes the case fail to load.
- Keep free text out of the settings block. It ends at the first `---` it meets, even in the middle of a sentence, so descriptions go in `case.yaml`.

**case.yaml**: the version (quoted, or it reads as a number and the case fails to load), the name (same as the folder), and a human-readable description of success (indented under the `|`, so that no character in it needs escaping).

```yaml
schema_version: "1.1"
name: flags-negative-quantity
expected_outcome: |
  Description of expected result
```

**graders/NN-few-words.md**: one verifiable statement per file, numbered so that they keep their order (`01-states-total-revenue.md`, `02-flags-negative-row.md`). The block on top is always the same, and the CLI ignores a file without it; the body is the statement.

```markdown
---
type: llm
focus: trace
weight: 1
---

summary.md states a total revenue of 693.5
```

`focus: trace` lets the CLI's judge see what was done as well as the final message, and equal weights make the CLI's score the same pass rate you compute.

A case with no grader fails to load, so write a placeholder with the case: `graders/01-expected-output.md`, with the same block on top and the body `The result matches this description: <the expected outcome>` (or, with no description to go on, `The response completes the task the prompt asks for.`). It stays until the case has real assertions, and you never grade it yourself.

If a case holds graders of another `type` (`regex`, `file_exists`, `tool_used`, `tool_order`, `baseline`), someone wrote them for the CLI. Leave them as they are, and grade what each one describes as well as you can from the outputs and transcript.

**Input files**: put them in the case's `files/` folder and hand their paths to the run. So that the CLI can find them too, do three more things: end the prompt with a line `Input files: orders.csv, notes.txt`; add this `place-files.sh` next to `prompt.md`:

```bash
#!/usr/bin/env bash
set -eu
cp -R "$(dirname "$0")/files/." .
```

and name it in `case.yaml`:

```yaml
context:
  scaffold_script: place-files.sh
```

**Running the same tests with the CLI** (optional; Claude Code v2.1.269 or later), from the skill directory: `claude plugin eval . --allow-tools Write,Edit,Bash`, plus `--scaffold` if any case has input files. It runs each case folder with and without the skill (it does not read `evals.json`) and writes its own report under `evals/results/`. These are real, billed model runs, so if the user has Claude Code, offer it rather than just doing it.

---

## evals.json (older format: read it, don't write it)

Earlier versions of skill-creator kept all tests in `evals/evals.json`. When a skill has one, run its tests along with the case folders, taking each test's prompt, input files and assertions from its entry, and leave the file untouched unless the user asks otherwise.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's example prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/sample1.pdf"],
      "expectations": [
        "The output includes X",
        "The skill used script Y"
      ]
    }
  ]
}
```

| evals.json | case folder |
|---|---|
| `skill_name` + `id` | the case name (below) |
| `prompt` | body of `prompt.md` |
| `expected_output` | `expected_outcome` in `case.yaml` |
| `files` (paths relative to the skill root) | copies in the case's `files/` |
| each `expectations` entry (`assertions` in some files; read both) | one file in `graders/` |

**Case name of an old test**: always `<skill>-<label>`.

1. To slug a text: lowercase it, keep its first 8 words, turn every run of characters other than a-z and 0-9 into one hyphen, cut it to 48 characters, and drop any hyphen at either end.
2. `<skill>` is the slug of the file's `skill_name`; if the file has none, of the `name` in the skill's SKILL.md. If that leaves nothing, it is `eval`.
3. `<label>` is the slug of the entry's `eval_name` (of its `name`, if it has no `eval_name` field). If that leaves nothing, it is the slug of its `id`; if that leaves nothing too, its position in the list as three digits (`001` for the first).
4. If several entries end up with the same case name, the later ones get `-2`, `-3`, ... at the end.

| entry in `csv-summary`'s evals.json | case name |
|---|---|
| `"id": 2` | `csv-summary-2` |
| `"id": 3, "eval_name": "Empty input!"` | `csv-summary-empty-input` |
| `"id": 4, "name": "Odd rows are mentioned"` | `csv-summary-odd-rows-are-mentioned` |
| the first entry, with none of the three | `csv-summary-001` |

**Putting the two together.** The set of tests for a run is every case folder, plus every `evals.json` entry whose case name is not already a case folder. When both exist the folder wins, because it is the newer version: when an old test needs to change (a better prompt, new assertions), write the new version as a case folder with the test's case name, and leave the file alone. If the user asks to move everything over, write one folder per entry with the table above, then ask before removing the file.

---

## history.json

Tracks version progression in Improve mode. Located at workspace root.

```json
{
  "started_at": "2026-01-15T10:30:00Z",
  "skill_name": "pdf",
  "current_best": "v2",
  "iterations": [
    {
      "version": "v0",
      "parent": null,
      "expectation_pass_rate": 0.65,
      "grading_result": "baseline",
      "is_current_best": false
    },
    {
      "version": "v1",
      "parent": "v0",
      "expectation_pass_rate": 0.75,
      "grading_result": "won",
      "is_current_best": false
    },
    {
      "version": "v2",
      "parent": "v1",
      "expectation_pass_rate": 0.85,
      "grading_result": "won",
      "is_current_best": true
    }
  ]
}
```

**Fields:**
- `started_at`: ISO timestamp of when improvement started
- `skill_name`: Name of the skill being improved
- `current_best`: Version identifier of the best performer
- `iterations[].version`: Version identifier (v0, v1, ...)
- `iterations[].parent`: Parent version this was derived from
- `iterations[].expectation_pass_rate`: Pass rate from grading
- `iterations[].grading_result`: "baseline", "won", "lost", or "tie"
- `iterations[].is_current_best`: Whether this is the current best version

---

## grading.json

Output from the grader agent. Located at `<run-dir>/grading.json`.

```json
{
  "expectations": [
    {
      "text": "The output includes the name 'John Smith'",
      "passed": true,
      "evidence": "Found in transcript Step 3: 'Extracted names: John Smith, Sarah Johnson'"
    },
    {
      "text": "The spreadsheet has a SUM formula in cell B10",
      "passed": false,
      "evidence": "No spreadsheet was created. The output was a text file."
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 1,
    "total": 3,
    "pass_rate": 0.67
  },
  "execution_metrics": {
    "tool_calls": {
      "Read": 5,
      "Write": 2,
      "Bash": 8
    },
    "total_tool_calls": 15,
    "total_steps": 6,
    "errors_encountered": 0,
    "output_chars": 12450,
    "transcript_chars": 3200
  },
  "timing": {
    "executor_duration_seconds": 165.0,
    "grader_duration_seconds": 26.0,
    "total_duration_seconds": 191.0
  },
  "claims": [
    {
      "claim": "The form has 12 fillable fields",
      "type": "factual",
      "verified": true,
      "evidence": "Counted 12 fields in field_info.json"
    }
  ],
  "user_notes_summary": {
    "uncertainties": ["Used 2023 data, may be stale"],
    "needs_review": [],
    "workarounds": ["Fell back to text overlay for non-fillable fields"]
  },
  "eval_feedback": {
    "suggestions": [
      {
        "assertion": "The output includes the name 'John Smith'",
        "reason": "A hallucinated document that mentions the name would also pass"
      }
    ],
    "overall": "Assertions check presence but not correctness."
  }
}
```

**Fields:**
- `expectations[]`: Graded expectations with evidence
- `summary`: Aggregate pass/fail counts
- `execution_metrics`: Tool usage and output size (from executor's metrics.json)
- `timing`: Wall clock timing (from timing.json)
- `claims`: Extracted and verified claims from the output
- `user_notes_summary`: Issues flagged by the executor
- `eval_feedback`: (optional) Improvement suggestions for the evals, only present when the grader identifies issues worth raising

---

## metrics.json

Output from the executor agent. Located at `<run-dir>/outputs/metrics.json`.

```json
{
  "tool_calls": {
    "Read": 5,
    "Write": 2,
    "Bash": 8,
    "Edit": 1,
    "Glob": 2,
    "Grep": 0
  },
  "total_tool_calls": 18,
  "total_steps": 6,
  "files_created": ["filled_form.pdf", "field_values.json"],
  "errors_encountered": 0,
  "output_chars": 12450,
  "transcript_chars": 3200
}
```

**Fields:**
- `tool_calls`: Count per tool type
- `total_tool_calls`: Sum of all tool calls
- `total_steps`: Number of major execution steps
- `files_created`: List of output files created
- `errors_encountered`: Number of errors during execution
- `output_chars`: Total character count of output files
- `transcript_chars`: Character count of transcript

---

## timing.json

Wall clock timing for a run. Located at `<run-dir>/timing.json`.

**How to capture:** When a subagent task completes, the task notification includes `total_tokens` and `duration_ms`. Save these immediately — they are not persisted anywhere else and cannot be recovered after the fact.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3,
  "executor_start": "2026-01-15T10:30:00Z",
  "executor_end": "2026-01-15T10:32:45Z",
  "executor_duration_seconds": 165.0,
  "grader_start": "2026-01-15T10:32:46Z",
  "grader_end": "2026-01-15T10:33:12Z",
  "grader_duration_seconds": 26.0
}
```

---

## stages.json

The stages of the skill under test, written once per iteration at `<workspace>/iteration-N/stages.json` before the runs start. Derived from the skill's workflow. Baseline runs use the same list; work that fits no stage goes to `other`.

```json
{
  "stages": [
    {"name": "read-input", "description": "Load and parse the user's files"},
    {"name": "build-report", "description": "Write the report from the parsed data"},
    {"name": "other", "description": "Anything outside the stages above"}
  ]
}
```

- `name`: short kebab-case, unique, the same from one iteration to the next.
- The order is the order the stages normally happen in; the waterfall rows follow it.

---

## Stage markers and the transcript

The executor declares stages inside the tool calls it makes, at no cost: a Bash command starts with the comment line `# stage: collect-stats`; any other tool call is preceded by a text line `stage: collect-stats`; `# stage: end` / `stage: end` marks the end of the last stage. A stage lasts until the next declaration. `scripts/stage_timing.py` reads these from the executor's transcript (JSONL, one message per line, each with an ISO `timestamp`) and splits the wall time into intervals:

- model time: from the previous tool result (or the prompt) to the assistant message, which is thinking plus writing the tool input; split over the stages a message declares in proportion to the text written for each;
- tool time: from the assistant message to its tool result;
- startup (before the first stage), handback (after the last), and unattributed (a tool call with no result);
- host stall: an idle gap between consecutive transcript events longer than 120 seconds (`--stall-threshold`) that overlaps a long gap in at least one other run of the iteration (any configuration). Overlap across independent runs means the cause is outside the skill (a frozen host or harness), so that time is taken out of the stage and booked to `host stall`. A long gap in only one run stays in its stage and is listed in `gaps` as "long single-run gap".

`timing.json` points at the transcript with `transcript_path` (absolute, or relative to the run directory) and/or `agent_id` (looked up under `~/.claude/projects/*/*/subagents/agent-<id>.jsonl`); a `transcript.jsonl` in the run directory is used when neither is set. Marks from older runs (`m <name> start` helper calls or `{"stage": ..., "event": "start"}` lines inside a tool input) still count as declarations; when `stages.jsonl` timestamps exist they only decide how a batched command is split.

---

## stages.jsonl

Legacy and claude.ai fallback, used only when a run has no transcript; its chart is labelled "shell-only marks: model time not attributed". Stage boundary marks, one JSON object per line, appended by the executor to `<run-dir>/stages.jsonl` while it works.

```jsonl
{"stage": "read-input", "event": "start", "t": 1768473000.12}
{"stage": "read-input", "event": "end", "t": 1768473012.8}
{"stage": "build-report", "event": "start", "t": 1768473012.9}
{"stage": "build-report", "event": "end", "t": 1768473041.5}
```

- `event`: `start` or `end`. `t`: epoch seconds as a number (`python3 -c 'import time;print(time.time())'` works on macOS and Linux; `date +%s.%N` does not work on macOS).
- A stage may repeat; its duration is the sum of its intervals. A stage may be nested in or overlap another: each keeps its own time, and the accounted time counts every second once.
- Lines that are not valid, an end without a start, a start without an end and a stage missing from `stages.json` are reported as gaps in `stage_timing.json`; they never stop the benchmark.

---

## stage_timing.json

Written by `scripts/stage_timing.py` (called from `aggregate_benchmark.py`), in two places.

**Per run**, `<run-dir>/stage_timing.json`:

```json
{
  "stages": [
    {"name": "read-input", "start_offset_seconds": 0.0, "duration_seconds": 12.68, "intervals": 1},
    {"name": "build-report", "start_offset_seconds": 12.78, "duration_seconds": 28.6, "intervals": 1}
  ],
  "total_seconds": 45.0,
  "accounted_seconds": 41.28,
  "unaccounted_seconds": 3.72,
  "gaps": []
}
```

- From a transcript the result also has `"source": "transcript"`, and each stage has `model_seconds`, `tool_seconds` (they add up to `duration_seconds`) and `output_tokens` (when the transcript carries usage); the run has `wall_seconds` (the transcript's first to last timestamp, also `total_seconds`), `startup_seconds`, `handback_seconds`, `host_stall_seconds`, `stalls` (a list of `{"start", "end", "seconds", "shared_with_runs"}`, ISO UTC times, `shared_with_runs` counting the other runs whose gap overlaps) and `unattributed_seconds` (also `unaccounted_seconds`). `stages` + `startup` + `handback` + `host stall` + `unattributed` equal `wall_seconds` within one second; this is checked when the file is written. From `stages.jsonl` the result has `"source": "marks"` and none of those.
- `start_offset_seconds` is relative to the run's earliest valid start mark (transcript: the run's first timestamp). `duration_seconds` and `start_offset_seconds` are `null` for a stage with no complete start/end pair.
- `total_seconds` comes from the run's `timing.json` (`total_duration_seconds`, else `duration_ms` / 1000), `null` when absent. `unaccounted_seconds` is the total minus `accounted_seconds` (never below 0), `null` when there is no total.
- `gaps`: plain-text sentences, one per problem found in the marks.

**Per iteration**, `<workspace>/iteration-N/stage_timing.json`, also the `stage_timing` section of `benchmark.json`:

```json
{
  "stages": [{"name": "read-input", "description": "Load and parse the user's files"}],
  "configurations": {
    "with_skill": {
      "runs": 3,
      "runs_total": 3,
      "source": "transcript",
      "stages": {
        "read-input": {
          "duration_seconds": {"mean": 11.0, "stddev": 1.2, "min": 10.0, "max": 12.4},
          "model_seconds": {"mean": 4.0, "stddev": 0.5, "min": 3.5, "max": 4.6},
          "tool_seconds": {"mean": 7.0, "stddev": 0.9, "min": 6.2, "max": 7.8},
          "output_tokens": {"mean": 310.0, "stddev": 20.0, "min": 290.0, "max": 335.0},
          "start_offset_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
          "runs": 3
        }
      },
      "total_seconds": {"mean": 45.0, "stddev": 2.0, "min": 43.0, "max": 47.0},
      "startup_seconds": {"mean": 4.0, "stddev": 0.3, "min": 3.7, "max": 4.3},
      "handback_seconds": {"mean": 2.0, "stddev": 0.2, "min": 1.8, "max": 2.2},
      "host_stall_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
      "unaccounted_seconds": {"mean": 3.7, "stddev": 0.5, "min": 3.2, "max": 4.2}
    }
  },
  "host_stalls": [],
  "gaps": [{"run": "case-one/with_skill/run-2", "issue": "stage build-report has no end mark, so its duration is unknown and left out"}]
}
```

- `source` is `transcript`, `marks` (shell-only marks) or `mixed`, per configuration and, as a top-level field, for the whole section. `model_seconds`, `tool_seconds`, `output_tokens`, `startup_seconds`, `handback_seconds` and `host_stall_seconds` appear only for transcript runs; `host_stalls` lists the distinct stall intervals across runs (`start`, `end`, `seconds`, `runs` = how many runs share it); `unaccounted_seconds` is the unattributed time for them.
- `runs` counts the runs with a transcript or a `stages.jsonl`, `runs_total` all runs of that configuration. Only runs with a complete interval for a stage count toward that stage's stats (`stages.<name>.runs`).
- The section is absent from `benchmark.json` when no run has a transcript or a `stages.jsonl`.
- `<workspace>/iteration-N/waterfall.svg` is the standalone chart of the same means, with the previous iteration (`iteration-(N-1)/stage_timing.json`) as an extra panel when it exists. The viewer's Benchmark tab shows the same chart.

---

## benchmark.json

Output from Benchmark mode. Located at `benchmarks/<timestamp>/benchmark.json`.

```json
{
  "metadata": {
    "skill_name": "pdf",
    "skill_path": "/path/to/pdf",
    "executor_model": "claude-sonnet-4-20250514",
    "analyzer_model": "most-capable-model",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2, 3],
    "runs_per_configuration": 3
  },

  "runs": [
    {
      "eval_id": 1,
      "eval_name": "Ocean",
      "configuration": "with_skill",
      "run_number": 1,
      "result": {
        "pass_rate": 0.85,
        "passed": 6,
        "failed": 1,
        "total": 7,
        "time_seconds": 42.5,
        "tokens": 3800,
        "tool_calls": 18,
        "errors": 0
      },
      "expectations": [
        {"text": "...", "passed": true, "evidence": "..."}
      ],
      "notes": [
        "Used 2023 data, may be stale",
        "Fell back to text overlay for non-fillable fields"
      ]
    }
  ],

  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.85, "stddev": 0.05, "min": 0.80, "max": 0.90},
      "time_seconds": {"mean": 45.0, "stddev": 12.0, "min": 32.0, "max": 58.0},
      "tokens": {"mean": 3800, "stddev": 400, "min": 3200, "max": 4100}
    },
    "without_skill": {
      "pass_rate": {"mean": 0.35, "stddev": 0.08, "min": 0.28, "max": 0.45},
      "time_seconds": {"mean": 32.0, "stddev": 8.0, "min": 24.0, "max": 42.0},
      "tokens": {"mean": 2100, "stddev": 300, "min": 1800, "max": 2500}
    },
    "delta": {
      "pass_rate": "+0.50",
      "time_seconds": "+13.0",
      "tokens": "+1700"
    }
  },

  "notes": [
    "Assertion 'Output is a PDF file' passes 100% in both configurations - may not differentiate skill value",
    "Eval 3 shows high variance (50% ± 40%) - may be flaky or model-dependent",
    "Without-skill runs consistently fail on table extraction expectations",
    "Skill adds 13s average execution time but improves pass rate by 50%"
  ]
}
```

**Fields:**
- `metadata`: Information about the benchmark run
  - `skill_name`: Name of the skill
  - `timestamp`: When the benchmark was run
  - `evals_run`: List of eval names or IDs
  - `runs_per_configuration`: Number of runs of each eval per config (e.g. 3)
- `runs[]`: Individual run results
  - `eval_id`: Eval identifier, a number or a name
  - `eval_name`: Human-readable eval name (used as section header in the viewer)
  - `configuration`: The name of the run's configuration directory, such as `"with_skill"`, `"without_skill"` or `"old_skill"` (the viewer groups runs by this string)
  - `run_number`: Integer run number (1, 2, 3...)
  - `result`: Nested object with `pass_rate`, `passed`, `total`, `time_seconds`, `tokens`, `errors`; `time_seconds` and `tokens` are each `null` when the run recorded no value for it
- `run_summary`: Statistical aggregates per configuration
  - `with_skill` / `without_skill`: Each contains `pass_rate`, `time_seconds`, `tokens` objects with `mean` and `stddev` fields. `time_seconds` and `tokens` cover only the runs that recorded a value, and are `null` when none did
  - `delta`: The first configuration minus the second, as strings like `"+0.50"`, `"+13.0"`, `"+1700"`. All three are `null` when there is only one configuration. `time_seconds` or `tokens` is also `null` when a run of either of the two recorded no value
- `notes`: Freeform observations from the analyzer, and the notes that `aggregate_benchmark.py` writes when a run recorded no time or token count

**Important:** The viewer reads these field names exactly. Using `config` instead of `configuration`, or putting `pass_rate` at the top level of a run instead of nested under `result`, will cause the viewer to show empty/zero values. Always reference this schema when generating benchmark.json manually.

---

## comparison.json

Output from blind comparator. Located at `<grading-dir>/comparison-N.json`.

```json
{
  "winner": "A",
  "reasoning": "Output A provides a complete solution with proper formatting and all required fields. Output B is missing the date field and has formatting inconsistencies.",
  "rubric": {
    "A": {
      "content": {
        "correctness": 5,
        "completeness": 5,
        "accuracy": 4
      },
      "structure": {
        "organization": 4,
        "formatting": 5,
        "usability": 4
      },
      "content_score": 4.7,
      "structure_score": 4.3,
      "overall_score": 9.0
    },
    "B": {
      "content": {
        "correctness": 3,
        "completeness": 2,
        "accuracy": 3
      },
      "structure": {
        "organization": 3,
        "formatting": 2,
        "usability": 3
      },
      "content_score": 2.7,
      "structure_score": 2.7,
      "overall_score": 5.4
    }
  },
  "output_quality": {
    "A": {
      "score": 9,
      "strengths": ["Complete solution", "Well-formatted", "All fields present"],
      "weaknesses": ["Minor style inconsistency in header"]
    },
    "B": {
      "score": 5,
      "strengths": ["Readable output", "Correct basic structure"],
      "weaknesses": ["Missing date field", "Formatting inconsistencies", "Partial data extraction"]
    }
  },
  "expectation_results": {
    "A": {
      "passed": 4,
      "total": 5,
      "pass_rate": 0.80,
      "details": [
        {"text": "Output includes name", "passed": true}
      ]
    },
    "B": {
      "passed": 3,
      "total": 5,
      "pass_rate": 0.60,
      "details": [
        {"text": "Output includes name", "passed": true}
      ]
    }
  }
}
```

---

## analysis.json

Output from post-hoc analyzer. Located at `<grading-dir>/analysis.json`.

```json
{
  "comparison_summary": {
    "winner": "A",
    "winner_skill": "path/to/winner/skill",
    "loser_skill": "path/to/loser/skill",
    "comparator_reasoning": "Brief summary of why comparator chose winner"
  },
  "winner_strengths": [
    "Clear step-by-step instructions for handling multi-page documents",
    "Included validation script that caught formatting errors"
  ],
  "loser_weaknesses": [
    "Vague instruction 'process the document appropriately' led to inconsistent behavior",
    "No script for validation, agent had to improvise"
  ],
  "instruction_following": {
    "winner": {
      "score": 9,
      "issues": ["Minor: skipped optional logging step"]
    },
    "loser": {
      "score": 6,
      "issues": [
        "Did not use the skill's formatting template",
        "Invented own approach instead of following step 3"
      ]
    }
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "instructions",
      "suggestion": "Replace 'process the document appropriately' with explicit steps",
      "expected_impact": "Would eliminate ambiguity that caused inconsistent behavior"
    }
  ],
  "transcript_insights": {
    "winner_execution_pattern": "Read skill -> Followed 5-step process -> Used validation script",
    "loser_execution_pattern": "Read skill -> Unclear on approach -> Tried 3 different methods"
  }
}
```
