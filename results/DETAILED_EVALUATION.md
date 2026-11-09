# Detailed Evaluation Report

Generated: 2026-11-08T20:20:38Z
Run type: live provider responses
Tasks: 8 | Models: 5 | Trials per task: 1

## Run configuration

Provider(s): openrouter.
Temperature: 0.2; maximum output tokens: 2400; reasoning: disabled where supported.
All tested model IDs use the explicit `:free` route suffix.
All returned responses report zero cost.

## Executive summary

The run contains 40 scored responses; 0 achieved a strict pass (0.0%).
Total reported or estimated run cost: $0.00000000.

## Key observations

Highest mean partial score: `dots-studio/dots-3-note-preview:free` at 85.1%; it produced 0 strict pass(es) in 8 scored responses.
Most frequent automated diagnostics: `LEDGER_BALANCE_MISMATCH` (35); `MISSING_RECONCILIATION_ITEM` (27); `EXTRA_RECONCILIATION_ITEM` (23).

## Model-level results

| Model | Responses | Coverage | Strict pass* | Mean partial | pass@k | pass^k | Balance contribution (max 50%) | Item contribution (max 25%) | Ignored-ID contribution (max 15%) | Status contribution (max 10%) | Mean latency (s) | Total cost ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| nvidia/nemotron-3.5-lightning:free | 8/8 | 100.0% | 0.0% | 46.5% | 0.0% | 0.0% | 22.9% | 6.5% | 7.1% | 10.0% | 3.947 | 0.000000 |
| nvidia/nemotron-3.5-super-vl:free | 8/8 | 100.0% | 0.0% | 65.0% | 0.0% | 0.0% | 30.2% | 10.2% | 14.6% | 10.0% | 2.328 | 0.000000 |
| dots-studio/dots-3-note-preview:free | 8/8 | 100.0% | 0.0% | 85.1% | 0.0% | 0.0% | 42.7% | 17.4% | 15.0% | 10.0% | 11.263 | 0.000000 |
| xingchen-agi/xing4.0-29b-a4b:free | 8/8 | 100.0% | 0.0% | 55.6% | 0.0% | 0.0% | 24.0% | 8.9% | 12.8% | 10.0% | 9.580 | 0.000000 |
| cohere/north-mini-code:free | 8/8 | 100.0% | 0.0% | 44.6% | 0.0% | 0.0% | 18.8% | 7.5% | 10.9% | 7.5% | 1.837 | 0.000000 |

## Observed mismatch-tag counts

Counts include one hit when a tag appears in a trial; a trial may contribute multiple tags. These labels describe output mismatches and do not infer a model's reasoning process.

| Model | EXTRA_RECONCILIATION_ITEM | IGNORED_EVENT_ID_MISMATCH | JSON_FORMAT_ERROR | LEDGER_BALANCE_MISMATCH | MISSING_RECONCILIATION_ITEM | OUTPUT_FORMAT_VIOLATION | STATUS_MISMATCH |
|---|---:|---:|---:|---:|---:|---:|---:|
| nvidia/nemotron-3.5-lightning:free | 6 | 5 | 0 | 8 | 6 | 0 | 0 |
| nvidia/nemotron-3.5-super-vl:free | 5 | 1 | 0 | 8 | 6 | 0 | 0 |
| dots-studio/dots-3-note-preview:free | 3 | 0 | 0 | 4 | 4 | 8 | 0 |
| xingchen-agi/xing4.0-29b-a4b:free | 6 | 2 | 0 | 8 | 6 | 0 | 0 |
| cohere/north-mini-code:free | 3 | 2 | 1 | 7 | 5 | 0 | 1 |

## Per-task results and transcript links

### nvidia/nemotron-3.5-lightning:free

| Task | Strict pass | Partial score | Balance contribution | Item contribution | Ignored-ID contribution | Status contribution | Failure tags | Transcript |
|---|---:|---:|---:|---:|---:|---:|---|---|
| task_01_idempotency_ooo | FAIL | 0.5950 | 0.2500 | 0.1250 | 0.1200 | 0.1000 | IGNORED_EVENT_ID_MISMATCH, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-lightning_free/task_01_idempotency_ooo_trial_1.json) |
| task_02_retro_proration_cooling | FAIL | 0.4333 | 0.3333 | 0.0000 | 0.0000 | 0.1000 | EXTRA_RECONCILIATION_ITEM, IGNORED_EVENT_ID_MISMATCH, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-lightning_free/task_02_retro_proration_cooling_trial_1.json) |
| task_03_coupon_floor_tax_cap | FAIL | 0.2667 | 0.1667 | 0.0000 | 0.0000 | 0.1000 | EXTRA_RECONCILIATION_ITEM, IGNORED_EVENT_ID_MISMATCH, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-lightning_free/task_03_coupon_floor_tax_cap_trial_1.json) |
| task_04_fx_chargeback_reversal | FAIL | 0.4167 | 0.1667 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-lightning_free/task_04_fx_chargeback_reversal_trial_1.json) |
| task_05_tiered_usage_retro_credit | FAIL | 0.2667 | 0.1667 | 0.0000 | 0.0000 | 0.1000 | EXTRA_RECONCILIATION_ITEM, IGNORED_EVENT_ID_MISMATCH, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-lightning_free/task_05_tiered_usage_retro_credit_trial_1.json) |
| task_06_leap_year_dst_cutover | FAIL | 0.2667 | 0.1667 | 0.0000 | 0.0000 | 0.1000 | EXTRA_RECONCILIATION_ITEM, IGNORED_EVENT_ID_MISMATCH, LEDGER_BALANCE_MISMATCH | [trial 1](../transcripts/nvidia_nemotron-3.5-lightning_free/task_06_leap_year_dst_cutover_trial_1.json) |
| task_07_negative_control_clean_audit | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../transcripts/nvidia_nemotron-3.5-lightning_free/task_07_negative_control_clean_audit_trial_1.json) |
| task_08_asc606_multi_rule_cascade | FAIL | 0.6429 | 0.2500 | 0.1429 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-lightning_free/task_08_asc606_multi_rule_cascade_trial_1.json) |

### nvidia/nemotron-3.5-super-vl:free

| Task | Strict pass | Partial score | Balance contribution | Item contribution | Ignored-ID contribution | Status contribution | Failure tags | Transcript |
|---|---:|---:|---:|---:|---:|---:|---|---|
| task_01_idempotency_ooo | FAIL | 0.5950 | 0.2500 | 0.1250 | 0.1200 | 0.1000 | IGNORED_EVENT_ID_MISMATCH, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-super-vl_free/task_01_idempotency_ooo_trial_1.json) |
| task_02_retro_proration_cooling | FAIL | 0.5833 | 0.3333 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-super-vl_free/task_02_retro_proration_cooling_trial_1.json) |
| task_03_coupon_floor_tax_cap | FAIL | 0.6667 | 0.4167 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-super-vl_free/task_03_coupon_floor_tax_cap_trial_1.json) |
| task_04_fx_chargeback_reversal | FAIL | 0.4167 | 0.1667 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-super-vl_free/task_04_fx_chargeback_reversal_trial_1.json) |
| task_05_tiered_usage_retro_credit | FAIL | 0.5833 | 0.3333 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-super-vl_free/task_05_tiered_usage_retro_credit_trial_1.json) |
| task_06_leap_year_dst_cutover | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../transcripts/nvidia_nemotron-3.5-super-vl_free/task_06_leap_year_dst_cutover_trial_1.json) |
| task_07_negative_control_clean_audit | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../transcripts/nvidia_nemotron-3.5-super-vl_free/task_07_negative_control_clean_audit_trial_1.json) |
| task_08_asc606_multi_rule_cascade | FAIL | 0.7708 | 0.3333 | 0.1875 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/nvidia_nemotron-3.5-super-vl_free/task_08_asc606_multi_rule_cascade_trial_1.json) |

### dots-studio/dots-3-note-preview:free

| Task | Strict pass | Partial score | Balance contribution | Item contribution | Ignored-ID contribution | Status contribution | Failure tags | Transcript |
|---|---:|---:|---:|---:|---:|---:|---|---|
| task_01_idempotency_ooo | FAIL | 0.7500 | 0.3333 | 0.1667 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM, OUTPUT_FORMAT_VIOLATION | [trial 1](../transcripts/dots-studio_dots-3-note-preview_free/task_01_idempotency_ooo_trial_1.json) |
| task_02_retro_proration_cooling | FAIL | 0.5833 | 0.3333 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM, OUTPUT_FORMAT_VIOLATION | [trial 1](../transcripts/dots-studio_dots-3-note-preview_free/task_02_retro_proration_cooling_trial_1.json) |
| task_03_coupon_floor_tax_cap | FAIL | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | OUTPUT_FORMAT_VIOLATION | [trial 1](../transcripts/dots-studio_dots-3-note-preview_free/task_03_coupon_floor_tax_cap_trial_1.json) |
| task_04_fx_chargeback_reversal | FAIL | 0.7667 | 0.4167 | 0.1000 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM, OUTPUT_FORMAT_VIOLATION | [trial 1](../transcripts/dots-studio_dots-3-note-preview_free/task_04_fx_chargeback_reversal_trial_1.json) |
| task_05_tiered_usage_retro_credit | FAIL | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | OUTPUT_FORMAT_VIOLATION | [trial 1](../transcripts/dots-studio_dots-3-note-preview_free/task_05_tiered_usage_retro_credit_trial_1.json) |
| task_06_leap_year_dst_cutover | FAIL | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | OUTPUT_FORMAT_VIOLATION | [trial 1](../transcripts/dots-studio_dots-3-note-preview_free/task_06_leap_year_dst_cutover_trial_1.json) |
| task_07_negative_control_clean_audit | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH, OUTPUT_FORMAT_VIOLATION | [trial 1](../transcripts/dots-studio_dots-3-note-preview_free/task_07_negative_control_clean_audit_trial_1.json) |
| task_08_asc606_multi_rule_cascade | FAIL | 0.8750 | 0.5000 | 0.1250 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, MISSING_RECONCILIATION_ITEM, OUTPUT_FORMAT_VIOLATION | [trial 1](../transcripts/dots-studio_dots-3-note-preview_free/task_08_asc606_multi_rule_cascade_trial_1.json) |

### xingchen-agi/xing4.0-29b-a4b:free

| Task | Strict pass | Partial score | Balance contribution | Item contribution | Ignored-ID contribution | Status contribution | Failure tags | Transcript |
|---|---:|---:|---:|---:|---:|---:|---|---|
| task_01_idempotency_ooo | FAIL | 0.6367 | 0.2500 | 0.1667 | 0.1200 | 0.1000 | EXTRA_RECONCILIATION_ITEM, IGNORED_EVENT_ID_MISMATCH, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/xingchen-agi_xing4.0-29b-a4b_free/task_01_idempotency_ooo_trial_1.json) |
| task_02_retro_proration_cooling | FAIL | 0.5833 | 0.3333 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/xingchen-agi_xing4.0-29b-a4b_free/task_02_retro_proration_cooling_trial_1.json) |
| task_03_coupon_floor_tax_cap | FAIL | 0.4167 | 0.1667 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/xingchen-agi_xing4.0-29b-a4b_free/task_03_coupon_floor_tax_cap_trial_1.json) |
| task_04_fx_chargeback_reversal | FAIL | 0.4167 | 0.0833 | 0.0833 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/xingchen-agi_xing4.0-29b-a4b_free/task_04_fx_chargeback_reversal_trial_1.json) |
| task_05_tiered_usage_retro_credit | FAIL | 0.3500 | 0.2500 | 0.0000 | 0.0000 | 0.1000 | EXTRA_RECONCILIATION_ITEM, IGNORED_EVENT_ID_MISMATCH, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/xingchen-agi_xing4.0-29b-a4b_free/task_05_tiered_usage_retro_credit_trial_1.json) |
| task_06_leap_year_dst_cutover | FAIL | 0.5000 | 0.2500 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH | [trial 1](../transcripts/xingchen-agi_xing4.0-29b-a4b_free/task_06_leap_year_dst_cutover_trial_1.json) |
| task_07_negative_control_clean_audit | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../transcripts/xingchen-agi_xing4.0-29b-a4b_free/task_07_negative_control_clean_audit_trial_1.json) |
| task_08_asc606_multi_rule_cascade | FAIL | 0.7143 | 0.2500 | 0.2143 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/xingchen-agi_xing4.0-29b-a4b_free/task_08_asc606_multi_rule_cascade_trial_1.json) |

### cohere/north-mini-code:free

| Task | Strict pass | Partial score | Balance contribution | Item contribution | Ignored-ID contribution | Status contribution | Failure tags | Transcript |
|---|---:|---:|---:|---:|---:|---:|---|---|
| task_01_idempotency_ooo | FAIL | 0.6533 | 0.3333 | 0.1000 | 0.1200 | 0.1000 | EXTRA_RECONCILIATION_ITEM, IGNORED_EVENT_ID_MISMATCH, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/cohere_north-mini-code_free/task_01_idempotency_ooo_trial_1.json) |
| task_02_retro_proration_cooling | FAIL | 0.5000 | 0.2500 | 0.0000 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/cohere_north-mini-code_free/task_02_retro_proration_cooling_trial_1.json) |
| task_03_coupon_floor_tax_cap | FAIL | 0.3333 | 0.0833 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/cohere_north-mini-code_free/task_03_coupon_floor_tax_cap_trial_1.json) |
| task_04_fx_chargeback_reversal | FAIL | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | JSON_FORMAT_ERROR | [trial 1](../transcripts/cohere_north-mini-code_free/task_04_fx_chargeback_reversal_trial_1.json) |
| task_05_tiered_usage_retro_credit | FAIL | 0.4167 | 0.1667 | 0.0000 | 0.1500 | 0.1000 | EXTRA_RECONCILIATION_ITEM, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM | [trial 1](../transcripts/cohere_north-mini-code_free/task_05_tiered_usage_retro_credit_trial_1.json) |
| task_06_leap_year_dst_cutover | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../transcripts/cohere_north-mini-code_free/task_06_leap_year_dst_cutover_trial_1.json) |
| task_07_negative_control_clean_audit | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../transcripts/cohere_north-mini-code_free/task_07_negative_control_clean_audit_trial_1.json) |
| task_08_asc606_multi_rule_cascade | FAIL | 0.1667 | 0.1667 | 0.0000 | 0.0000 | 0.0000 | IGNORED_EVENT_ID_MISMATCH, LEDGER_BALANCE_MISMATCH, MISSING_RECONCILIATION_ITEM, STATUS_MISMATCH | [trial 1](../transcripts/cohere_north-mini-code_free/task_08_asc606_multi_rule_cascade_trial_1.json) |

## Unscored requests

No unscored requests were recorded.

## Interpretation and limits

Strict pass is binary: the response must be exactly one JSON object (raw or a single JSON fence), account ID and cutoff must match, the output must follow the exact schema, all six balances must match to the cent, reconciling items must match exactly at F1 1.0, ignored IDs must match exactly, and final status must match.
Mismatch tags describe observed output differences; they do not infer the model's internal reasoning.
Strict pass rate is over returned, scored responses; coverage reports returned responses divided by requested responses. pass@k and pass^k use the complete task set, so missing responses do not count as passes. With one trial per task, pass@k and pass^k both equal the observed fraction of tasks with a strict pass. Repeated trials are needed to estimate sampling-sensitive pass@k/pass^k behavior.
