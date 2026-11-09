"""Integrity checks for fixtures, deterministic references, and grader edge cases."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from graders.grader import grade_response
from reference.oracle_solver import make_prompt, solve_task

ROOT = Path(__file__).resolve().parent


def load_cases() -> list[tuple[dict, dict]]:
    cases = []
    for task_path in sorted((ROOT / "tasks").glob("task_*.json")):
        task = json.loads(task_path.read_text(encoding="utf-8"))
        ref_path = ROOT / "reference" / f"{task_path.stem}_reference.json"
        reference = json.loads(ref_path.read_text(encoding="utf-8"))
        cases.append((task, reference))
    if len(cases) != 8:
        raise AssertionError(f"expected 8 task definitions; found {len(cases)}")
    return cases


def _reject(candidate: dict | str, reference: dict, metadata: dict, description: str) -> None:
    result = grade_response(candidate, reference, metadata)
    assert not result["passed"], f"grader accepted {description}"


def validate() -> None:
    cases = load_cases()
    checked_oracles = 0
    checked_prompts = 0
    rejected_mutations = 0
    rows = []

    for task, reference in cases:
        metadata = task.get("metadata", {})
        assert task["prompt"] == make_prompt(task), f"{task['task_id']} prompt is stale"
        checked_prompts += 1

        regenerated = solve_task(task)
        assert regenerated == reference, f"{task['task_id']} stored reference differs from the current oracle"
        checked_oracles += 1

        result = grade_response(reference, reference, metadata)
        assert result["passed"] and result["total_score"] == 1.0, f"{task['task_id']} reference failed its grader: {result}"
        fenced = f"```json\n{json.dumps(reference)}\n```"
        result = grade_response(fenced, reference, metadata)
        assert result["passed"], f"{task['task_id']} exact fenced JSON failed: {result}"
        wrapped = f"Reasoning text\n{fenced}"
        result = grade_response(wrapped, reference, metadata)
        assert not result["passed"] and result["format_compliant"] is False and result["total_score"] == 1.0, f"{task['task_id']} wrapped response should receive semantic credit but fail strict format"

        def check(candidate: dict | str, description: str) -> None:
            nonlocal rejected_mutations
            _reject(candidate, reference, metadata, description)
            rejected_mutations += 1

        # Ledger arithmetic and complete reconciliation-list matching.
        bad = copy.deepcopy(reference)
        bad["ledger_balances_usd"]["net_cash_collected"] = round(float(bad["ledger_balances_usd"]["net_cash_collected"]) + 0.05, 2)
        check(bad, "$0.05 balance mutation")

        bad = copy.deepcopy(reference)
        bad["ledger_balances_usd"]["net_cash_collected"] = round(float(bad["ledger_balances_usd"]["net_cash_collected"]) + 0.01, 2)
        check(bad, "one-cent balance mutation")

        missing_gold = copy.deepcopy(reference)
        missing_output = copy.deepcopy(reference)
        if missing_gold["reconciling_items"]:
            missing_output["reconciling_items"].pop()
        else:
            missing_gold["reconciling_items"].append({
                "event_id": "evt_validation_expected", "category": "POLICY_VIOLATION_HOLD", "amount_impact_usd": 1.00,
            })
        result = grade_response(missing_output, missing_gold, metadata)
        assert not result["passed"] and result["total_score"] < 1.0, f"{task['task_id']} accepted a missing reconciling item"
        rejected_mutations += 1

        bad = copy.deepcopy(reference)
        if bad["reconciling_items"]:
            bad["reconciling_items"][0]["amount_impact_usd"] = round(bad["reconciling_items"][0]["amount_impact_usd"] + 0.01, 2)
        else:
            bad["reconciling_items"].append({
                "event_id": "evt_hallucinated", "category": "COUPON_FLOOR_CAPPED", "amount_impact_usd": 1.23,
            })
        check(bad, "one-cent or extra reconciling-item mutation")

        # Exact output contract: task identity, field set, and unique ID arrays.
        bad = copy.deepcopy(reference)
        bad["account_id"] = "wrong-account"
        check(bad, "wrong account ID")

        bad = copy.deepcopy(reference)
        bad["audit_period_end"] = "2099-12-31T00:00:00Z"
        check(bad, "wrong audit cutoff")

        bad = copy.deepcopy(reference)
        bad["unexpected_top_level_key"] = True
        check(bad, "unexpected top-level key")

        bad = copy.deepcopy(reference)
        ids = bad["ignored_event_ids"]
        ids.append(ids[0] if ids else "evt_duplicate")
        if not reference["ignored_event_ids"]:
            ids.append("evt_duplicate")
        check(bad, "duplicate ignored event ID")

        bad = copy.deepcopy(reference)
        bad["ignored_event_ids"].append("evt_unexpected")
        check(bad, "unexpected ignored event ID")

        bad = copy.deepcopy(reference)
        bad["ledger_balances_usd"]["net_cash_collected"] += 0.001
        check(bad, "sub-cent ledger amount")

        check(json.dumps(reference) + "\n" + json.dumps(reference), "multiple candidate answer objects")
        serialized = json.dumps(reference)
        account_key = serialized.index('"account_id":')
        check(serialized[:account_key] + '"account_id":"duplicate",' + serialized[account_key:], "duplicate JSON object key")

        # Status and parser controls.
        bad = copy.deepcopy(reference)
        bad["final_subscription_status"] = "PAST_DUE" if reference["final_subscription_status"] != "PAST_DUE" else "ACTIVE"
        check(bad, "wrong subscription status")
        check("{not valid JSON", "malformed JSON")

        rows.append((task["task_id"], "PASS", "14/14 rejected"))

    print("Task                                      Prompt   Oracle   Grader edge cases")
    print("-" * 82)
    for task_id, status, mutation_status in rows:
        print(f"{task_id:<41} PASS     PASS     {mutation_status}")
    print("-" * 82)
    print(f"Prompt fixtures match generator: {checked_prompts}/8")
    print(f"Stored references match regenerated oracle: {checked_oracles}/8")
    print(f"Invalid-output mutations rejected: {rejected_mutations}/{len(cases) * 14}")
    print("Note: regeneration confirms consistency with this oracle; it is not independent accounting review.")


if __name__ == "__main__":
    validate()
