# Detailed Evaluation Report

Generated: 2026-11-08T18:49:23Z
Run type: oracle and simulated profiles
Tasks: 8 | Models: 3 | Trials per task: 3

## Run configuration

Provider: local dry-run simulation; no API requests were made.
Generation parameters: not applicable.
Simulated cost: $0.00.

## Executive summary

The run contains 72 scored responses; 24 achieved a strict pass (33.3%).
Simulated run cost: $0.00; no provider requests were made.

## Key observations

Highest mean partial score: `dry-run/oracle-reference` at 100.0%; it produced 24 strict pass(es) in 24 scored responses.
Most frequent automated diagnostics: `LEDGER_BALANCE_MISMATCH` (48).

## Model-level results

| Model | Responses | Coverage | Strict pass* | Mean partial | pass@k | pass^k | Balance contribution (max 50%) | Item contribution (max 25%) | Ignored-ID contribution (max 15%) | Status contribution (max 10%) | Mean latency (s) | Total cost ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dry-run/oracle-reference | 24/24 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 50.0% | 25.0% | 15.0% | 10.0% | 0.000 | 0.000000 |
| dry-run/simulated-balance-offset-a | 24/24 | 100.0% | 0.0% | 75.0% | 0.0% | 0.0% | 25.0% | 25.0% | 15.0% | 10.0% | 0.000 | 0.000000 |
| dry-run/simulated-balance-offset-b | 24/24 | 100.0% | 0.0% | 83.3% | 0.0% | 0.0% | 33.3% | 25.0% | 15.0% | 10.0% | 0.000 | 0.000000 |

## Observed mismatch-tag counts

Counts include one hit when a tag appears in a trial; a trial may contribute multiple tags. These labels describe output mismatches and do not infer a model's reasoning process.

| Model | LEDGER_BALANCE_MISMATCH |
|---|---:|
| dry-run/oracle-reference | 0 |
| dry-run/simulated-balance-offset-a | 24 |
| dry-run/simulated-balance-offset-b | 24 |

## Per-task results and transcript links

### dry-run/oracle-reference

| Task | Strict pass | Partial score | Balance contribution | Item contribution | Ignored-ID contribution | Status contribution | Failure tags | Transcript |
|---|---:|---:|---:|---:|---:|---:|---|---|
| task_01_idempotency_ooo | PASS | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | — | [trial 1](../../transcripts/dry-run_oracle-reference/task_01_idempotency_ooo_trial_1.json) |
| task_02_retro_proration_cooling | PASS | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | — | [trial 1](../../transcripts/dry-run_oracle-reference/task_02_retro_proration_cooling_trial_1.json) |
| task_03_coupon_floor_tax_cap | PASS | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | — | [trial 1](../../transcripts/dry-run_oracle-reference/task_03_coupon_floor_tax_cap_trial_1.json) |
| task_04_fx_chargeback_reversal | PASS | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | — | [trial 1](../../transcripts/dry-run_oracle-reference/task_04_fx_chargeback_reversal_trial_1.json) |
| task_05_tiered_usage_retro_credit | PASS | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | — | [trial 1](../../transcripts/dry-run_oracle-reference/task_05_tiered_usage_retro_credit_trial_1.json) |
| task_06_leap_year_dst_cutover | PASS | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | — | [trial 1](../../transcripts/dry-run_oracle-reference/task_06_leap_year_dst_cutover_trial_1.json) |
| task_07_negative_control_clean_audit | PASS | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | — | [trial 1](../../transcripts/dry-run_oracle-reference/task_07_negative_control_clean_audit_trial_1.json) |
| task_08_asc606_multi_rule_cascade | PASS | 1.0000 | 0.5000 | 0.2500 | 0.1500 | 0.1000 | — | [trial 1](../../transcripts/dry-run_oracle-reference/task_08_asc606_multi_rule_cascade_trial_1.json) |

### dry-run/simulated-balance-offset-a

| Task | Strict pass | Partial score | Balance contribution | Item contribution | Ignored-ID contribution | Status contribution | Failure tags | Transcript |
|---|---:|---:|---:|---:|---:|---:|---|---|
| task_01_idempotency_ooo | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-a/task_01_idempotency_ooo_trial_1.json) |
| task_02_retro_proration_cooling | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-a/task_02_retro_proration_cooling_trial_1.json) |
| task_03_coupon_floor_tax_cap | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-a/task_03_coupon_floor_tax_cap_trial_1.json) |
| task_04_fx_chargeback_reversal | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-a/task_04_fx_chargeback_reversal_trial_1.json) |
| task_05_tiered_usage_retro_credit | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-a/task_05_tiered_usage_retro_credit_trial_1.json) |
| task_06_leap_year_dst_cutover | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-a/task_06_leap_year_dst_cutover_trial_1.json) |
| task_07_negative_control_clean_audit | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-a/task_07_negative_control_clean_audit_trial_1.json) |
| task_08_asc606_multi_rule_cascade | FAIL | 0.7500 | 0.2500 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-a/task_08_asc606_multi_rule_cascade_trial_1.json) |

### dry-run/simulated-balance-offset-b

| Task | Strict pass | Partial score | Balance contribution | Item contribution | Ignored-ID contribution | Status contribution | Failure tags | Transcript |
|---|---:|---:|---:|---:|---:|---:|---|---|
| task_01_idempotency_ooo | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-b/task_01_idempotency_ooo_trial_1.json) |
| task_02_retro_proration_cooling | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-b/task_02_retro_proration_cooling_trial_1.json) |
| task_03_coupon_floor_tax_cap | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-b/task_03_coupon_floor_tax_cap_trial_1.json) |
| task_04_fx_chargeback_reversal | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-b/task_04_fx_chargeback_reversal_trial_1.json) |
| task_05_tiered_usage_retro_credit | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-b/task_05_tiered_usage_retro_credit_trial_1.json) |
| task_06_leap_year_dst_cutover | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-b/task_06_leap_year_dst_cutover_trial_1.json) |
| task_07_negative_control_clean_audit | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-b/task_07_negative_control_clean_audit_trial_1.json) |
| task_08_asc606_multi_rule_cascade | FAIL | 0.8333 | 0.3333 | 0.2500 | 0.1500 | 0.1000 | LEDGER_BALANCE_MISMATCH | [trial 1](../../transcripts/dry-run_simulated-balance-offset-b/task_08_asc606_multi_rule_cascade_trial_1.json) |

## Unscored requests

No unscored requests were recorded.

## Interpretation and limits

Strict pass is binary: the response must be exactly one JSON object (raw or a single JSON fence), account ID and cutoff must match, the output must follow the exact schema, all six balances must match to the cent, reconciling items must match exactly at F1 1.0, ignored IDs must match exactly, and final status must match.
Mismatch tags describe observed output differences; they do not infer the model's internal reasoning.
Strict pass rate is over returned, scored responses; coverage reports returned responses divided by requested responses. pass@k and pass^k use the complete task set, so missing responses do not count as passes. With one trial per task, pass@k and pass^k both equal the observed fraction of tasks with a strict pass. Repeated trials are needed to estimate sampling-sensitive pass@k/pass^k behavior.
