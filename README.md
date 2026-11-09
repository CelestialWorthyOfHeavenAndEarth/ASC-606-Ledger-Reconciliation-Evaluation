# ASC 606 Ledger Reconciliation Evaluation

## 1. Short Description

This benchmark tests whether a model can reconcile asynchronous financial events into audit-ready ledger balances under the benchmark's ASC 606-inspired policies. Eight synthetic ledgers cover out-of-order events, duplicate webhooks, retroactive proration, coupon and tax precedence, FX settlement, and dispute holds. The deterministic validator confirms all eight references and rejects 112 invalid-output mutations. The latest full run scored all 40 responses from five OpenRouter `:free` routes. No response passed strictly; Dots3 Note Preview had the highest mean partial score at 85.10%. Successful calls reported $0.00 cost.

## 2. Video Walkthrough Link

**[INSERT PUBLIC VIDEO LINK HERE BEFORE ZIPPING]**

## 3. Domain and Expertise

The domain is Financial Accounting (ASC 606 revenue recognition) and Distributed Billing Systems Engineering. The cases model subscription billing events that may be duplicated, received late, or effective retroactively, then require a reproducible period-end trial-balance view.

## 4. What It Tests and Why It Matters

Billing webhooks are not guaranteed to arrive in effective-time order. Treating receipt time as the accounting timeline can change a credit-note cap, daily proration, or the service period to which usage belongs. Combining a promotional discount, minimum contract commitment, tax, and wallet balance in the wrong order changes cash and liabilities. FX settlement, chargeback reversals, and unresolved disputes can also move cash and revenue recognition independently.

The eight cases measure those choices through exact USD-cent balances, reconciling-item precision and recall, duplicate IDs, and final account status. The negative control is designed to catch false positives: equal-value payments are distinct, a coupon reaches the floor with no prevented discount, and cancellation falls one second outside the cooling-off window.

## 5. Setup and Run Instructions

From the repository directory, use Python 3.10 or later:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python validate_eval.py
python run_eval.py --dry-run-oracle
```

The validator uses no keys and normally completes in under two seconds. The dry run evaluates the oracle and two controlled balance-offset profiles across all tasks and trials, writes 72 transcripts, and generates its report under `results/dry_run/`. It makes no network calls and reports zero API cost.

The clean negative-control task has an intentionally empty gold reconciling-item set. For its missing-item mutation, the validator adds a temporary synthetic expected item so the grader's missing-item recall path is still exercised; this annotation is not written to the task or reference files.

### Interactive browser dashboard

To explore the saved evaluation in a browser, start the static server from the repository root:

```powershell
python -m http.server 8000
```

Open <http://localhost:8000/web/>. Select a task and model to compare scores and strict-pass status, review observed mismatch tags and weighted score dimensions, and expand the saved prompt, model response, or grader details. The dashboard reads the checked-in JSON results and transcripts; it does not call a model or need an API key. Keep the server terminal open while recording and press `Ctrl+C` when finished. Do not open `web/index.html` directly as a file, because browsers block its data fetches from `file://` URLs.

For an API-free demo recording, run `python validate_eval.py` followed by `python run_eval.py --dry-run-oracle`. Show the validator's reference and mutation checks, then open `results/dry_run/DETAILED_EVALUATION.md` to walk through the passing oracle and the two controlled balance-offset profiles. Start the dashboard server above and use the task/model selectors to inspect a saved live response and its grader breakdown. Finish with the saved live comparison in `results/DETAILED_EVALUATION.md`; these saved results do not require a key or a live model call. A timed narration is in [`SUBMISSION_TEXT.md`](SUBMISSION_TEXT.md).

For the free-only comparison, set an OpenRouter credential and run the explicit `:free` routes. These are also the harness defaults; the default run uses one trial per task, concurrency 1, and a 2,400-token output cap:

```powershell
$env:OPENROUTER_API_KEY = "your-key"
python run_eval.py --trials 1 --temperature 0.2 --concurrency 1 --max-tokens 2400 --disable-reasoning
```

The five default IDs are `nvidia/nemotron-3.5-lightning:free`, `nvidia/nemotron-3.5-super-vl:free`, `dots-studio/dots-3-note-preview:free`, `xingchen-agi/xing4.0-29b-a4b:free`, and `cohere/north-mini-code:free`. OpenRouter's free routes use shared provider capacity and availability can change; a transient upstream limit or incomplete response may need a retry. Native provider credentials are also supported (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`); check pricing before selecting non-free model routes. Keep local `.env` files out of version control; `.gitignore` excludes them.

The default live run contains 8 tasks × 1 trial per model (40 requests when all five routes are available). The harness uses provider-reported cost when available; otherwise configure `INPUT_PRICE_USD_PER_MILLION` and `OUTPUT_PRICE_USD_PER_MILLION` in the environment. A live run with unknown rates records cost as unavailable rather than inventing a price. Runtime depends on provider latency and concurrency; the local validation and dry run complete in seconds.

Generated outputs are written to `results/summary_results.json`, `results/summary_table.csv`, `results/RESULTS_REPORT.md`, `results/DETAILED_EVALUATION.md`, and `transcripts/<model_slug>/<task_id>_trial_<n>.json`.

## 6. Models Tested and Results

The current post-fix comparison ran each of five explicitly free OpenRouter routes once on each of eight tasks, with reasoning disabled and a 2,400-token output cap. All 40 responses were eventually scored, with four Xing4.0 cases recovered by retrying transient incomplete or upstream-rate-limited calls. No paid route was selected; successful responses reported $0.00 cost.

| Model | Scored / requested | Coverage | Strict pass* | Mean partial | pass@1 | pass^1 | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| `nvidia/nemotron-3.5-lightning:free` | 8/8 | 100.0% | 0.0% | 46.51% | 0.0% | 0.0% | $0.00 |
| `nvidia/nemotron-3.5-super-vl:free` | 8/8 | 100.0% | 0.0% | 64.99% | 0.0% | 0.0% | $0.00 |
| `dots-studio/dots-3-note-preview:free` | 8/8 | 100.0% | 0.0% | 85.10% | 0.0% | 0.0% | $0.00 |
| `xingchen-agi/xing4.0-29b-a4b:free` | 8/8 | 100.0% | 0.0% | 55.64% | 0.0% | 0.0% | $0.00 |
| `cohere/north-mini-code:free` | 8/8 | 100.0% | 0.0% | 44.62% | 0.0% | 0.0% | $0.00 |

`Strict pass*` and mean partial score use scored responses; `pass@1` and `pass^1` use all eight tasks. Dots3 had the highest partial score, but all eight of its responses failed strict format validation. See the [detailed evaluation](results/DETAILED_EVALUATION.md), [summary matrix](results/RESULTS_REPORT.md), and [saved transcripts](transcripts/).

The [detailed evaluation report](results/DETAILED_EVALUATION.md) includes weighted dimension scores, each task's score and diagnostic tags, transcript links, coverage, and latency. The [summary results report](results/RESULTS_REPORT.md) contains the task matrix. The offline harness dry run is reported in [the dry-run report](results/dry_run/RESULTS_REPORT.md); the oracle passes all tasks on all three trials, while two simulated balance-offset profiles fail by design.

| Dry-run control | Strict pass rate | Mean partial score | pass@3 | pass^3 | Cost |
|---|---:|---:|---:|---:|---:|
| `dry-run/oracle-reference` | 100.0% | 100.0% | 100.0% | 100.0% | $0.00 |
| `dry-run/simulated-balance-offset-a` | 0.0% | 75.0% | 0.0% | 0.0% | $0.00 |
| `dry-run/simulated-balance-offset-b` | 0.0% | 83.3% | 0.0% | 0.0% | $0.00 |

## 7. Failure Analysis & Takeaway

The dry-run profiles apply two fixed balance offsets to reference answers. They verify that the runner stores responses, the grader detects ledger differences, and the reports aggregate the results. They do not simulate event arrival-order or accounting-rule algorithms. See the [Task 1 offset transcript](transcripts/dry-run_simulated-balance-offset-a/task_01_idempotency_ooo_trial_1.json) and [Task 3 offset transcript](transcripts/dry-run_simulated-balance-offset-b/task_03_coupon_floor_tax_cap_trial_1.json).

Task 3 shows why coupon cap, commitment floor, post-coupon tax, and post-tax wallet application must be evaluated in order; Task 8 combines a floor cap with an open dispute that freezes the elapsed share of revenue. The live reports now label observed mismatches such as incorrect ledger balances, missing or extra reconciliation items, and status mismatches without inferring their underlying cause.

In the current run, none of the 40 responses earned a strict pass. The most frequent observed tags were ledger-balance mismatch (35 responses), missing reconciliation item (27), and extra reconciliation item (23). Dots3 had the highest mean partial score (85.10%), but all eight outputs had a format violation. The report separates observed format, identity, ledger, reconciliation-item, ignored-ID, and status mismatches without claiming to diagnose hidden reasoning. See the [detailed analysis](results/DETAILED_EVALUATION.md).

The dry-run profiles are controlled balance offsets, not observed model outputs or simulations of accounting algorithms. Live transcripts store each model response and the grader's per-dimension breakdown. The benchmark tests whether a model preserves temporal order, interacting policy constraints, cent-level arithmetic, and clean-audit evidence together.

## 8. Prior Work, Provenance, and AI Use Disclosure

All eight enterprise ledger datasets, accounting policy specifications, task prompts, deterministic oracle, and grader were created originally for this hackathon. The benchmark contains synthetic IDs, dates, amounts, and transactions only; it uses no confidential, customer, or unlicensed data.

AI coding tools assisted with implementation, synthetic fixtures, and documentation. `python validate_eval.py` checks prompt generation, recomputes stored references using the deterministic oracle, and rejects 112 invalid-output mutations. These are reproducibility and grader-integrity checks, not independent accounting sign-off; have the benchmark policies and gold answers reviewed by an accounting expert before using them as accounting guidance.
