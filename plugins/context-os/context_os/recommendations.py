#!/usr/bin/env python3
"""
Multi-variant recommendation generator.

For each detected waste category in a scored session, emit 2-4 distinct
recommendation variants representing different possible root causes, each
with its own confidence. Variants are ranked and then adjusted based on
prior user feedback (accepted / rejected / known) for matching pattern
signatures. Purely stdlib.
"""

from __future__ import annotations

from typing import Any

from context_os.feedback_store import (
    history_by_signature,
    make_rec_id,
    make_signature,
)

# Variant templates per category. Each variant has a stable `variant` key
# (used in rec_id), a title, a rationale sketch, a suggested_action, and a
# baseline confidence. Baselines are rebalanced per session based on the
# dominant tool / evidence.
VARIANTS: dict[str, list[dict]] = {
    "tool_hammering": [
        {
            "variant": "batch_calls",
            "title": "Batch repeated tool calls into one message",
            "rationale": "Multiple calls to the same tool in sequence are often independent and can be issued in parallel in a single assistant turn.",
            "suggested_action": "Group the repeated calls into one message; the harness will parallelize them.",
            "base_confidence": 0.70,
        },
        {
            "variant": "legitimate_loop_cache",
            "title": "Loop may be legitimate — cache intermediate results instead",
            "rationale": "If call N depends on the output of N-1 (e.g., pagination, graph traversal), batching is impossible. Focus on caching or memoizing the result.",
            "suggested_action": "Persist intermediate results to a scratch file or knowledge node so reruns don't repeat the loop.",
            "base_confidence": 0.35,
        },
        {
            "variant": "use_glob_grep",
            "title": "Replace repeated Read calls with Glob/Grep",
            "rationale": "Individual Read calls over many files are typically answerable by a single Glob or Grep with a pattern.",
            "suggested_action": "Rewrite the exploratory reads as one Grep or Glob invocation.",
            "base_confidence": 0.55,
        },
        {
            "variant": "delegate_agent",
            "title": "Delegate to a subagent for exploration",
            "rationale": "High tool-call counts on open-ended exploration keep bloat in the main context; a subagent returns only a summary.",
            "suggested_action": "Invoke a search/explore agent instead of hammering tools in the main thread.",
            "base_confidence": 0.45,
        },
    ],
    "tool_pollution": [
        {
            "variant": "disable_unused_mcp",
            "title": "Disable unused MCP servers",
            "rationale": "Every registered MCP tool consumes system-prompt tokens even when unused; a high overall tool-call count often correlates with a cluttered toolbelt.",
            "suggested_action": "Prune MCP servers you don't use in this project via settings.json.",
            "base_confidence": 0.55,
        },
        {
            "variant": "batch_reads",
            "title": "Batch file reads and searches",
            "rationale": "Multiple small reads/searches inflate total tool-call volume without proportional signal.",
            "suggested_action": "Consolidate reads into one message or one Grep.",
            "base_confidence": 0.60,
        },
        {
            "variant": "narrower_scope",
            "title": "Narrow the task scope",
            "rationale": "Very high tool volume is often a symptom of attempting too much in one session.",
            "suggested_action": "Split the work into multiple focused sessions.",
            "base_confidence": 0.40,
        },
    ],
    "thinking_waste": [
        {
            "variant": "disable_for_routine",
            "title": "Disable extended thinking for routine edits",
            "rationale": "Extended thinking paired with tiny responses indicates the thinking budget is not justified by the output.",
            "suggested_action": "Turn off extended thinking for this class of task.",
            "base_confidence": 0.65,
        },
        {
            "variant": "reserve_for_planning",
            "title": "Reserve thinking for planning-only turns",
            "rationale": "Thinking pays off for planning and complex reasoning, not for mechanical tool sequences.",
            "suggested_action": "Enable thinking only on the first planning turn; disable once execution starts.",
            "base_confidence": 0.45,
        },
        {
            "variant": "lower_budget",
            "title": "Lower the thinking token budget",
            "rationale": "A smaller budget may deliver the same planning benefit at lower cost.",
            "suggested_action": "Reduce thinking_budget in settings.",
            "base_confidence": 0.35,
        },
    ],
    "context_bloat": [
        {
            "variant": "compact_now",
            "title": "Run /compact mid-session",
            "rationale": "Large context with low cache reuse indicates drift; /compact resets working set while preserving summary.",
            "suggested_action": "Run /compact when the conversation has accumulated >100K tokens of cache creation.",
            "base_confidence": 0.70,
        },
        {
            "variant": "split_sessions",
            "title": "Split into smaller focused sessions",
            "rationale": "Long single sessions accumulate context that is mostly irrelevant to each sub-task.",
            "suggested_action": "Start a fresh session for each distinct goal.",
            "base_confidence": 0.55,
        },
        {
            "variant": "trim_inputs",
            "title": "Trim large file reads",
            "rationale": "Reading whole large files inflates context when only a range is needed.",
            "suggested_action": "Use Read with offset/limit or Grep to extract only relevant lines.",
            "base_confidence": 0.40,
        },
    ],
    "cache_inefficiency": [
        {
            "variant": "stable_system_prompt",
            "title": "Keep system prompt stable across turns",
            "rationale": "Low cache reuse usually means the prefix is being invalidated between turns.",
            "suggested_action": "Avoid randomizing tool descriptions or timestamps in the system prompt.",
            "base_confidence": 0.60,
        },
        {
            "variant": "stable_tool_order",
            "title": "Keep tool list and order stable",
            "rationale": "Changing the set or order of tools between turns invalidates the cache prefix.",
            "suggested_action": "Register tools once at session start; don't toggle MCP servers mid-session.",
            "base_confidence": 0.45,
        },
        {
            "variant": "short_session_ok",
            "title": "Short session — low reuse may be normal",
            "rationale": "In very short sessions there's not enough opportunity for the cache to pay off.",
            "suggested_action": "Ignore if the session was intentionally short.",
            "base_confidence": 0.25,
        },
    ],
    "compaction_absence": [
        {
            "variant": "add_compact",
            "title": "Add /compact to your workflow",
            "rationale": "Sessions longer than 45-60 minutes benefit from at least one compaction.",
            "suggested_action": "Run /compact at natural task boundaries.",
            "base_confidence": 0.70,
        },
        {
            "variant": "auto_compact_setting",
            "title": "Enable automatic compaction",
            "rationale": "For consistently long sessions, manual compaction is easy to forget.",
            "suggested_action": "Configure auto-compaction in settings.json.",
            "base_confidence": 0.50,
        },
        {
            "variant": "shorter_sessions",
            "title": "Use shorter sessions instead of compacting",
            "rationale": "If each subtask is independent, /compact is less useful than just starting fresh.",
            "suggested_action": "End the session at task boundaries rather than compacting.",
            "base_confidence": 0.40,
        },
    ],
    "interruption_loops": [
        {
            "variant": "clearer_prompts",
            "title": "Write clearer prompts upfront",
            "rationale": "Frequent interruptions often indicate the initial prompt underspecified constraints.",
            "suggested_action": "Use a short spec template (goal, constraints, done-criteria) at session start.",
            "base_confidence": 0.55,
        },
        {
            "variant": "todowrite",
            "title": "Use TodoWrite for shared task state",
            "rationale": "Interruption loops often re-explain the same plan; externalizing it reduces churn.",
            "suggested_action": "Maintain an explicit TODO list the assistant updates.",
            "base_confidence": 0.45,
        },
        {
            "variant": "scope_down",
            "title": "Reduce scope per session",
            "rationale": "Large scope invites corrective interrupts.",
            "suggested_action": "Split work into sessions with single, testable outcomes.",
            "base_confidence": 0.40,
        },
    ],
    "parallel_sprawl": [
        {
            "variant": "consolidate",
            "title": "Consolidate into one session",
            "rationale": "Concurrent sessions on the same project duplicate setup cost and context warmup.",
            "suggested_action": "Work in one terminal window per project at a time.",
            "base_confidence": 0.60,
        },
        {
            "variant": "separate_agents",
            "title": "Separate intentional parallel work by agent",
            "rationale": "If parallelism is deliberate (e.g., independent features), use distinct agents with explicit handoff.",
            "suggested_action": "Route parallel streams through the autonomous agents plugin rather than ad-hoc terminals.",
            "base_confidence": 0.35,
        },
    ],
}


def _top_tool_names(session: dict, k: int = 3) -> list[str]:
    tc = session.get("tool_counts") or session.get("tool_breakdown") or {}
    if not isinstance(tc, dict):
        return []
    return [name for name, _ in sorted(tc.items(), key=lambda x: -x[1])[:k]]


def _rebalance(category: str, variant: dict, session: dict) -> float:
    """Nudge baseline confidence based on session-specific signals."""
    conf = variant["base_confidence"]
    top = _top_tool_names(session, k=1)
    top_name = (top[0] if top else "").lower()
    vname = variant["variant"]
    duration = session.get("duration_minutes", 0) or 0
    tool_counts = session.get("tool_counts") or session.get("tool_breakdown") or {}

    if category == "tool_hammering":
        if vname == "use_glob_grep" and top_name in ("read",):
            conf += 0.15
        if vname == "batch_calls" and top_name in ("bash", "read", "edit"):
            conf += 0.10
        if vname == "legitimate_loop_cache" and top_name in ("webfetch", "grep"):
            conf += 0.05
    elif category == "tool_pollution":
        mcp = sum(
            c for n, c in (tool_counts or {}).items()
            if isinstance(n, str) and "mcp" in n.lower()
        )
        if vname == "disable_unused_mcp" and mcp > 10:
            conf += 0.20
    elif category == "compaction_absence":
        if vname == "add_compact" and duration > 120:
            conf += 0.15
        if vname == "shorter_sessions" and duration < 60:
            conf += 0.10
    elif category == "context_bloat":
        if vname == "compact_now" and duration > 120:
            conf += 0.10
    elif category == "cache_inefficiency":
        if vname == "short_session_ok" and duration < 15:
            conf += 0.20

    return max(0.0, min(1.0, conf))


def _apply_feedback(
    variant_entry: dict,
    signature: str,
    category: str,
) -> dict:
    """Down-weight or boost a variant based on prior user feedback for the same signature."""
    history = history_by_signature(signature)
    if not history:
        return variant_entry

    # Feedback targets the same (category, variant) combination when possible.
    same_cat = [h for h in history if h.get("category") == category]
    rejected = sum(1 for h in same_cat if h.get("status") == "rejected")
    known = sum(1 for h in same_cat if h.get("status") == "known")
    accepted = sum(1 for h in same_cat if h.get("status") == "accepted")

    v = dict(variant_entry)
    delta = 0.0
    if rejected:
        delta -= min(0.35, 0.12 * rejected)
    if known:
        delta -= min(0.5, 0.20 * known)
    if accepted:
        delta += min(0.20, 0.08 * accepted)

    if known >= 2:
        v["_suppressed"] = True

    v["confidence"] = max(0.0, min(1.0, v["confidence"] + delta))
    v["feedback_seen"] = {
        "accepted": accepted,
        "rejected": rejected,
        "known": known,
    }
    return v


def generate_recommendations_for_session(session: dict) -> list[dict]:
    """
    Produce a ranked list of recommendations for one scored session.

    `session` should be a scored-session dict as produced by analyze.build_spec
    (i.e. an entry from spec["sessions"]). Falls back gracefully if keys are
    missing.
    """
    session_id = session.get("session_id", "")
    waste_scores = session.get("waste_scores") or {}
    evidence = session.get("waste_evidence") or {}
    tool_breakdown = session.get("tool_breakdown") or session.get("tool_counts") or {}
    top_tools = [name for name, _ in sorted(tool_breakdown.items(), key=lambda x: -x[1])[:3]]

    out: list[dict] = []
    for category, score in (waste_scores or {}).items():
        if not score or score <= 0:
            continue
        variants = VARIANTS.get(category)
        if not variants:
            continue
        signature = make_signature(category, top_tools)

        for v in variants:
            rec_id = make_rec_id(session_id, category, v["variant"])
            conf = _rebalance(category, v, session)
            # Category severity acts as a multiplier on all variants in this category.
            severity = score / 100.0
            conf = max(0.05, min(1.0, conf * (0.5 + 0.5 * severity)))

            ev = evidence.get(category) or {}
            entry = {
                "id": rec_id,
                "session_id": session_id,
                "category": category,
                "variant": v["variant"],
                "signature": signature,
                "title": v["title"],
                "rationale": v["rationale"],
                "suggested_action": v["suggested_action"],
                "confidence": round(conf, 3),
                "evidence": {
                    "category_score": score,
                    "finding": ev.get("finding", ""),
                    "top_tools": dict(sorted(tool_breakdown.items(), key=lambda x: -x[1])[:5]),
                },
            }
            entry = _apply_feedback(entry, signature, category)
            if entry.pop("_suppressed", False):
                continue
            out.append(entry)

    out.sort(key=lambda r: (-r["confidence"], r["category"], r["variant"]))
    return out


def generate_from_spec(spec: dict) -> dict[str, list[dict]]:
    """Given an analyze.py spec dict, return {session_id: [recs...]}."""
    result: dict[str, list[dict]] = {}
    for s in spec.get("sessions", []):
        sid = s.get("session_id", "")
        if not sid:
            continue
        result[sid] = generate_recommendations_for_session(s)
    return result
