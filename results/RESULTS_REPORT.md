# Evaluation Results

Generated: 2026-11-08T20:20:38Z
Run type: live provider run

## Model summary

| Model ID | Responses | Coverage | Strict pass rate* | Mean partial score | pass@k | pass^k | Mean latency (s) | Total cost ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| nvidia/nemotron-3.5-lightning:free | 8/8 | 100.0% | 0.0% | 46.5% | 0.0% | 0.0% | 3.947 | 0.000000 |
| nvidia/nemotron-3.5-super-vl:free | 8/8 | 100.0% | 0.0% | 65.0% | 0.0% | 0.0% | 2.328 | 0.000000 |
| dots-studio/dots-3-note-preview:free | 8/8 | 100.0% | 0.0% | 85.1% | 0.0% | 0.0% | 11.263 | 0.000000 |
| xingchen-agi/xing4.0-29b-a4b:free | 8/8 | 100.0% | 0.0% | 55.6% | 0.0% | 0.0% | 9.580 | 0.000000 |
| cohere/north-mini-code:free | 8/8 | 100.0% | 0.0% | 44.6% | 0.0% | 0.0% | 1.837 | 0.000000 |

## Task-by-task matrix

| Task | nvidia/nemotron-3.5-lightning:free | nvidia/nemotron-3.5-super-vl:free | dots-studio/dots-3-note-preview:free | xingchen-agi/xing4.0-29b-a4b:free | cohere/north-mini-code:free |
|---|---|---|---|---|---|
| task_01_idempotency_ooo | 0/1 pass; IGNORED_EVENT_ID_MISMATCH,LEDGER_BALANCE_MISMATCH | 0/1 pass; IGNORED_EVENT_ID_MISMATCH,LEDGER_BALANCE_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,IGNORED_EVENT_ID_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,IGNORED_EVENT_ID_MISMATCH |
| task_02_retro_proration_cooling | 0/1 pass; EXTRA_RECONCILIATION_ITEM,IGNORED_EVENT_ID_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; LEDGER_BALANCE_MISMATCH,MISSING_RECONCILIATION_ITEM |
| task_03_coupon_floor_tax_cap | 0/1 pass; EXTRA_RECONCILIATION_ITEM,IGNORED_EVENT_ID_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; OUTPUT_FORMAT_VIOLATION | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH |
| task_04_fx_chargeback_reversal | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; LEDGER_BALANCE_MISMATCH,MISSING_RECONCILIATION_ITEM | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; JSON_FORMAT_ERROR |
| task_05_tiered_usage_retro_credit | 0/1 pass; EXTRA_RECONCILIATION_ITEM,IGNORED_EVENT_ID_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; OUTPUT_FORMAT_VIOLATION | 0/1 pass; EXTRA_RECONCILIATION_ITEM,IGNORED_EVENT_ID_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH |
| task_06_leap_year_dst_cutover | 0/1 pass; EXTRA_RECONCILIATION_ITEM,IGNORED_EVENT_ID_MISMATCH | 0/1 pass; LEDGER_BALANCE_MISMATCH | 0/1 pass; OUTPUT_FORMAT_VIOLATION | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; LEDGER_BALANCE_MISMATCH |
| task_07_negative_control_clean_audit | 0/1 pass; LEDGER_BALANCE_MISMATCH | 0/1 pass; LEDGER_BALANCE_MISMATCH | 0/1 pass; LEDGER_BALANCE_MISMATCH,OUTPUT_FORMAT_VIOLATION | 0/1 pass; LEDGER_BALANCE_MISMATCH | 0/1 pass; LEDGER_BALANCE_MISMATCH |
| task_08_asc606_multi_rule_cascade | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,LEDGER_BALANCE_MISMATCH | 0/1 pass; EXTRA_RECONCILIATION_ITEM,MISSING_RECONCILIATION_ITEM | 0/1 pass; LEDGER_BALANCE_MISMATCH,MISSING_RECONCILIATION_ITEM | 0/1 pass; IGNORED_EVENT_ID_MISMATCH,LEDGER_BALANCE_MISMATCH |

`Strict pass rate*` is computed over scored responses. `pass@k` and `pass^k` use the full task set, so an unscored task contributes no pass. A cost of `N/A` means the provider did not report cost and no token rates were configured.
