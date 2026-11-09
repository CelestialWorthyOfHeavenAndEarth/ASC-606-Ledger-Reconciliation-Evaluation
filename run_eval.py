"""Concurrent multi-model evaluation runner with deterministic grading."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from graders.grader import grade_response

ROOT = Path(__file__).resolve().parent
DEFAULT_MODELS = "nvidia/nemotron-3.5-lightning:free,nvidia/nemotron-3.5-super-vl:free,dots-studio/dots-3-note-preview:free,xingchen-agi/xing4.0-29b-a4b:free,cohere/north-mini-code:free"
DEFAULT_TASKS = [
    "task_01_idempotency_ooo", "task_02_retro_proration_cooling", "task_03_coupon_floor_tax_cap",
    "task_04_fx_chargeback_reversal", "task_05_tiered_usage_retro_credit", "task_06_leap_year_dst_cutover",
    "task_07_negative_control_clean_audit", "task_08_asc606_multi_rule_cascade",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-") or "model"


def load_inputs(task_filters: list[str] | None) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    cases = []
    for task_id in DEFAULT_TASKS:
        if task_filters and not any(task_id == f or task_id.startswith(f) for f in task_filters):
            continue
        task = json.loads((ROOT / "tasks" / f"{task_id}.json").read_text(encoding="utf-8"))
        reference = json.loads((ROOT / "reference" / f"{task_id}_reference.json").read_text(encoding="utf-8"))
        cases.append((task, reference))
    if not cases:
        raise ValueError("task filter matched no tasks")
    return cases


def _http_json(url: str, headers: dict[str, str], body: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={**headers, "Content-Type": "application/json"}, method="POST")
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1200]
            last_error = RuntimeError(f"HTTP {exc.code}: {detail}")
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == 2:
                break
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"provider request failed after retries: {last_error}")


def _model_route(model_id: str) -> tuple[str, str]:
    prefix, sep, rest = model_id.partition("/")
    if sep and prefix.lower() in {"openai", "anthropic", "google", "gemini", "meta-llama", "mistral", "deepseek"}:
        provider = "google" if prefix == "gemini" else prefix
        return provider, rest
    return "openai", model_id


def call_model(model_id: str, prompt: str, temperature: float, max_tokens: int = 4096,
               disable_reasoning: bool = False) -> tuple[str, dict[str, Any], float | None, str]:
    """Returns raw text, usage, provider reported cost, and provider name."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        from openai import OpenAI
        client = OpenAI(api_key=openrouter_key, base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))
        extra_body = {"usage": {"include": True}}
        if disable_reasoning:
            extra_body["reasoning"] = {"enabled": False}
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body,
        )
        raw = response.choices[0].message.content or ""
        usage_obj = response.usage
        usage = {
            "input_tokens": getattr(usage_obj, "prompt_tokens", None),
            "output_tokens": getattr(usage_obj, "completion_tokens", None),
            "total_tokens": getattr(usage_obj, "total_tokens", None),
        } if usage_obj else {}
        cost = None
        if usage_obj is not None:
            cost = getattr(usage_obj, "cost", None)
        return raw, usage, float(cost) if cost is not None else None, "openrouter"

    provider, native_model = _model_route(model_id)
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(f"{model_id}: set OPENAI_API_KEY or OPENROUTER_API_KEY")
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
        response = client.chat.completions.create(model=native_model, messages=[{"role": "user", "content": prompt}], temperature=temperature, max_tokens=max_tokens)
        raw = response.choices[0].message.content or ""
        usage_obj = response.usage
        usage = {"input_tokens": getattr(usage_obj, "prompt_tokens", None), "output_tokens": getattr(usage_obj, "completion_tokens", None), "total_tokens": getattr(usage_obj, "total_tokens", None)} if usage_obj else {}
        return raw, usage, None, "openai"

    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(f"{model_id}: set ANTHROPIC_API_KEY or OPENROUTER_API_KEY")
        data = _http_json("https://api.anthropic.com/v1/messages", {
            "x-api-key": api_key, "anthropic-version": "2023-06-01",
        }, {"model": native_model, "max_tokens": max_tokens, "temperature": temperature, "messages": [{"role": "user", "content": prompt}]})
        raw = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        usage = data.get("usage", {})
        usage = {"input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"), "total_tokens": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)}
        return raw, usage, None, "anthropic"

    if provider == "google":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(f"{model_id}: set GEMINI_API_KEY or OPENROUTER_API_KEY")
        encoded_model = urllib.parse.quote(native_model, safe="-")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{encoded_model}:generateContent?key={urllib.parse.quote(api_key)}"
        data = _http_json(url, {}, {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}})
        candidates = data.get("candidates", [])
        raw = "".join(part.get("text", "") for part in (candidates[0].get("content", {}).get("parts", []) if candidates else []))
        metadata = data.get("usageMetadata", {})
        usage = {"input_tokens": metadata.get("promptTokenCount"), "output_tokens": metadata.get("candidatesTokenCount"), "total_tokens": metadata.get("totalTokenCount")}
        return raw, usage, None, "google"

    raise RuntimeError(f"{model_id}: native provider '{provider}' is not supported; use OpenRouter")


def estimate_cost(model_id: str, usage: dict[str, Any], provider_cost: float | None, dry_run: bool = False) -> tuple[float | None, str]:
    if dry_run:
        return 0.0, "simulated; no API request"
    if provider_cost is not None:
        return round(provider_cost, 8), "provider-reported usage cost"
    input_rate = os.getenv("INPUT_PRICE_USD_PER_MILLION")
    output_rate = os.getenv("OUTPUT_PRICE_USD_PER_MILLION")
    if input_rate and output_rate and usage.get("input_tokens") is not None and usage.get("output_tokens") is not None:
        estimated = (int(usage["input_tokens"]) * float(input_rate) + int(usage["output_tokens"]) * float(output_rate)) / 1_000_000
        return round(estimated, 8), f"configured token rates for {model_id}"
    return None, "unavailable; set per-million token rates or use provider-reported cost"


def run_one(model_id: str, task: dict[str, Any], reference: dict[str, Any], trial: int,
            temperature: float, dry_profile: str | None = None, max_tokens: int = 4096,
            disable_reasoning: bool = False) -> dict[str, Any]:
    start = time.perf_counter()
    prompt = task["prompt"]
    raw_response: str
    usage: dict[str, Any]
    provider_cost: float | None
    provider: str
    if dry_profile:
        response_obj = json.loads(json.dumps(reference))
        if dry_profile != "oracle":
            response_obj["ledger_balances_usd"] = json.loads(json.dumps(task["metadata"]["dry_run_balance_mutations"][dry_profile]))
        raw_response = json.dumps(response_obj, indent=2)
        usage = {
            "input_tokens": max(1, len(prompt) // 4),
            "output_tokens": max(1, len(raw_response) // 4),
            "total_tokens": max(2, (len(prompt) + len(raw_response)) // 4),
        }
        provider_cost = 0.0
        provider = "dry-run"
    else:
        raw_response, usage, provider_cost, provider = call_model(model_id, prompt, temperature, max_tokens, disable_reasoning)
    latency_ms = round((time.perf_counter() - start) * 1000, 3)
    estimated_cost, cost_basis = estimate_cost(model_id, usage, provider_cost, dry_run=bool(dry_profile))
    grade = grade_response(raw_response, reference, task.get("metadata", {}))
    return {
        "timestamp": utc_now(),
        "model_id": model_id,
        "provider": provider,
        "task_id": task["task_id"],
        "trial": trial,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "reasoning_disabled": disable_reasoning,
        "prompt": prompt,
        "raw_model_response": raw_response,
        "token_usage": usage,
        "estimated_usd_cost": estimated_cost,
        "cost_estimate_basis": cost_basis,
        "latency_ms": latency_ms,
        "grader": grade,
        "automated_failure_tags": grade["failure_tags"],
    }


def _metrics(model_id: str, trials: list[dict[str, Any]], trial_count: int, task_ids: list[str]) -> dict[str, Any]:
    total = len(trials)
    strict_passes = sum(bool(t["grader"]["passed"]) for t in trials)
    scores = [float(t["grader"]["total_score"]) for t in trials]
    by_task: dict[str, list[dict[str, Any]]] = {task_id: [] for task_id in task_ids}
    for trial in trials:
        by_task.setdefault(trial["task_id"], []).append(trial)
    pass_at_k = sum(1 for task_id in task_ids if any(x["grader"]["passed"] for x in by_task.get(task_id, []))) / max(1, len(task_ids))
    pass_all = sum(1 for task_id in task_ids if len(by_task.get(task_id, [])) >= trial_count and all(x["grader"]["passed"] for x in by_task[task_id])) / max(1, len(task_ids))
    costs = [t["estimated_usd_cost"] for t in trials]
    known_cost = bool(costs) and all(c is not None for c in costs)
    expected = len(task_ids) * trial_count
    return {
        "model_id": model_id,
        "trials_per_task": trial_count,
        "trial_count": total,
        "expected_trial_count": expected,
        "coverage_rate": total / expected if expected else 0.0,
        "strict_pass_rate": strict_passes / total if total else 0.0,
        "mean_partial_score": sum(scores) / total if total else 0.0,
        "pass_at_k": pass_at_k,
        "pass_all_k": pass_all,
        "mean_latency_seconds": (sum(t["latency_ms"] for t in trials) / total / 1000) if total else 0.0,
        "total_run_cost_usd": round(sum(float(c) for c in costs), 8) if known_cost else None,
        "task_results": by_task,
    }


def write_outputs(trials: list[dict[str, Any]], models: list[str], tasks: list[dict[str, Any]], trial_count: int,
                  dry_run: bool, results_dir: Path | None = None,
                  transcript_dir: Path | None = None) -> None:
    results_dir = results_dir or (ROOT / "results")
    transcript_dir = transcript_dir or (ROOT / "transcripts")
    results_dir.mkdir(parents=True, exist_ok=True)
    transcript_prefix = Path(os.path.relpath(transcript_dir, results_dir)).as_posix().rstrip("/") + "/"
    task_ids = [t["task_id"] for t in tasks]
    grouped = {model: [t for t in trials if t["model_id"] == model] for model in models}
    metrics = [_metrics(model, grouped[model], trial_count, task_ids) for model in models]
    summary_json = {
        "generated_at": utc_now(),
        "dry_run_oracle": dry_run,
        "task_ids": task_ids,
        "trials_per_task": trial_count,
        "models": [
            {k: v for k, v in metric.items() if k != "task_results"}
            for metric in metrics
        ],
        "task_matrix": [],
    }
    matrix: list[dict[str, Any]] = []
    for task_id in task_ids:
        row: dict[str, Any] = {"task_id": task_id}
        for model, metric in zip(models, metrics):
            task_trials = metric["task_results"].get(task_id, [])
            successes = sum(bool(t["grader"]["passed"]) for t in task_trials)
            tags = sorted({tag for t in task_trials for tag in t["automated_failure_tags"]})
            row[model] = {"passed_trials": successes, "trials": len(task_trials), "primary_failure_tags": tags[:2]}
        matrix.append(row)
    summary_json["task_matrix"] = matrix
    (results_dir / "summary_results.json").write_text(json.dumps(summary_json, indent=2) + "\n", encoding="utf-8")

    with (results_dir / "summary_table.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["model_id", "trials_per_task", "responses_scored", "expected_responses", "coverage_pct", "strict_pass_rate_pct", "mean_partial_score_pct", "pass_at_k_pct", "pass_all_k_pct", "mean_latency_seconds", "total_run_cost_usd"])
        writer.writeheader()
        for metric in metrics:
            writer.writerow({
                "model_id": metric["model_id"], "trials_per_task": metric["trials_per_task"],
                "responses_scored": metric["trial_count"], "expected_responses": metric["expected_trial_count"],
                "coverage_pct": round(metric["coverage_rate"] * 100, 2),
                "strict_pass_rate_pct": round(metric["strict_pass_rate"] * 100, 2),
                "mean_partial_score_pct": round(metric["mean_partial_score"] * 100, 2),
                "pass_at_k_pct": round(metric["pass_at_k"] * 100, 2),
                "pass_all_k_pct": round(metric["pass_all_k"] * 100, 2),
                "mean_latency_seconds": round(metric["mean_latency_seconds"], 3),
                "total_run_cost_usd": metric["total_run_cost_usd"] if metric["total_run_cost_usd"] is not None else "N/A",
            })

    def pc(value: float) -> str:
        return f"{value * 100:.1f}%"
    lines = [
        "# Evaluation Results", "", f"Generated: {summary_json['generated_at']}",
        f"Run type: {'oracle and simulated flaw profiles (no API calls)' if dry_run else 'live provider run'}", "",
        "## Model summary", "",
        "| Model ID | Responses | Coverage | Strict pass rate* | Mean partial score | pass@k | pass^k | Mean latency (s) | Total cost ($) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for metric in metrics:
        cost = f"{metric['total_run_cost_usd']:.6f}" if metric["total_run_cost_usd"] is not None else "N/A"
        lines.append("| " + " | ".join([
            metric["model_id"], f"{metric['trial_count']}/{metric['expected_trial_count']}", pc(metric["coverage_rate"]), pc(metric["strict_pass_rate"]),
            pc(metric["mean_partial_score"]), pc(metric["pass_at_k"]), pc(metric["pass_all_k"]),
            f"{metric['mean_latency_seconds']:.3f}", cost,
        ]) + " |")
    lines += ["", "## Task-by-task matrix", "", "| Task | " + " | ".join(models) + " |", "|---|" + "|".join(["---"] * len(models)) + "|"]
    for row in matrix:
        cells = [row["task_id"]]
        for model in models:
            value = row[model]
            tags = ",".join(value["primary_failure_tags"]) or "—"
            cells.append(f"{value['passed_trials']}/{value['trials']} pass; {tags}")
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "`Strict pass rate*` is computed over scored responses. `pass@k` and `pass^k` use the full task set, so an unscored task contributes no pass. A cost of `N/A` means the provider did not report cost and no token rates were configured.", ""]
    (results_dir / "RESULTS_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    detailed = [
        "# Detailed Evaluation Report", "", f"Generated: {summary_json['generated_at']}",
        f"Run type: {'oracle and simulated profiles' if dry_run else 'live provider responses'}",
        f"Tasks: {len(task_ids)} | Models: {len(models)} | Trials per task: {trial_count}",
        "",
        "## Run configuration", "",
    ]
    if dry_run:
        detailed += [
            "Provider: local dry-run simulation; no API requests were made.",
            "Generation parameters: not applicable.",
            "Simulated cost: $0.00.",
            "",
        ]
    elif trials:
        providers = ", ".join(sorted({str(t.get("provider", "unknown")) for t in trials}))
        temperatures = ", ".join(str(x) for x in sorted({t.get("temperature") for t in trials}, key=lambda x: (x is None, x)))
        token_limits = ", ".join(str(x) for x in sorted({t.get("max_tokens") for t in trials}, key=lambda x: (x is None, x)))
        reasoning_values = {bool(t.get("reasoning_disabled")) for t in trials}
        reasoning_label = "disabled where supported" if reasoning_values == {True} else "enabled" if reasoning_values == {False} else "mixed"
        all_free_routes = bool(models) and all(model.endswith(":free") for model in models)
        all_zero_reported_cost = bool(trials) and all(t.get("estimated_usd_cost") == 0 for t in trials)
        detailed += [
            f"Provider(s): {providers}.",
            f"Temperature: {temperatures}; maximum output tokens: {token_limits}; reasoning: {reasoning_label}.",
            "All tested model IDs use the explicit `:free` route suffix." if all_free_routes else "This run includes non-`:free` model IDs; model pricing depends on the selected provider route.",
            "All returned responses report zero cost." if all_zero_reported_cost else "Cost totals use provider-reported usage cost when available; unknown rates are reported as unavailable.",
            "",
        ]
    detailed += [
        "## Executive summary", "",
    ]
    strict_total = sum(bool(t["grader"]["passed"]) for t in trials)
    detailed.append(f"The run contains {len(trials)} scored responses; {strict_total} achieved a strict pass ({(strict_total / len(trials) * 100 if trials else 0):.1f}%).")
    known_costs = [t["estimated_usd_cost"] for t in trials]
    if dry_run:
        detailed.append("Simulated run cost: $0.00; no provider requests were made.")
    elif known_costs and all(cost is not None for cost in known_costs):
        detailed.append(f"Total reported or estimated run cost: ${sum(float(cost) for cost in known_costs):.8f}.")
    else:
        detailed.append("At least one trial has no provider-reported cost and no configured token-rate estimate.")
    best_model = max(metrics, key=lambda metric: metric["mean_partial_score"], default=None)
    if best_model:
        detailed += ["", "## Key observations", "",
            f"Highest mean partial score: `{best_model['model_id']}` at {pc(best_model['mean_partial_score'])}; it produced {sum(bool(t['grader']['passed']) for t in grouped[best_model['model_id']])} strict pass(es) in {best_model['trial_count']} scored responses."]
    pooled_tags = Counter(tag for trial in trials for tag in trial["automated_failure_tags"])
    leading_tags = pooled_tags.most_common(3)
    if leading_tags:
        detailed.append("Most frequent automated diagnostics: " + "; ".join(f"`{tag}` ({count})" for tag, count in leading_tags) + ".")
    detailed += ["", "## Model-level results", "",
        "| Model | Responses | Coverage | Strict pass* | Mean partial | pass@k | pass^k | Balance contribution (max 50%) | Item contribution (max 25%) | Ignored-ID contribution (max 15%) | Status contribution (max 10%) | Mean latency (s) | Total cost ($) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for model, metric in zip(models, metrics):
        model_trials = grouped[model]
        mean_dim = {
            key: (sum(float(t["grader"]["dimension_scores"][key]) for t in model_trials) / len(model_trials) if model_trials else 0.0)
            for key in ("ledger_balances", "reconciling_items", "ignored_event_ids", "final_status")
        }
        cost = f"{metric['total_run_cost_usd']:.6f}" if metric["total_run_cost_usd"] is not None else "N/A"
        detailed.append("| " + " | ".join([
            model, f"{metric['trial_count']}/{metric['expected_trial_count']}", pc(metric["coverage_rate"]), pc(metric["strict_pass_rate"]), pc(metric["mean_partial_score"]),
            pc(metric["pass_at_k"]), pc(metric["pass_all_k"]), pc(mean_dim["ledger_balances"]),
            pc(mean_dim["reconciling_items"]), pc(mean_dim["ignored_event_ids"]), pc(mean_dim["final_status"]),
            f"{metric['mean_latency_seconds']:.3f}", cost,
        ]) + " |")

    known_tags = sorted({tag for trial in trials for tag in trial["automated_failure_tags"]})
    if not known_tags:
        known_tags = ["JSON_FORMAT_ERROR", "OUTPUT_SCHEMA_ERROR", "LEDGER_BALANCE_MISMATCH", "MISSING_RECONCILIATION_ITEM", "EXTRA_RECONCILIATION_ITEM", "IGNORED_EVENT_ID_MISMATCH", "STATUS_MISMATCH"]
    detailed += ["", "## Observed mismatch-tag counts", "", "Counts include one hit when a tag appears in a trial; a trial may contribute multiple tags. These labels describe output mismatches and do not infer a model's reasoning process.", "",
        "| Model | " + " | ".join(known_tags) + " |",
        "|---|" + "|".join(["---:"] * len(known_tags)) + "|"]
    for model in models:
        counts = Counter(tag for t in grouped[model] for tag in t["automated_failure_tags"])
        detailed.append("| " + model + " | " + " | ".join(str(counts.get(tag, 0)) for tag in known_tags) + " |")

    detailed += ["", "## Per-task results and transcript links", ""]
    for model in models:
        detailed += [f"### {model}", "", "| Task | Strict pass | Partial score | Balance contribution | Item contribution | Ignored-ID contribution | Status contribution | Failure tags | Transcript |", "|---|---:|---:|---:|---:|---:|---:|---|---|"]
        for task_id in task_ids:
            task_trials = [t for t in grouped[model] if t["task_id"] == task_id]
            if not task_trials:
                detailed.append("| " + " | ".join([task_id, "NOT SCORED", "—", "—", "—", "—", "—", "REQUEST_FAILED", "—"]) + " |")
                continue
            grade = task_trials[0]["grader"]
            dimension_keys = ("ledger_balances", "reconciling_items", "ignored_event_ids", "final_status")
            dimensions = [f"{grade['dimension_scores'][key]:.4f}" for key in dimension_keys]
            tags = ", ".join(task_trials[0]["automated_failure_tags"]) or "—"
            transcript_link = f"[trial {task_trials[0]['trial']}]({transcript_prefix}{slug(model)}/{task_id}_trial_{task_trials[0]['trial']}.json)"
            detailed.append("| " + " | ".join([
                task_id, "PASS" if grade["passed"] else "FAIL", f"{grade['total_score']:.4f}",
                *dimensions, tags, transcript_link,
            ]) + " |")
        detailed.append("")

    errors_path = results_dir / "run_errors.json"
    if errors_path.exists():
        run_errors = json.loads(errors_path.read_text(encoding="utf-8"))
        detailed += ["## Unscored requests", ""]
        if run_errors:
            detailed += ["These requested trials did not return a gradeable response:", ""]
            for error in run_errors:
                detailed.append(f"- `{error['model_id']}` / `{error['task_id']}` trial {error['trial']}: {error['detail']}")
        else:
            detailed.append("No unscored requests were recorded.")
        detailed.append("")

    detailed += ["## Interpretation and limits", "",
        "Strict pass is binary: the response must be exactly one JSON object (raw or a single JSON fence), account ID and cutoff must match, the output must follow the exact schema, all six balances must match to the cent, reconciling items must match exactly at F1 1.0, ignored IDs must match exactly, and final status must match.",
        "Mismatch tags describe observed output differences; they do not infer the model's internal reasoning.",
        "Strict pass rate is over returned, scored responses; coverage reports returned responses divided by requested responses. pass@k and pass^k use the complete task set, so missing responses do not count as passes. With one trial per task, pass@k and pass^k both equal the observed fraction of tasks with a strict pass. Repeated trials are needed to estimate sampling-sensitive pass@k/pass^k behavior.",
        "", ""]
    (results_dir / "DETAILED_EVALUATION.md").write_text("\n".join(detailed), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate model outputs on the ASC 606 reconciliation benchmark")
    parser.add_argument("--models", default=DEFAULT_MODELS, help="comma-separated model IDs")
    parser.add_argument("--trials", type=int, default=1, help="trials per task (default: 1)")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--tasks", default="all", help="all or comma-separated task IDs/prefixes")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--max-tokens", type=int, default=2400, help="maximum generated tokens per live response")
    parser.add_argument("--disable-reasoning", action="store_true", help="disable model reasoning where the provider supports it")
    parser.add_argument("--dry-run-oracle", action="store_true", help="run reference and simulated flawed profiles without API calls")
    args = parser.parse_args(argv)
    if args.trials < 1 or args.concurrency < 1 or args.max_tokens < 1:
        parser.error("--trials, --concurrency, and --max-tokens must be positive")
    task_filters = None if args.tasks.strip().lower() == "all" else [x.strip() for x in args.tasks.split(",") if x.strip()]
    try:
        cases = load_inputs(task_filters)
    except Exception as exc:
        parser.error(str(exc))

    if args.dry_run_oracle:
        model_profiles = [
            ("dry-run/oracle-reference", "oracle"),
            ("dry-run/simulated-balance-offset-a", "SIMULATED_LEDGER_OFFSET_A"),
            ("dry-run/simulated-balance-offset-b", "SIMULATED_LEDGER_OFFSET_B"),
        ]
    else:
        model_profiles = [(model.strip(), None) for model in args.models.split(",") if model.strip()]
        if not model_profiles:
            parser.error("--models must contain at least one model ID")

    jobs = [(model, profile, task, reference, trial) for model, profile in model_profiles for task, reference in cases for trial in range(1, args.trials + 1)]
    transcripts: list[dict[str, Any]] = []
    errors: list[str] = []
    error_records: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(run_one, model, task, reference, trial, args.temperature, profile, args.max_tokens, args.disable_reasoning): (model, task["task_id"], trial)
                   for model, profile, task, reference, trial in jobs}
        for future in as_completed(futures):
            model, task_id, trial = futures[future]
            try:
                record = future.result()
                transcripts.append(record)
                model_dir = ROOT / "transcripts" / slug(model)
                model_dir.mkdir(parents=True, exist_ok=True)
                path = model_dir / f"{task_id}_trial_{trial}.json"
                path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"[{record['grader']['total_score']:.2f} {'PASS' if record['grader']['passed'] else 'FAIL'}] {model} {task_id} trial {trial}")
            except Exception as exc:
                message = f"{model} {task_id} trial {trial}: {exc}"
                errors.append(message)
                error_text = str(exc).lower()
                if "429" in error_text or "rate-limit" in error_text or "rate limited" in error_text:
                    category, detail = "provider_rate_limit", "Provider route rate-limited this request."
                elif "nonetype" in error_text or "incomplete" in error_text:
                    category, detail = "incomplete_provider_response", "Provider returned an incomplete response."
                else:
                    category, detail = "provider_request_error", "Provider request failed; see the command output for the runtime error."
                error_records.append({"model_id": model, "task_id": task_id, "trial": trial, "category": category, "detail": detail})
                print(f"[ERROR] {message}", file=sys.stderr)
    results_dir = ROOT / "results" / "dry_run" if args.dry_run_oracle else ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "run_errors.json").write_text(json.dumps(error_records, indent=2) + "\n", encoding="utf-8")
    model_ids = [model for model, _ in model_profiles]
    write_outputs(transcripts, model_ids, [t for t, _ in cases], args.trials, args.dry_run_oracle, results_dir)
    print(f"Wrote {len(transcripts)} transcripts and reports under {ROOT}")
    if errors:
        print(f"Completed with {len(errors)} failed API trial(s).", file=sys.stderr)
        return 1
    if not transcripts:
        print("No trials completed.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
