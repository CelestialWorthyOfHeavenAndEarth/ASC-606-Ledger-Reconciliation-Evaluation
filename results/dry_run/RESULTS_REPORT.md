# Evaluation Results

Generated: 2026-11-08T18:49:23Z
Run type: oracle and simulated flaw profiles (no API calls)

## Model summary

| Model ID | Responses | Coverage | Strict pass rate* | Mean partial score | pass@k | pass^k | Mean latency (s) | Total cost ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dry-run/oracle-reference | 24/24 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.000 | 0.000000 |
| dry-run/simulated-balance-offset-a | 24/24 | 100.0% | 0.0% | 75.0% | 0.0% | 0.0% | 0.000 | 0.000000 |
| dry-run/simulated-balance-offset-b | 24/24 | 100.0% | 0.0% | 83.3% | 0.0% | 0.0% | 0.000 | 0.000000 |

## Task-by-task matrix

| Task | dry-run/oracle-reference | dry-run/simulated-balance-offset-a | dry-run/simulated-balance-offset-b |
|---|---|---|---|
| task_01_idempotency_ooo | 3/3 pass; — | 0/3 pass; LEDGER_BALANCE_MISMATCH | 0/3 pass; LEDGER_BALANCE_MISMATCH |
| task_02_retro_proration_cooling | 3/3 pass; — | 0/3 pass; LEDGER_BALANCE_MISMATCH | 0/3 pass; LEDGER_BALANCE_MISMATCH |
| task_03_coupon_floor_tax_cap | 3/3 pass; — | 0/3 pass; LEDGER_BALANCE_MISMATCH | 0/3 pass; LEDGER_BALANCE_MISMATCH |
| task_04_fx_chargeback_reversal | 3/3 pass; — | 0/3 pass; LEDGER_BALANCE_MISMATCH | 0/3 pass; LEDGER_BALANCE_MISMATCH |
| task_05_tiered_usage_retro_credit | 3/3 pass; — | 0/3 pass; LEDGER_BALANCE_MISMATCH | 0/3 pass; LEDGER_BALANCE_MISMATCH |
| task_06_leap_year_dst_cutover | 3/3 pass; — | 0/3 pass; LEDGER_BALANCE_MISMATCH | 0/3 pass; LEDGER_BALANCE_MISMATCH |
| task_07_negative_control_clean_audit | 3/3 pass; — | 0/3 pass; LEDGER_BALANCE_MISMATCH | 0/3 pass; LEDGER_BALANCE_MISMATCH |
| task_08_asc606_multi_rule_cascade | 3/3 pass; — | 0/3 pass; LEDGER_BALANCE_MISMATCH | 0/3 pass; LEDGER_BALANCE_MISMATCH |

`Strict pass rate*` is computed over scored responses. `pass@k` and `pass^k` use the full task set, so an unscored task contributes no pass. A cost of `N/A` means the provider did not report cost and no token rates were configured.
