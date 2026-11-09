# Video Walkthrough and AI Voiceover

## Recording setup

This is designed as a five-minute screen recording. You do not need to appear on camera. Before recording, open a terminal in the repository root and start the dashboard:

```powershell
python -m http.server 8000
```

Open <http://localhost:8000/web/> in a browser. The dashboard uses the saved evaluation and makes no model calls. If you want to capture the verification step too, run `python validate_eval.py` and `python run_eval.py --dry-run-oracle` before starting the screen recording; both run without API credentials. Keep the browser zoom around 90–100% so the leaderboard and task explorer are readable.

## Screen plan

| Time | Show on screen |
|---|---|
| 0:00–0:45 | Dashboard title and evaluation configuration; introduce the reconciliation problem. |
| 0:45–1:35 | README or task examples; show the eight synthetic cases and what makes events difficult. |
| 1:35–2:25 | `validate_eval.py` result and the detailed report; explain the oracle, grader, strict pass, and partial score. |
| 2:25–3:40 | Dashboard leaderboard; point to five free routes, 40/40 coverage, scores, and zero strict passes. |
| 3:40–4:35 | Select Task 1 or Task 3, then choose two models; expand score dimensions, mismatch tags, response, and grader details. |
| 4:35–5:00 | Show the detailed report takeaway and close with the benchmark’s limitations. |

## Voiceover script

### 0:00–0:45 — The problem

This project evaluates whether language models can reconcile asynchronous billing events into an audit-ready ledger under a set of ASC 606-inspired policies. In real billing systems, events can arrive late, more than once, or out of effective-time order. A seat change may take effect before a credit note even when the webhook arrives afterward. Discounts, tax, wallet balances, refunds, foreign exchange, and disputes can each affect different accounts. A plausible-looking answer can still be wrong by cents, by event, or by accounting period.

### 0:45–1:35 — The benchmark

The benchmark uses eight synthetic cases. They cover duplicate events, retroactive proration, coupon and tax precedence, foreign-exchange settlement, tiered usage, leap-year and daylight-saving cutovers, a negative control, and a multi-rule dispute case. Each task supplies its event stream, accounting policies, cutoff, and required JSON format. The data is synthetic and contains no customer records.

### 1:35–2:25 — How evaluation works

The reference solver uses decimal arithmetic to produce an expected answer. The grader checks the output format and task identity, six ledger balances, reconciling items, ignored event IDs, and final status. A strict pass requires every required check to match. A partial score shows which dimensions matched when the complete answer did not. The validation command recomputes all eight references and rejects 112 deliberately invalid answer mutations. The dry run also checks the reporting pipeline without calling any model. These checks confirm consistency with the benchmark’s own reference rules; they are not an independent accounting audit.

### 2:25–3:40 — Models and headline results

This saved comparison contains five explicitly free OpenRouter model routes: Nemotron 3.5 Lightning, Nemotron 3.5 Super VL, Dots 3 Note Preview, Xing 4.0, and Cohere North Mini Code. Each route has one response for each of the eight tasks, for 40 scored responses total. No response earned a strict pass. Dots 3 had the highest mean partial score at 85.10 percent, followed by Nemotron Super VL at 64.99 percent, Xing 4.0 at 55.64 percent, Nemotron Lightning at 46.51 percent, and Cohere North Mini Code at 44.62 percent. Dots 3 still failed strict grading on all eight tasks because its outputs violated the required format. Partial score is useful for diagnosis, but with one trial per task it should not be treated as a stable ranking.

### 3:40–4:35 — Inspect a task and response

In the dashboard, I can select a task and compare every model’s score, strict-pass result, and observed mismatch tags. I’ll open a transcript to see the weighted score dimensions, then expand the original prompt, model response, and grader discrepancy details. For example, Task 1 tests a late-arriving seat change and credit note. Task 3 combines a coupon cap, a commitment floor, tax, and wallet application. The grader reports the mismatched balances or reconciliation items it observed; it does not claim to know the model’s hidden reasoning. Everything shown here is saved locally, so browsing the results does not make new API calls.

### 4:35–5:00 — Takeaway

The results show that producing a plausible ledger is not enough: the model must also follow the exact schema and preserve event identity, policy order, and cent-level balances. This repository makes the tasks, references, transcripts, and grader available for review and reruns. The benchmark is a reproducible evaluation prototype, not accounting advice or an independent certification.

## AI voice generation notes

Use a clear, neutral documentary voice at roughly 125–135 words per minute. Keep the delivery measured and pronounce “ASC 606” as “A-S-C six-oh-six,” “JSON” as “JAY-sən,” and “Dots 3” as “Dots Three.” Add a short pause between timed sections. For the voice generator, paste only the narration under **Voiceover script**; keep the timestamps and screen plan as editing cues, not spoken text.
