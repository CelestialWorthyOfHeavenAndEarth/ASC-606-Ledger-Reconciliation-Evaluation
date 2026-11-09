"""Deterministic JSON extraction, schema validation, and scoring."""
from __future__ import annotations

import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from typing import Any

BALANCE_FIELDS = (
    "net_cash_collected", "customer_wallet_balance", "recognized_revenue",
    "deferred_revenue", "tax_liability", "fx_realized_gain_loss",
)
REQUIRED_TOP_LEVEL = (
    "account_id", "audit_period_end", "ledger_balances_usd", "reconciling_items",
    "ignored_event_ids", "final_subscription_status",
)
BALANCE_KEYS = frozenset(BALANCE_FIELDS)
ITEM_KEYS = frozenset({"event_id", "category", "amount_impact_usd"})
CENT = Decimal("0.01")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
VALID_CATEGORIES = {
    "DUPLICATE_IGNORED", "RETROACTIVE_PRORATION", "COUPON_FLOOR_CAPPED",
    "COOLING_OFF_REFUND", "FX_SETTLEMENT_DIFF", "CHARGEBACK_FEE_UNRECOVERED",
    "LATE_USAGE_REBILL", "POLICY_VIOLATION_HOLD",
}


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return result if result.is_finite() else None


def extract_json(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise ValueError("model response must be a JSON string or object")
    text = raw.strip()
    if not text:
        raise ValueError("response is empty")
    try:
        value = json.loads(text, object_pairs_hook=_unique_object)
    except json.JSONDecodeError:
        fenced = re.fullmatch(r"```(?:json)?[ \t]*\r?\n?(.*?)\r?\n?```", text, flags=re.IGNORECASE | re.DOTALL)
        if fenced is None:
            raise ValueError("response must contain exactly one JSON object and no surrounding text")
        try:
            value = json.loads(fenced.group(1).strip(), object_pairs_hook=_unique_object)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError("fenced response does not contain valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("response JSON must be one object")
    return value


def _extract_for_scoring(raw: str | dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Return a single answer object and whether the whole response obeys the format contract."""
    if isinstance(raw, dict):
        return raw, True
    try:
        return extract_json(raw), True
    except ValueError as strict_error:
        if not isinstance(raw, str):
            raise
        decoder = json.JSONDecoder(object_pairs_hook=_unique_object)
        candidates: list[dict[str, Any]] = []
        cursor = 0
        while cursor < len(raw):
            start = raw.find("{", cursor)
            if start < 0:
                break
            try:
                value, end = decoder.raw_decode(raw, start)
            except json.JSONDecodeError:
                cursor = start + 1
                continue
            if isinstance(value, dict) and set(REQUIRED_TOP_LEVEL).issubset(value):
                candidates.append(value)
            cursor = max(end, start + 1)
        if len(candidates) == 1:
            return candidates[0], False
        if len(candidates) > 1:
            raise ValueError("response contains multiple candidate answer objects") from strict_error
        raise strict_error


def _numeric_cents(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    result = _decimal(value)
    if result is None:
        return None
    try:
        return result if result == result.quantize(CENT, rounding=ROUND_HALF_EVEN) else None
    except InvalidOperation:
        return None


def _validate(obj: dict[str, Any], reference: dict[str, Any]) -> list[str]:
    problems = [f"missing top-level key: {key}" for key in REQUIRED_TOP_LEVEL if key not in obj]
    extra_top = set(obj) - set(REQUIRED_TOP_LEVEL)
    if extra_top:
        problems.append(f"unexpected top-level key(s): {', '.join(sorted(extra_top))}")
    if "ledger_balances_usd" in obj:
        balances = obj["ledger_balances_usd"]
        if not isinstance(balances, dict):
            problems.append("ledger_balances_usd must be an object")
        else:
            extra_balances = set(balances) - BALANCE_KEYS
            if extra_balances:
                problems.append(f"unexpected ledger balance key(s): {', '.join(sorted(extra_balances))}")
            for field in BALANCE_FIELDS:
                if field not in balances:
                    problems.append(f"missing balance: {field}")
                elif _numeric_cents(balances[field]) is None:
                    problems.append(f"balance {field} must be a finite USD amount in whole cents")
    if "reconciling_items" in obj:
        items = obj["reconciling_items"]
        if not isinstance(items, list):
            problems.append("reconciling_items must be an array")
        else:
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    problems.append(f"reconciling_items[{i}] must be an object")
                    continue
                extra_item_keys = set(item) - ITEM_KEYS
                missing_item_keys = ITEM_KEYS - set(item)
                if extra_item_keys:
                    problems.append(f"reconciling_items[{i}] has unexpected key(s): {', '.join(sorted(extra_item_keys))}")
                if missing_item_keys:
                    problems.append(f"reconciling_items[{i}] is missing key(s): {', '.join(sorted(missing_item_keys))}")
                if not isinstance(item.get("event_id"), str):
                    problems.append(f"reconciling_items[{i}].event_id must be a string")
                if item.get("category") not in VALID_CATEGORIES:
                    problems.append(f"reconciling_items[{i}].category is invalid")
                if _numeric_cents(item.get("amount_impact_usd")) is None:
                    problems.append(f"reconciling_items[{i}].amount_impact_usd must be a finite USD amount in whole cents")
    if "ignored_event_ids" in obj and (not isinstance(obj["ignored_event_ids"], list) or not all(isinstance(x, str) for x in obj["ignored_event_ids"])):
        problems.append("ignored_event_ids must be an array of strings")
    elif "ignored_event_ids" in obj and len(obj["ignored_event_ids"]) != len(set(obj["ignored_event_ids"])):
        problems.append("ignored_event_ids must not contain duplicate values")
    if "final_subscription_status" in obj and (not isinstance(obj["final_subscription_status"], str) or obj["final_subscription_status"].strip().upper() not in {"ACTIVE", "CANCELED", "PAST_DUE", "SUSPENDED_DISPUTE"}):
        problems.append("final_subscription_status is invalid")
    if "account_id" in obj and not isinstance(obj["account_id"], str):
        problems.append("account_id must be a string")
    if "audit_period_end" in obj:
        value = obj["audit_period_end"]
        if not isinstance(value, str):
            problems.append("audit_period_end must be a string")
        elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
            problems.append("audit_period_end must use YYYY-MM-DDTHH:MM:SSZ")
        else:
            try:
                datetime.fromisoformat(value[:-1] + "+00:00")
            except ValueError:
                problems.append("audit_period_end is not a valid UTC timestamp")
    if isinstance(obj.get("account_id"), str) and obj["account_id"] != reference.get("account_id"):
        problems.append("account_id does not match the task")
    if isinstance(obj.get("audit_period_end"), str) and obj["audit_period_end"] != reference.get("audit_period_end"):
        problems.append("audit_period_end does not match the task")
    return problems


def _items_f1(predicted: list[dict[str, Any]], expected: list[dict[str, Any]]) -> tuple[float, list[dict[str, Any]], list[dict[str, Any]]]:
    unmatched = list(expected)
    extras: list[dict[str, Any]] = []
    matched = 0
    for item in predicted:
        amount = _decimal(item.get("amount_impact_usd"))
        found = None
        if amount is not None:
            for index, gold in enumerate(unmatched):
                gold_amount = _decimal(gold.get("amount_impact_usd"))
                if (item.get("event_id") == gold.get("event_id")
                        and item.get("category") == gold.get("category")
                        and gold_amount is not None
                        and amount == amount.quantize(CENT, rounding=ROUND_HALF_EVEN)
                        and gold_amount == gold_amount.quantize(CENT, rounding=ROUND_HALF_EVEN)
                        and amount.quantize(CENT, rounding=ROUND_HALF_EVEN)
                                == gold_amount.quantize(CENT, rounding=ROUND_HALF_EVEN)):
                    found = index
                    break
        if found is None:
            extras.append(item)
        else:
            unmatched.pop(found)
            matched += 1
    predicted_n = len(predicted)
    expected_n = len(expected)
    precision = matched / predicted_n if predicted_n else (1.0 if expected_n == 0 else 0.0)
    recall = matched / expected_n if expected_n else (1.0 if predicted_n == 0 else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return f1, extras, unmatched


def grade_response(raw_response: str | dict[str, Any], reference: dict[str, Any], task_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Score a model response. Returns a JSON-serializable breakdown."""
    task_metadata = task_metadata or {}
    format_compliant = False
    try:
        candidate, format_compliant = _extract_for_scoring(raw_response)
    except ValueError as exc:
        return {
            "passed": False,
            "total_score": 0.0,
            "dimension_scores": {"ledger_balances": 0.0, "reconciling_items": 0.0, "ignored_event_ids": 0.0, "final_status": 0.0},
            "failure_tags": ["JSON_FORMAT_ERROR"],
            "format_compliant": False,
            "errors": [str(exc)],
            "discrepancies": {},
        }
    schema_errors = _validate(candidate, reference)
    if schema_errors:
        tags = {"OUTPUT_SCHEMA_ERROR"}
        if any(error.startswith("account_id does not match") for error in schema_errors):
            tags.add("OUTPUT_IDENTITY_MISMATCH")
        if any(error.startswith("audit_period_end does not match") for error in schema_errors):
            tags.add("OUTPUT_PERIOD_MISMATCH")
        return {
            "passed": False,
            "total_score": 0.0,
            "dimension_scores": {"ledger_balances": 0.0, "reconciling_items": 0.0, "ignored_event_ids": 0.0, "final_status": 0.0},
            "failure_tags": sorted(tags),
            "format_compliant": format_compliant,
            "errors": schema_errors,
            "discrepancies": {},
        }

    actual_balances = candidate["ledger_balances_usd"]
    expected_balances = reference["ledger_balances_usd"]
    balance_matches: dict[str, bool] = {}
    balance_deltas: dict[str, float] = {}
    for field in BALANCE_FIELDS:
        actual = _decimal(actual_balances[field])
        expected = _decimal(expected_balances[field])
        delta = actual - expected
        balance_deltas[field] = float(delta)
        balance_matches[field] = delta == 0
    balance_score_raw = sum(balance_matches.values()) / len(BALANCE_FIELDS)

    expected_items = reference.get("reconciling_items", [])
    actual_items = candidate["reconciling_items"]
    item_f1, extra_items, missing_items = _items_f1(actual_items, expected_items)

    actual_ignored = set(candidate["ignored_event_ids"])
    expected_ignored = set(reference.get("ignored_event_ids", []))
    ignored_precision = len(actual_ignored & expected_ignored) / len(actual_ignored) if actual_ignored else (1.0 if not expected_ignored else 0.0)
    ignored_recall = len(actual_ignored & expected_ignored) / len(expected_ignored) if expected_ignored else (1.0 if not actual_ignored else 0.0)
    ignored_f1 = 2 * ignored_precision * ignored_recall / (ignored_precision + ignored_recall) if ignored_precision + ignored_recall else 0.0
    ignored_exact = actual_ignored == expected_ignored

    status_matches = candidate["final_subscription_status"].strip().upper() == reference["final_subscription_status"].strip().upper()
    dimensions = {
        "ledger_balances": round(balance_score_raw * 0.50, 6),
        "reconciling_items": round(item_f1 * 0.25, 6),
        "ignored_event_ids": round(ignored_f1 * 0.15, 6),
        "final_status": 0.10 if status_matches else 0.0,
    }
    total = round(sum(dimensions.values()), 6)
    balance_exact = all(balance_matches.values())
    passed = format_compliant and balance_exact and item_f1 == 1.0 and ignored_exact and status_matches

    tags: set[str] = set()
    if not format_compliant:
        tags.add("OUTPUT_FORMAT_VIOLATION")
    if extra_items:
        tags.add("EXTRA_RECONCILIATION_ITEM")
    if missing_items:
        tags.add("MISSING_RECONCILIATION_ITEM")
    if actual_ignored != expected_ignored:
        tags.add("IGNORED_EVENT_ID_MISMATCH")
    if not balance_exact:
        tags.add("LEDGER_BALANCE_MISMATCH")
    if not status_matches:
        tags.add("STATUS_MISMATCH")

    return {
        "passed": passed,
        "total_score": total,
        "dimension_scores": dimensions,
        "failure_tags": sorted(tags),
        "format_compliant": format_compliant,
        "errors": [],
        "discrepancies": {
            "balance_matches": balance_matches,
            "balance_deltas_usd": balance_deltas,
            "extra_reconciling_items": extra_items,
            "missing_reconciling_items": missing_items,
            "ignored_event_ids_missing": sorted(expected_ignored - actual_ignored),
            "ignored_event_ids_extra": sorted(actual_ignored - expected_ignored),
            "status_matches": status_matches,
        },
    }
