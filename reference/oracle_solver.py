"""Synthetic task generator and deterministic accounting oracle.

All monetary values use Decimal and ROUND_HALF_EVEN. Run this module to regenerate
the eight task prompts and their reference outputs.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CENT = Decimal("0.01")
BALANCE_FIELDS = (
    "net_cash_collected", "customer_wallet_balance", "recognized_revenue",
    "deferred_revenue", "tax_liability", "fx_realized_gain_loss",
)


def D(value: Any) -> Decimal:
    return Decimal(str(value))


def q2(value: Any) -> Decimal:
    return D(value).quantize(CENT, rounding=ROUND_HALF_EVEN)


def iso(day: int, month: int = 3, year: int = 2026, hour: int = 0, minute: int = 0, second: int = 0) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"


def event(event_id: str, effective_at: str, received_at: str, sequence_no: int,
          event_type: str, idempotency_key: str | None = None, **fields: Any) -> dict[str, Any]:
    row = {
        "event_id": event_id,
        "idempotency_key": idempotency_key or f"key_{event_id}",
        "effective_at": effective_at,
        "received_at": received_at,
        "sequence_no": sequence_no,
        "event_type": event_type,
    }
    row.update(fields)
    return row


UNIVERSAL_RULES = [
    "Event Ordering: process events in ascending effective_at (ISO-8601 UTC); break exact timestamp ties by sequence_no ascending. received_at is only for choosing the earliest duplicate and deciding whether a notice deadline was met relative to effective_at.",
    "Idempotency Deduplication: among events sharing idempotency_key, apply only the event with earliest received_at (tie-break by sequence_no). Put every later retry's event_id in ignored_event_ids and add one DUPLICATE_IGNORED reconciling item whose amount_impact_usd is that duplicate's gross USD amount.",
    "Intermediate Rounding: round every discrete monetary calculation, including proration daily rates, discount, tax, and FX conversion, to USD 0.01 using Banker's Rounding (ROUND_HALF_EVEN) before using it in a later calculation.",
    "ASC 606 Revenue Recognition (Daily Proration): for a billing cycle with N days and D elapsed days at audit_period_end, recognized_revenue = ROUND_HALF_EVEN(net pretax consideration * D / N, 0.01), and deferred_revenue = net pretax consideration - recognized_revenue. Use exact UTC day counts unless a task explicitly defines local calendar-day billing boundaries, in which case use those stated boundaries.",
    "Cutoff: only effective events at or before audit_period_end affect balances. Future-effective events remain visible in the input but have no effect on the as-of output.",
    "Output only one JSON object matching the exact schema below. Use numeric USD amounts, two decimal places, all required keys, and no additional top-level keys.",
]

OUTPUT_SCHEMA = {
    "account_id": "string",
    "audit_period_end": "YYYY-MM-DDTHH:MM:SSZ",
    "ledger_balances_usd": {
        "net_cash_collected": 0.00,
        "customer_wallet_balance": 0.00,
        "recognized_revenue": 0.00,
        "deferred_revenue": 0.00,
        "tax_liability": 0.00,
        "fx_realized_gain_loss": 0.00,
    },
    "reconciling_items": [
        {"event_id": "string", "category": "DUPLICATE_IGNORED | RETROACTIVE_PRORATION | COUPON_FLOOR_CAPPED | COOLING_OFF_REFUND | FX_SETTLEMENT_DIFF | CHARGEBACK_FEE_UNRECOVERED | LATE_USAGE_REBILL | POLICY_VIOLATION_HOLD", "amount_impact_usd": 0.00}
    ],
    "ignored_event_ids": ["evt_..."],
    "final_subscription_status": "ACTIVE | CANCELED | PAST_DUE | SUSPENDED_DISPUTE",
}


def _task(task_id: str, title: str, difficulty: str, account_id: str, audit_end: str,
          scenario: str, policies: list[str], events: list[dict[str, Any]], case: dict[str, Any]) -> dict[str, Any]:
    if not 12 <= len(events) <= 25:
        raise ValueError(f"{task_id}: expected 12-25 events, got {len(events)}")
    task = {
        "task_id": task_id,
        "title": title,
        "difficulty": difficulty,
        "account_id": account_id,
        "audit_period_end": audit_end,
        "scenario": scenario,
        "governing_accounting_asc_606_ledger_specification": UNIVERSAL_RULES,
        "policy_rules": policies,
        "events": events,
        "metadata": {"case": case, "dry_run_balance_mutations": {}},
    }
    task["prompt"] = make_prompt(task)
    return task


def make_prompt(task: dict[str, Any]) -> str:
    visible_input = {
        "account_id": task["account_id"],
        "audit_period_end": task["audit_period_end"],
        "events": task["events"],
    }
    return "\n".join([
        f"# {task['title']} ({task['difficulty']})",
        "## Scenario",
        task["scenario"],
        "## Governing Accounting & ASC 606 Ledger Specification",
        *[f"{index}. {rule}" for index, rule in enumerate(task["governing_accounting_asc_606_ledger_specification"], 1)],
        "## Task-Specific Policies",
        *[f"{index}. {rule}" for index, rule in enumerate(task["policy_rules"], 1)],
        "## Input data (complete event stream)",
        "```json",
        json.dumps(visible_input, indent=2, ensure_ascii=False),
        "```",
        "## Required output JSON schema",
        "Return exactly this JSON shape; preserve every key, use an array even when empty, and use two-decimal USD values:",
        "```json",
        json.dumps(OUTPUT_SCHEMA, indent=2),
        "```",
    ])


def build_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []

    # 1. The late-arriving seat purchase is effective before the credit-note cutoff.
    e1 = [
        event("evt_01_invoice", iso(1), iso(1, hour=0, minute=1), 1, "invoice_issued", gross_usd="1200.00", role="base_subscription"),
        event("evt_02_pay_a", iso(2), iso(2, hour=10), 2, "payment_settled", amount_usd="900.00", role="base_payment_a"),
        event("evt_03_pay_b", iso(3), iso(3, hour=10), 3, "payment_settled", amount_usd="300.00", gross_usd="300.00", idempotency_key="pay_base_300", role="base_payment_b"),
        event("evt_04_pay_b_retry", iso(3), iso(4, hour=8), 4, "payment_settled", amount_usd="300.00", gross_usd="300.00", idempotency_key="pay_base_300", role="retry"),
        event("evt_05_seat_addon", iso(11), iso(19), 5, "seat_addon.purchased", monthly_rate_usd="300.00", cycle_days=30, remaining_days=20, role="addon"),
        event("evt_06_addon_payment", iso(11), iso(11, hour=2), 6, "payment_settled", amount_usd="200.00", role="addon_payment"),
        event("evt_07_credit_note", iso(16), iso(16, hour=1), 7, "credit_note.issued", requested_credit_usd="250.00", target_role="addon", role="credit"),
        event("evt_08_invoice_retry", iso(1), iso(5), 8, "invoice_issued", gross_usd="0.00", idempotency_key="invoice_base_retry", role="invoice_retry_original"),
        event("evt_09_invoice_retry2", iso(1), iso(6), 9, "invoice_issued", gross_usd="0.00", idempotency_key="invoice_base_retry", role="retry"),
        event("evt_10_usage", iso(12), iso(12), 10, "usage_recorded", units=120, amount_usd="0.00"),
        event("evt_11_plan_check", iso(14), iso(14), 11, "subscription_status", status="ACTIVE"),
        event("evt_12_payment_notice", iso(15), iso(15), 12, "payment_notice", amount_usd="0.00"),
        event("evt_13_tax_recalc", iso(17), iso(17), 13, "tax_recalculated", amount_usd="0.00"),
        event("evt_14_audit_marker", iso(18), iso(18), 14, "audit_marker", label="cycle_review"),
    ]
    tasks.append(_task("task_01_idempotency_ooo", "Idempotency and out-of-order credit note", "Medium-Easy", "acct_1001", iso(19),
        "A B2B SaaS account has a $1,200 monthly plan on a 30-day cycle. A $300/month seat add-on is effective on Day 10, but its webhook arrives after a Day 15 credit note. Two webhook retries collide by idempotency_key; one is a $300 payment retry.", [
            "The base subscription is $1,200 for March 1 through March 31 (30 daily units for this synthetic task); the audit cutoff is 18 elapsed days into that cycle.",
            "Prorate the $300 monthly seat add-on for the 20 remaining days: round the daily rate to cents, then multiply by 20.",
            "A credit note targeting the add-on is capped at the total add-on charge effective on or before its effective_at. Apply the capped credit as a cash refund; it reduces net_cash_collected and add-on transaction price.",
            "Recognize base revenue over the 30-day cycle. Recognize any net add-on consideration over its 20-day service window; the audit cutoff is 8 days into that window. The final status is ACTIVE unless an effective status event changes it.",
        ], e1, {"engine": "task_01"}))

    # 2. Mid-cycle upgrade, backdated downgrade, late cancellation.
    e2 = [
        event("evt_02_01_signup", "2026-03-01T00:00:00Z", "2026-03-01T00:00:02Z", 1, "subscription_started", initial_monthly_rate_usd="600.00"),
        event("evt_02_02_invoice", "2026-03-01T00:00:00Z", "2026-03-01T00:00:03Z", 2, "invoice_issued", amount_usd="600.00"),
        event("evt_02_03_payment", "2026-03-01T01:00:00Z", "2026-03-01T01:00:01Z", 3, "payment_settled", amount_usd="600.00"),
        event("evt_02_04_upgrade", "2026-03-07T00:00:00Z", "2026-03-07T00:00:03Z", 4, "seat_addon.purchased", monthly_delta_usd="300.00", remaining_days=25, cycle_days=30),
        event("evt_02_05_upgrade_payment", "2026-03-07T00:05:00Z", "2026-03-07T00:05:01Z", 5, "payment_settled", amount_usd="250.00"),
        event("evt_02_06_downgrade", "2026-03-12T00:00:00Z", "2026-03-17T10:00:00Z", 6, "plan_downgrade", prior_monthly_rate_usd="900.00", new_monthly_rate_usd="450.00", remaining_days=20, cycle_days=30),
        event("evt_02_07_cancel", "2026-03-21T00:00:00Z", "2026-03-21T00:00:03Z", 7, "subscription_canceled", initial_subscription_at="2026-03-01T00:00:00Z", cycle_days=30, elapsed_days=20),
        event("evt_02_08_wallet", "2026-03-21T00:00:01Z", "2026-03-21T00:00:04Z", 8, "wallet_policy_marker", amount_usd="0.00"),
        event("evt_02_09_notice", "2026-03-12T00:00:00Z", "2026-03-17T10:00:01Z", 9, "plan_notice_received", notice_deadline_met=False),
        event("evt_02_10_tax", "2026-03-21T00:00:00Z", "2026-03-21T00:00:05Z", 10, "tax_recalculated", amount_usd="0.00"),
        event("evt_02_11_usage", "2026-03-18T00:00:00Z", "2026-03-18T00:00:01Z", 11, "usage_recorded", units=40, amount_usd="0.00"),
        event("evt_02_12_audit", "2026-03-21T00:00:00Z", "2026-03-21T00:00:06Z", 12, "audit_marker", label="cancellation_cutoff"),
    ]
    tasks.append(_task("task_02_retro_proration_cooling", "Retroactive proration and cooling-off boundary", "Medium", "acct_2002", "2026-03-21T00:00:00Z",
        "A Pro subscription begins March 1, 2026 at $600/month. A $300/month seat upgrade takes effect on Day 6. A downgrade webhook received on Day 16 is backdated to Day 11, and the customer cancels on Day 20.", [
            "The upgrade adds $300/month for the 25 remaining days of the 30-day cycle, billed as a rounded prorated charge.",
            "The backdated downgrade changes the effective monthly rate from $900 to $450 for 20 remaining days. Its credit is ($900 - $450) * 20/30, rounded to cents, and is posted to the customer wallet, never returned as cash.",
            "A cancellation within 14 exact days of initial subscription creation refunds unused prepaid balance to cash. A cancellation later than 14 days does not refund cash; transfer unused deferred consideration to the wallet and set deferred revenue to zero.",
            "Revenue is earned by the effective daily plan schedule: $600/day-rate for Days 1-6, $900/day-rate for Days 6-11, and $450/day-rate for Days 11-20. At cancellation, recognize earned consideration and transfer the remaining net deferred amount to wallet.",
        ], e2, {"engine": "task_02"}))

    # 3. Coupon cap, commitment floor, tax, then wallet.
    e3 = []
    e3 += [event("evt_03_01_contract", "2026-06-01T00:00:00Z", "2026-06-01T00:00:01Z", 1, "contract_started", minimum_pretax_commitment_usd="2600.00")]
    e3 += [event("evt_03_02_base_invoice", "2026-06-01T00:00:00Z", "2026-06-01T00:00:02Z", 2, "invoice_line", amount_usd="2500.00", line_type="base")]
    e3 += [event("evt_03_03_usage_invoice", "2026-06-01T00:00:00Z", "2026-06-01T00:00:03Z", 3, "invoice_line", amount_usd="850.00", line_type="overage")]
    e3 += [event("evt_03_04_coupon", "2026-06-02T00:00:00Z", "2026-06-02T00:00:01Z", 4, "coupon_applied", percent="30", max_discount_usd="900.00")]
    e3 += [event("evt_03_05_tax", "2026-06-02T00:00:01Z", "2026-06-02T00:00:02Z", 5, "tax_calculated", rate_percent="8.875")]
    e3 += [event("evt_03_06_wallet_open", "2026-06-02T00:00:02Z", "2026-06-02T00:00:03Z", 6, "wallet_opening_balance", amount_usd="400.00")]
    e3 += [event("evt_03_07_payment", "2026-06-03T00:00:00Z", "2026-06-03T00:00:01Z", 7, "payment_settled", amount_usd="2430.75")]
    e3 += [event("evt_03_08_usage", "2026-06-04T00:00:00Z", "2026-06-04T00:00:01Z", 8, "usage_recorded", units=500)]
    for i in range(9, 17):
        e3.append(event(f"evt_03_{i:02d}_audit", f"2026-06-{min(i, 15):02d}T00:00:00Z", f"2026-06-{min(i, 15):02d}T00:00:01Z", i, "invoice_audit_marker", marker=f"line_{i}"))
    tasks.append(_task("task_03_coupon_floor_tax_cap", "Coupon floor, tax, and wallet precedence", "Hard", "acct_3003", "2026-06-16T00:00:00Z",
        "An enterprise invoice has $2,500 base charge and $850 overage, a 30% promotional coupon capped at $900, a $2,600 minimum pre-tax commitment floor, a $400 opening wallet, and 8.875% sales tax.", [
            "Combine the $2,500 base and $850 usage lines before discount. Compute 30% off, first applying the $900 maximum discount, then cap the allowed discount so post-discount pretax subtotal is not below $2,600. Log the prevented discount as COUPON_FLOOR_CAPPED with positive amount_impact_usd.",
            "Compute sales tax at 8.875% on the post-coupon pretax subtotal and round to cents.",
            "Apply the $400 opening wallet only after tax. It reduces cash collected, but does not reduce tax liability or recognized revenue.",
            "The service cycle is 30 days, starts June 1, and has 15 elapsed days at audit_period_end. Recognize/defer the post-coupon pretax consideration using the universal daily proration rule. The account remains ACTIVE.",
        ], e3, {"engine": "task_03"}))

    # 4. EUR settlement, refund, chargeback and win.
    e4 = [
        event("evt_04_01_invoice", "2026-07-01T00:00:00Z", "2026-07-01T00:00:02Z", 1, "invoice_issued", base_eur="4000.00", vat_eur="800.00", invoice_fx="1.0850"),
        event("evt_04_02_payment", "2026-07-04T00:00:00Z", "2026-07-04T00:00:01Z", 2, "payment_settled", amount_eur="4800.00", settlement_fx="1.0920"),
        event("evt_04_03_fx_notice", "2026-07-04T00:00:02Z", "2026-07-04T00:00:03Z", 3, "fx_settlement_notice", amount_usd="33.60"),
        event("evt_04_04_refund", "2026-07-05T00:00:00Z", "2026-07-05T00:00:01Z", 4, "partial_refund", total_eur="1000.00", base_eur="833.33", vat_eur="166.67", refund_fx="1.0780"),
        event("evt_04_05_refund_tax", "2026-07-05T00:00:01Z", "2026-07-05T00:00:02Z", 5, "vat_reversal", amount_eur="166.67"),
        event("evt_04_06_dispute", "2026-07-08T00:00:00Z", "2026-07-08T00:00:01Z", 6, "chargeback_opened", principal_eur="3800.00", dispute_fx="1.1000"),
        event("evt_04_07_fee", "2026-07-08T00:00:01Z", "2026-07-08T00:00:02Z", 7, "chargeback_fee", amount_usd="15.00"),
        event("evt_04_08_reversal", "2026-07-18T00:00:00Z", "2026-07-18T00:00:01Z", 8, "chargeback_won", principal_eur="3800.00", reversal_fx="1.0950"),
        event("evt_04_09_notice", "2026-07-18T00:00:01Z", "2026-07-18T00:00:02Z", 9, "dispute_status", status="WON"),
        event("evt_04_10_fx", "2026-07-19T00:00:00Z", "2026-07-19T00:00:01Z", 10, "fx_close_marker"),
        event("evt_04_11_vat", "2026-07-19T00:00:01Z", "2026-07-19T00:00:02Z", 11, "vat_close_marker"),
        event("evt_04_12_audit", "2026-07-20T00:00:00Z", "2026-07-20T00:00:01Z", 12, "audit_marker"),
    ]
    tasks.append(_task("task_04_fx_chargeback_reversal", "FX settlement and chargeback reversal", "Hard", "acct_4004", "2026-07-20T00:00:00Z",
        "A European subsidiary invoices €4,000 plus €800 VAT at 1.0850 USD/EUR. The €4,800 payment settles at 1.0920. The account receives a proportional €1,000 refund at 1.0780, then a €3,800 chargeback at 1.1000, which is won ten days later at 1.0950. A $15 fee is not recoverable.", [
            "Translate invoice principal and VAT separately at invoice FX. Recognize invoice principal in revenue and VAT as tax liability.",
            "The payment settlement creates FX gain/loss equal to USD cash received minus the invoice's USD carrying value. The refund reverses base and VAT pro rata at invoice FX; compare the reversed carrying value with USD cash refunded at refund_fx to calculate refund FX gain/loss.",
            "A chargeback temporarily removes the disputed USD principal from cash. On a won dispute, restore the principal at reversal_fx. The realized FX loss on the dispute lifecycle is disputed principal times (dispute_fx - reversal_fx). Keep the $15 fee deducted from cash and report it as CHARGEBACK_FEE_UNRECOVERED.",
            "Reverse the partial refund's proportional VAT at invoice FX. All service has been delivered by the audit cutoff, so deferred revenue is zero. A won dispute leaves status ACTIVE.",
        ], e4, {"engine": "task_04"}))

    # 5. Fifteen usage batches across two periods, one late batch and retro credit.
    e5: list[dict[str, Any]] = []
    e5.append(event("evt_05_period1_open", "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z", 1, "billing_period_opened", period="P1", cycle_days=31))
    p1_batches = [1500, 1500, 1500, 1500, 1500, 1500, 3000]  # 12,000 timely units
    for idx, units in enumerate(p1_batches, 2):
        day = idx
        e5.append(event(f"evt_05_p1_usage_{idx:02d}", f"2026-01-{day:02d}T12:00:00Z", f"2026-01-{day:02d}T12:01:00Z", idx, "usage_batch", period="P1", units=units))
    e5.append(event("evt_05_p1_late_batch", "2026-01-20T12:00:00Z", "2026-02-05T09:00:00Z", 9, "usage_batch", period="P1", units=3000, late_arrival=True))
    e5.append(event("evt_05_p1_invoice", "2026-02-01T00:00:00Z", "2026-02-01T00:00:01Z", 10, "usage_invoice", period="P1", amount_usd="675.00"))
    e5.append(event("evt_05_p1_payment", "2026-02-02T00:00:00Z", "2026-02-02T00:00:01Z", 11, "payment_settled", amount_usd="675.00", period="P1"))
    e5.append(event("evt_05_sla_credit", "2026-02-06T00:00:00Z", "2026-02-06T00:00:01Z", 12, "sla_usage_credit", period="P1", units=12500))
    e5.append(event("evt_05_period2_open", "2026-02-01T00:00:00Z", "2026-02-01T00:00:02Z", 13, "billing_period_opened", period="P2", cycle_days=30))
    p2_batches = [7000, 7000, 7000, 7000, 7000, 7000, 10000]  # 52,000 units
    for idx, units in enumerate(p2_batches, 14):
        day = min(idx - 12, 15)
        e5.append(event(f"evt_05_p2_usage_{idx-13:02d}", f"2026-02-{day:02d}T13:00:00Z", f"2026-02-{day:02d}T13:01:00Z", idx, "usage_batch", period="P2", units=units))
    e5.append(event("evt_05_p2_invoice", "2026-02-10T00:00:00Z", "2026-02-10T00:00:01Z", 21, "usage_invoice", period="P2", amount_usd="1940.00"))
    e5.append(event("evt_05_p2_payment", "2026-02-11T00:00:00Z", "2026-02-11T00:00:01Z", 22, "payment_settled", amount_usd="1940.00", period="P2"))
    e5.append(event("evt_05_cutoff", "2026-02-16T00:00:00Z", "2026-02-16T00:00:01Z", 23, "audit_cutoff_marker"))
    tasks.append(_task("task_05_tiered_usage_retro_credit", "Tiered usage and retroactive SLA credit", "Hard", "acct_5005", "2026-02-16T00:00:00Z",
        "Graduated marginal usage billing spans two periods. Fifteen usage batches total 15,000 units in P1 (including a late 3,000-unit batch) and 52,000 units in P2. A retroactive SLA credit removes 12,500 P1 units.", [
            "Use graduated marginal tiers separately for each billing period: units 1-10,000 at $0.05, units 10,001-50,000 at $0.035, and units above 50,000 at $0.02. Never apply one all-units rate to the entire period.",
            "Include every usage batch according to effective period, including a batch received in P2 whose effective period is P1. The P1 invoice of $675 and P2 invoice of $1,940 have already been collected.",
            "The 12,500-unit SLA credit unwinds P1's highest marginal units first. Credit $0.035 for the 5,000 P1 units in Tier 2, then $0.05 for the next 7,500 Tier 1 units. Credit is issued to customer_wallet_balance and reduces P1 revenue; log it as LATE_USAGE_REBILL with negative amount impact.",
        "P1 is fully delivered at audit cutoff. P2 is a 30-day service cycle with 15 days elapsed. Both invoices have been collected by the cutoff. Recognize net P1 revenue in full and half of P2 revenue; defer the remainder. Status is ACTIVE.",
        ], e5, {"engine": "task_05"}))

    # 6. New York monthly anchor, leap February, DST boundary batches.
    e6 = [
        event("evt_06_anchor", "2024-01-31T05:00:00Z", "2024-01-31T05:00:01Z", 1, "subscription_started", anchor_local="2024-01-31T00:00:00-05:00", timezone="America/New_York", monthly_price_usd="290.00"),
        event("evt_06_feb_invoice", "2024-01-31T05:00:00Z", "2024-01-31T05:00:02Z", 2, "monthly_invoice", cycle="2024-01-31/2024-02-29", amount_usd="290.00"),
        event("evt_06_feb_payment", "2024-01-31T06:00:00Z", "2024-01-31T06:00:01Z", 3, "payment_settled", amount_usd="290.00"),
        event("evt_06_feb_boundary_usage", "2024-03-01T04:30:00Z", "2024-03-02T09:00:00Z", 4, "usage_batch", units=10, rate_usd="1.00", timezone="America/New_York"),
        event("evt_06_feb_usage_invoice", "2024-03-02T09:00:00Z", "2024-03-02T09:00:01Z", 5, "usage_invoice", amount_usd="10.00", cycle="2024-01-31/2024-02-29"),
        event("evt_06_feb_usage_payment", "2024-03-03T00:00:00Z", "2024-03-03T00:00:01Z", 6, "payment_settled", amount_usd="10.00"),
        event("evt_06_mar_renewal", "2024-02-29T05:00:00Z", "2024-02-29T05:00:01Z", 7, "subscription_renewed", next_cycle="2024-02-29/2024-03-31", local_anchor="2024-02-29T00:00:00-05:00"),
        event("evt_06_mar_invoice", "2024-02-29T05:00:00Z", "2024-02-29T05:00:02Z", 8, "monthly_invoice", cycle="2024-02-29/2024-03-31", amount_usd="290.00"),
        event("evt_06_mar_payment", "2024-02-29T06:00:00Z", "2024-02-29T06:00:01Z", 9, "payment_settled", amount_usd="290.00"),
        event("evt_06_dst", "2024-03-10T07:00:00Z", "2024-03-10T07:00:01Z", 10, "timezone_offset_change", from_offset="-05:00", to_offset="-04:00", zone="America/New_York"),
        event("evt_06_mar_boundary_usage", "2024-04-01T03:30:00Z", "2024-04-02T08:00:00Z", 11, "usage_batch", units=20, rate_usd="1.00", timezone="America/New_York"),
        event("evt_06_future_usage_invoice", "2024-04-02T08:00:00Z", "2024-04-02T08:00:01Z", 12, "usage_invoice", amount_usd="20.00", cycle="2024-02-29/2024-03-31"),
        event("evt_06_audit", "2024-03-16T04:00:00Z", "2024-04-02T08:00:02Z", 13, "audit_cutoff_marker"),
        event("evt_06_status", "2024-03-16T04:00:00Z", "2024-04-02T08:00:03Z", 14, "subscription_status", status="ACTIVE"),
    ]
    tasks.append(_task("task_06_leap_year_dst_cutover", "Leap year and DST billing cutover", "Hard", "acct_6006", "2024-03-16T04:00:00Z",
        "A New York subscription renews on its local monthly anchor from January 31, 2024 across leap-year February and the March 10 DST shift. Usage at 2024-03-01T04:30Z is still February 29 local time; usage at 2024-04-01T03:30Z is still March 31 local time.", [
            "Use America/New_York local monthly anchor boundaries: Jan 31 to Feb 29 is 29 calendar days, and Feb 29 to Mar 31 is 31 calendar days. The second interval crosses the spring DST change; do not use a fixed 05:00Z cutoff after DST.",
            "For usage-batch attribution, use the batch's New York local calendar date: local February 29 belongs to the February usage bucket and local March 31 belongs to March, even when the UTC timestamp falls on the next UTC date. This date-based usage attribution is separate from base-fee daily proration across the stated anchor boundaries.",
            "The $290 February and March base invoices have been collected. The 10-unit batch at 2024-03-01T04:30Z belongs to the February cycle (10 * $1 = $10) and is billed and collected before cutoff.",
            "The 20-unit batch at 2024-04-01T03:30Z belongs to March 31 local time but occurs after audit_period_end; exclude its $20 from the as-of balances.",
            "At audit_period_end, the February cycle is complete and 16 of 31 local calendar days have elapsed in the March cycle. Recognize the full February consideration and 16/31 of the March base fee; defer the rest. Status is ACTIVE.",
        ], e6, {"engine": "task_06"}))

    # 7. Deliberate clean negative control: same-value payments are distinct, coupon lands exactly on floor.
    e7 = [
        event("evt_07_signup", "2026-04-01T00:00:00Z", "2026-04-01T00:00:01Z", 1, "subscription_started", initial_subscription_at="2026-04-01T00:00:00Z", cycle_days=30),
        event("evt_07_invoice_a", "2026-04-01T00:00:00Z", "2026-04-01T00:00:02Z", 2, "invoice_issued", invoice_id="inv_A", amount_usd="1500.00"),
        event("evt_07_invoice_b", "2026-04-01T00:00:00Z", "2026-04-01T00:00:03Z", 3, "invoice_issued", invoice_id="inv_B", amount_usd="1500.00"),
        event("evt_07_payment_a", "2026-04-01T12:00:00Z", "2026-04-01T12:00:01Z", 4, "payment_settled", invoice_id="inv_A", amount_usd="1500.00", idempotency_key="pay_inv_A"),
        event("evt_07_payment_b", "2026-04-01T12:00:00Z", "2026-04-01T12:00:02Z", 5, "payment_settled", invoice_id="inv_B", amount_usd="1500.00", idempotency_key="pay_inv_B"),
        event("evt_07_coupon", "2026-04-02T00:00:00Z", "2026-04-02T00:00:01Z", 6, "coupon_applied", gross_pretax_usd="3000.00", discount_usd="400.00", commitment_floor_usd="2600.00"),
        event("evt_07_cancel", "2026-04-15T00:00:01Z", "2026-04-15T00:00:02Z", 7, "subscription_canceled", initial_subscription_at="2026-04-01T00:00:00Z", exact_elapsed_seconds=1209601, cycle_seconds=2592000),
        event("evt_07_floor_check", "2026-04-02T00:00:01Z", "2026-04-02T00:00:02Z", 8, "commitment_floor_check", prevented_discount_usd="0.00"),
        event("evt_07_invoice_notice_a", "2026-04-01T12:00:01Z", "2026-04-01T12:00:03Z", 9, "payment_notice", invoice_id="inv_A"),
        event("evt_07_invoice_notice_b", "2026-04-01T12:00:02Z", "2026-04-01T12:00:04Z", 10, "payment_notice", invoice_id="inv_B"),
        event("evt_07_service", "2026-04-10T00:00:00Z", "2026-04-10T00:00:01Z", 11, "service_delivered", amount_usd="0.00"),
        event("evt_07_tax", "2026-04-15T00:00:01Z", "2026-04-15T00:00:03Z", 12, "tax_close_marker", amount_usd="0.00"),
        event("evt_07_wallet", "2026-04-15T00:00:01Z", "2026-04-15T00:00:04Z", 13, "wallet_close_marker"),
        event("evt_07_audit_14", "2026-04-15T00:00:01Z", "2026-04-15T00:00:05Z", 14, "audit_marker", label="cooling_off_boundary"),
        event("evt_07_audit_15", "2026-04-15T00:00:01Z", "2026-04-15T00:00:06Z", 15, "audit_marker", label="same_amount_invoices"),
        event("evt_07_audit_16", "2026-04-15T00:00:01Z", "2026-04-15T00:00:07Z", 16, "audit_marker", label="no_duplicate"),
        event("evt_07_audit_17", "2026-04-15T00:00:01Z", "2026-04-15T00:00:08Z", 17, "audit_marker", label="floor_exact"),
        event("evt_07_audit_18", "2026-04-15T00:00:01Z", "2026-04-15T00:00:09Z", 18, "audit_marker", label="late_cancel"),
        event("evt_07_audit_19", "2026-04-15T00:00:01Z", "2026-04-15T00:00:10Z", 19, "audit_marker", label="negative_control"),
        event("evt_07_audit_20", "2026-04-15T00:00:01Z", "2026-04-15T00:00:11Z", 20, "audit_marker", label="final"),
    ]
    tasks.append(_task("task_07_negative_control_clean_audit", "Negative control: clean audit boundary", "Medium-Hard", "acct_7007", "2026-04-15T00:00:01Z",
        "A 20-event enterprise ledger contains two $1,500 payments on the same day for distinct invoices with distinct idempotency keys. A $400 coupon takes the $3,000 subtotal exactly to a $2,600 floor with $0 prevented discount. Cancellation occurs 14 days and 1 second after signup, just outside cooling-off.", [
            "The two $1,500 payments are distinct valid payments because their invoice IDs and idempotency keys differ. Do not deduplicate by amount or timestamp.",
            "The $400 coupon reduces $3,000 to exactly the $2,600 minimum commitment floor. The prevented discount is exactly $0.00, so do not report a COUPON_FLOOR_CAPPED item.",
            "Cooling-off is exactly 14 * 24 hours. Cancellation at 1,209,601 seconds is one second outside the window: no cash refund. At cancellation, recognize $2,600 * elapsed_seconds / 2,592,000 using half-even rounding; move all remaining collected consideration, including the $400 overpayment, to customer_wallet_balance and set deferred revenue to zero.",
            "This is a valid clean audit: reconciling_items and ignored_event_ids must both be empty. Final status is CANCELED.",
        ], e7, {"engine": "task_07"}))

    # 8. Multi-rule cascade with migration, discount floor, credit note, dispute hold and duplicate.
    e8 = [
        event("evt_08_01_start", "2026-09-01T00:00:00Z", "2026-09-01T00:00:01Z", 1, "subscription_started", old_monthly_rate_usd="1800.00", cycle_days=30),
        event("evt_08_02_initial_invoice", "2026-09-01T00:00:00Z", "2026-09-01T00:00:02Z", 2, "invoice_issued", amount_usd="1800.00"),
        event("evt_08_03_migration", "2026-09-07T00:00:00Z", "2026-09-17T10:00:00Z", 3, "plan_migration", old_monthly_rate_usd="1800.00", new_monthly_rate_usd="3000.00", remaining_days=24, cycle_days=30),
        event("evt_08_04_migration_adjust", "2026-09-07T00:00:01Z", "2026-09-17T10:00:01Z", 4, "invoice_adjustment", amount_usd="960.00", effective_day=6),
        event("evt_08_05_coupon", "2026-09-17T10:01:00Z", "2026-09-17T10:01:01Z", 5, "coupon_applied", percent="20", max_discount_usd="900.00", commitment_floor_usd="2600.00", gross_subtotal_usd="2760.00"),
        event("evt_08_06_final_invoice", "2026-09-17T10:02:00Z", "2026-09-17T10:02:01Z", 6, "invoice_issued", amount_usd="2600.00", role="net_invoice"),
        event("evt_08_07_payment", "2026-09-17T10:03:00Z", "2026-09-17T10:03:01Z", 7, "payment_settled", amount_usd="2600.00", gross_usd="2600.00", idempotency_key="pay_enterprise_invoice"),
        event("evt_08_08_payment_retry", "2026-09-17T10:03:00Z", "2026-09-17T10:05:00Z", 8, "payment_settled", amount_usd="2600.00", gross_usd="2600.00", idempotency_key="pay_enterprise_invoice"),
        event("evt_08_09_credit", "2026-09-18T08:00:00Z", "2026-09-18T08:00:01Z", 9, "credit_note_writeoff", amount_usd="300.00", treatment="reduce_transaction_price_wallet_credit"),
        event("evt_08_10_dispute", "2026-09-19T00:00:00Z", "2026-09-19T00:00:01Z", 10, "chargeback_opened", amount_usd="600.00", status="OPEN"),
        event("evt_08_11_usage", "2026-09-10T00:00:00Z", "2026-09-10T00:00:01Z", 11, "usage_recorded", units=800),
        event("evt_08_12_status", "2026-09-19T00:00:01Z", "2026-09-19T00:00:02Z", 12, "subscription_status", status="SUSPENDED_DISPUTE"),
        event("evt_08_13_tax", "2026-09-19T00:00:02Z", "2026-09-19T00:00:03Z", 13, "tax_close_marker", amount_usd="0.00"),
        event("evt_08_14_notice", "2026-09-18T00:00:00Z", "2026-09-18T00:00:01Z", 14, "dispute_notice"),
        event("evt_08_15_migration_receipt", "2026-09-17T10:00:00Z", "2026-09-17T10:00:02Z", 15, "migration_receipt"),
        event("evt_08_16_coupon_close", "2026-09-17T10:02:01Z", "2026-09-17T10:02:02Z", 16, "coupon_close_marker"),
        event("evt_08_17_payment_notice", "2026-09-17T10:03:01Z", "2026-09-17T10:03:02Z", 17, "payment_notice"),
        event("evt_08_18_refund_review", "2026-09-18T08:00:01Z", "2026-09-18T08:00:02Z", 18, "credit_review"),
        event("evt_08_19_dispute_review", "2026-09-19T00:00:03Z", "2026-09-19T00:00:04Z", 19, "dispute_review"),
        event("evt_08_20_audit", "2026-09-19T00:00:00Z", "2026-09-19T00:00:05Z", 20, "audit_marker"),
        event("evt_08_21_cycle", "2026-09-19T00:00:00Z", "2026-09-19T00:00:06Z", 21, "billing_cycle_marker", cycle_days=30),
        event("evt_08_22_cutoff", "2026-09-19T00:00:00Z", "2026-09-19T00:00:07Z", 22, "quarter_end_cutoff", elapsed_days=18),
    ]
    tasks.append(_task("task_08_asc606_multi_rule_cascade", "ASC 606 multi-rule quarter-end cascade", "Frontier Stress Test", "acct_8008", "2026-09-19T00:00:00Z",
        "A 30-day enterprise ledger combines a retroactive plan migration received late, duplicate payment retry, coupon floor, partial credit-note write-off, and an open chargeback at an 18/30 quarter-end cutoff.", [
            "The plan is $1,800/month until Day 6, then $3,000/month for the remaining 24 of 30 days. The retroactive migration uplift is ($3,000-$1,800)*24/30 = $960; gross pretax subtotal is $2,760.",
            "Apply the 20% coupon to $2,760, subject to the $900 maximum and $2,600 minimum commitment floor. Actual allowed discount is $160; the prevented part of the coupon is $392 and is a COUPON_FLOOR_CAPPED item.",
            "The final $2,600 invoice is collected once. The later event with the same idempotency_key is a duplicate and must be ignored and logged at its gross USD amount.",
            "An approved $300 partial credit-note write-off reduces transaction price and is added to customer_wallet_balance; it does not refund cash. The net contract consideration is $2,300.",
            "The open $600 chargeback is withdrawn from net_cash_collected; any disputed receivable or claim is outside the six requested balance fields. At Day 18 of 30, ordinary recognized revenue would be $2,300*18/30. Freeze the elapsed-period share ($600*18/30) from recognition and retain it in deferred revenue. Log the disputed amount as POLICY_VIOLATION_HOLD. Status is SUSPENDED_DISPUTE.",
        ], e8, {"engine": "task_08"}))

    return tasks


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def deduplicate(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in events:
        groups.setdefault(str(row["idempotency_key"]), []).append(row)
    applied: list[dict[str, Any]] = []
    ignored: list[str] = []
    recon: list[dict[str, Any]] = []
    for rows in groups.values():
        rows_sorted = sorted(rows, key=lambda r: (_utc(r["received_at"]), int(r["sequence_no"])))
        applied.append(rows_sorted[0])
        for duplicate in rows_sorted[1:]:
            ignored.append(duplicate["event_id"])
            amount = q2(duplicate.get("gross_usd", duplicate.get("amount_usd", "0.00")))
            recon.append({"event_id": duplicate["event_id"], "category": "DUPLICATE_IGNORED", "amount_impact_usd": float(amount)})
    applied.sort(key=lambda r: (_utc(r["effective_at"]), int(r["sequence_no"])))
    ignored.sort()
    recon.sort(key=lambda r: (r["event_id"], r["category"]))
    return applied, ignored, recon


def _base_output(task: dict[str, Any], recon: list[dict[str, Any]], ignored: list[str], status: str = "ACTIVE") -> dict[str, Any]:
    return {
        "account_id": task["account_id"],
        "audit_period_end": task["audit_period_end"],
        "ledger_balances_usd": {field: 0.0 for field in BALANCE_FIELDS},
        "reconciling_items": recon,
        "ignored_event_ids": ignored,
        "final_subscription_status": status,
    }


def _recognized(amount: Decimal, elapsed: Decimal, total: Decimal) -> tuple[Decimal, Decimal]:
    earned = q2(amount * elapsed / total)
    return earned, q2(amount - earned)


def solve_task(task: dict[str, Any]) -> dict[str, Any]:
    cutoff = _utc(task["audit_period_end"])
    in_scope_events = [row for row in task["events"] if _utc(row["effective_at"]) <= cutoff]
    events, ignored, recon = deduplicate(in_scope_events)
    engine = task["metadata"]["case"]["engine"]
    out = _base_output(task, recon, ignored)
    b = out["ledger_balances_usd"]
    by_type: dict[str, list[dict[str, Any]]] = {}
    for row in events:
        by_type.setdefault(row["event_type"], []).append(row)

    if engine == "task_01":
        credit = next(r for r in events if r["event_type"] == "credit_note.issued")
        addon = next(r for r in events if r["event_type"] == "seat_addon.purchased")
        addon_charge = q2(q2(D(addon["monthly_rate_usd"]) / D(addon["cycle_days"])) * D(addon["remaining_days"]))
        eligible = addon_charge if _utc(addon["effective_at"]) <= _utc(credit["effective_at"]) else D("0.00")
        actual_credit = min(q2(credit["requested_credit_usd"]), eligible)
        recon.append({"event_id": credit["event_id"], "category": "RETROACTIVE_PRORATION", "amount_impact_usd": float(q2(-actual_credit))})
        collected = sum((D(r["amount_usd"]) for r in events if r["event_type"] == "payment_settled"), D("0"))
        # The addon payment and base payments are in collected; the cash refund reduces cash.
        b["net_cash_collected"] = float(q2(collected - actual_credit))
        base_rec, base_def = _recognized(D("1200"), D("18"), D("30"))
        addon_net = q2(addon_charge - actual_credit)
        addon_rec, addon_def = _recognized(addon_net, D("8"), D("20"))
        b["recognized_revenue"] = float(q2(base_rec + addon_rec))
        b["deferred_revenue"] = float(q2(base_def + addon_def))
        out["final_subscription_status"] = "ACTIVE"

    elif engine == "task_02":
        starting_cash = sum((D(r["amount_usd"]) for r in events if r["event_type"] == "payment_settled"), D("0"))
        upgrade = next(r for r in events if r["event_type"] == "seat_addon.purchased")
        upgrade_credit = q2(q2(D(upgrade["monthly_delta_usd"]) / D(upgrade["cycle_days"])) * D(upgrade["remaining_days"]))
        downgrade = next(r for r in events if r["event_type"] == "plan_downgrade")
        downgrade_credit = q2(q2((D(downgrade["prior_monthly_rate_usd"]) - D(downgrade["new_monthly_rate_usd"])) / D(downgrade["cycle_days"])) * D(downgrade["remaining_days"]))
        recon.append({"event_id": downgrade["event_id"], "category": "RETROACTIVE_PRORATION", "amount_impact_usd": float(q2(-downgrade_credit))})
        # Daily schedule earned by cycle date ranges: $600 for 6d, $900 for 5d, $450 for 9d.
        earned = q2(D("600") / 30 * 6) + q2(D("900") / 30 * 5) + q2(D("450") / 30 * 9)
        net_consideration = q2(D("600") + upgrade_credit - downgrade_credit)
        unearned = q2(net_consideration - earned)
        # Credit note is a wallet credit; cancellation is outside 14 days, so no cash refund.
        b["net_cash_collected"] = float(q2(starting_cash))
        b["customer_wallet_balance"] = float(q2(downgrade_credit + unearned))
        b["recognized_revenue"] = float(earned)
        b["deferred_revenue"] = 0.0
        out["final_subscription_status"] = "CANCELED"

    elif engine == "task_03":
        lines = [D(r["amount_usd"]) for r in events if r["event_type"] == "invoice_line"]
        subtotal = q2(sum(lines, D("0")))
        coupon = next(r for r in events if r["event_type"] == "coupon_applied")
        requested = min(q2(subtotal * D(coupon["percent"]) / D("100")), q2(coupon["max_discount_usd"]))
        floor = D("2600.00")
        actual_discount = min(requested, q2(subtotal - floor))
        prevented = q2(requested - actual_discount)
        if prevented:
            recon.append({"event_id": coupon["event_id"], "category": "COUPON_FLOOR_CAPPED", "amount_impact_usd": float(prevented)})
        net_pretax = q2(subtotal - actual_discount)
        tax_event = next(r for r in events if r["event_type"] == "tax_calculated")
        tax = q2(net_pretax * D(tax_event["rate_percent"]) / D("100"))
        opening_wallet = next(r for r in events if r["event_type"] == "wallet_opening_balance")
        wallet_used = min(q2(opening_wallet["amount_usd"]), q2(net_pretax + tax))
        payment = next(r for r in events if r["event_type"] == "payment_settled")
        b["net_cash_collected"] = float(q2(D(payment["amount_usd"])))
        b["customer_wallet_balance"] = float(q2(D(opening_wallet["amount_usd"]) - wallet_used))
        b["tax_liability"] = float(tax)
        rec, deferred = _recognized(net_pretax, D("15"), D("30"))
        b["recognized_revenue"] = float(rec)
        b["deferred_revenue"] = float(deferred)

    elif engine == "task_04":
        inv = next(r for r in events if r["event_type"] == "invoice_issued")
        invoice_fx = D(inv["invoice_fx"])
        invoice_principal_usd = q2(D(inv["base_eur"]) * invoice_fx)
        invoice_vat_usd = q2(D(inv["vat_eur"]) * invoice_fx)
        payment = next(r for r in events if r["event_type"] == "payment_settled")
        settle_usd = q2(D(payment["amount_eur"]) * D(payment["settlement_fx"]))
        refund = next(r for r in events if r["event_type"] == "partial_refund")
        refund_cash = q2(D(refund["total_eur"]) * D(refund["refund_fx"]))
        refund_base_usd = q2(D(refund["base_eur"]) * invoice_fx)
        refund_vat_usd = q2(D(refund["vat_eur"]) * invoice_fx)
        dispute = next(r for r in events if r["event_type"] == "chargeback_opened")
        reversal = next(r for r in events if r["event_type"] == "chargeback_won")
        disputed_at_rate = q2(D(dispute["principal_eur"]) * D(dispute["dispute_fx"]))
        reversal_cash = q2(D(reversal["principal_eur"]) * D(reversal["reversal_fx"]))
        fee = next(r for r in events if r["event_type"] == "chargeback_fee")
        b["net_cash_collected"] = float(q2(settle_usd - refund_cash - disputed_at_rate + reversal_cash - D(fee["amount_usd"])))
        b["recognized_revenue"] = float(q2(invoice_principal_usd - refund_base_usd))
        b["deferred_revenue"] = 0.0
        b["tax_liability"] = float(q2(invoice_vat_usd - refund_vat_usd))
        settlement_fx_gain = q2(settle_usd - invoice_principal_usd - invoice_vat_usd)
        refund_fx_gain = q2(q2(D(refund["total_eur"]) * invoice_fx) - refund_cash)
        dispute_reversal_fx = q2(disputed_at_rate - reversal_cash)
        b["fx_realized_gain_loss"] = float(q2(settlement_fx_gain + refund_fx_gain - dispute_reversal_fx))
        recon.extend([
            {"event_id": payment["event_id"], "category": "FX_SETTLEMENT_DIFF", "amount_impact_usd": float(settlement_fx_gain)},
            {"event_id": refund["event_id"], "category": "FX_SETTLEMENT_DIFF", "amount_impact_usd": float(refund_fx_gain)},
            {"event_id": reversal["event_id"], "category": "FX_SETTLEMENT_DIFF", "amount_impact_usd": float(q2(-dispute_reversal_fx))},
            {"event_id": fee["event_id"], "category": "CHARGEBACK_FEE_UNRECOVERED", "amount_impact_usd": float(q2(-D(fee["amount_usd"])))},
        ])
        out["final_subscription_status"] = "ACTIVE"

    elif engine == "task_05":
        batches = [r for r in events if r["event_type"] == "usage_batch"]
        units = {period: sum(int(r["units"]) for r in batches if r["period"] == period) for period in ("P1", "P2")}
        def tiered(n: int) -> Decimal:
            tier1 = min(n, 10000)
            tier2 = min(max(n - 10000, 0), 40000)
            tier3 = max(n - 50000, 0)
            return q2(D(tier1) * D("0.05") + D(tier2) * D("0.035") + D(tier3) * D("0.02"))
        p1_gross = tiered(units["P1"])
        p2_gross = tiered(units["P2"])
        sla = next(r for r in events if r["event_type"] == "sla_usage_credit")
        credit_units = int(sla["units"])
        # Unwind P1 highest marginal units first, based on full P1 volume.
        remaining = credit_units
        tier3_eligible = max(units["P1"] - 50000, 0)
        tier3_credit_units = min(remaining, tier3_eligible)
        remaining -= tier3_credit_units
        tier2_eligible = min(max(units["P1"] - 10000, 0), 40000)
        tier2_credit_units = min(remaining, tier2_eligible)
        remaining -= tier2_credit_units
        tier1_credit_units = min(remaining, min(units["P1"], 10000))
        credit = q2(D(tier3_credit_units) * D("0.02") + D(tier2_credit_units) * D("0.035") + D(tier1_credit_units) * D("0.05"))
        p1_net = q2(p1_gross - credit)
        payments = sum((D(r["amount_usd"]) for r in events if r["event_type"] == "payment_settled"), D("0"))
        p1_rec, _ = _recognized(p1_net, D("31"), D("31"))
        p2_rec, p2_deferred = _recognized(p2_gross, D("15"), D("30"))
        b["net_cash_collected"] = float(q2(payments))
        b["customer_wallet_balance"] = float(credit)
        b["recognized_revenue"] = float(q2(p1_rec + p2_rec))
        b["deferred_revenue"] = float(p2_deferred)
        recon.append({"event_id": sla["event_id"], "category": "LATE_USAGE_REBILL", "amount_impact_usd": float(q2(-credit))})

    elif engine == "task_06":
        # Use local calendar boundaries, not a constant UTC offset, for cycle membership.
        from zoneinfo import ZoneInfo
        ny = ZoneInfo("America/New_York")
        audit = _utc(task["audit_period_end"]).astimezone(ny)
        feb_start = datetime(2024, 1, 31, 0, 0, tzinfo=ny)
        feb_end = datetime(2024, 2, 29, 0, 0, tzinfo=ny)
        mar_end = datetime(2024, 3, 31, 0, 0, tzinfo=ny)
        feb_days = D((feb_end.date() - feb_start.date()).days)
        march_days = D((mar_end.date() - feb_end.date()).days)
        feb_units = D("0")
        for row in events:
            if row["event_type"] == "usage_batch" and _utc(row["effective_at"]) <= _utc(task["audit_period_end"]):
                local = _utc(row["effective_at"]).astimezone(ny)
                if feb_start.date() <= local.date() <= feb_end.date():
                    feb_units += D(row["units"])
        feb_usage = q2(feb_units * D("1.00"))
        elapsed_march = D((audit.date() - feb_end.date()).days)
        elapsed_march = max(D("0"), min(elapsed_march, march_days))
        base_rec = q2(D("290") * elapsed_march / march_days)
        feb_rec = q2(D("290") + feb_usage)
        total_cash = sum((D(r["amount_usd"]) for r in events if r["event_type"] == "payment_settled" and _utc(r["effective_at"]) <= _utc(task["audit_period_end"])), D("0"))
        total_consideration = q2(D("290") + feb_usage + D("290"))
        b["net_cash_collected"] = float(q2(total_cash))
        b["recognized_revenue"] = float(q2(feb_rec + base_rec))
        b["deferred_revenue"] = float(q2(total_consideration - (feb_rec + base_rec)))
        out["final_subscription_status"] = "ACTIVE"

    elif engine == "task_07":
        payments = [r for r in events if r["event_type"] == "payment_settled"]
        gross = q2(sum((D(r["amount_usd"]) for r in payments), D("0")))
        coupon = next(r for r in events if r["event_type"] == "coupon_applied")
        consideration = q2(D(coupon["gross_pretax_usd"]) - D(coupon["discount_usd"]))
        cancel = next(r for r in events if r["event_type"] == "subscription_canceled")
        elapsed = D(cancel["exact_elapsed_seconds"])
        cycle = D(cancel["cycle_seconds"])
        earned = q2(consideration * elapsed / cycle)
        wallet = q2(gross - earned)
        b["net_cash_collected"] = float(gross)
        b["customer_wallet_balance"] = float(wallet)
        b["recognized_revenue"] = float(earned)
        b["deferred_revenue"] = 0.0
        out["final_subscription_status"] = "CANCELED"

    elif engine == "task_08":
        migration = next(r for r in events if r["event_type"] == "plan_migration")
        uplift = q2(q2((D(migration["new_monthly_rate_usd"]) - D(migration["old_monthly_rate_usd"])) / D(migration["cycle_days"])) * D(migration["remaining_days"]))
        coupon = next(r for r in events if r["event_type"] == "coupon_applied")
        subtotal = q2(D(coupon["gross_subtotal_usd"]))
        requested = min(q2(subtotal * D(coupon["percent"]) / D("100")), q2(D(coupon["max_discount_usd"])))
        discount = min(requested, q2(subtotal - D(coupon["commitment_floor_usd"])))
        prevented = q2(requested - discount)
        recon.append({"event_id": migration["event_id"], "category": "RETROACTIVE_PRORATION", "amount_impact_usd": float(uplift)})
        recon.append({"event_id": coupon["event_id"], "category": "COUPON_FLOOR_CAPPED", "amount_impact_usd": float(prevented)})
        credit = next(r for r in events if r["event_type"] == "credit_note_writeoff")
        dispute = next(r for r in events if r["event_type"] == "chargeback_opened")
        recon.append({"event_id": dispute["event_id"], "category": "POLICY_VIOLATION_HOLD", "amount_impact_usd": float(q2(D(dispute["amount_usd"])))})
        net_contract = q2(subtotal - discount - D(credit["amount_usd"]))
        ordinary_rec, _ = _recognized(net_contract, D("18"), D("30"))
        frozen_rec = q2(D(dispute["amount_usd"]) * D("18") / D("30"))
        rec = q2(ordinary_rec - frozen_rec)
        deferred = q2(net_contract - rec)
        payment = next(r for r in events if r["event_type"] == "payment_settled")
        b["net_cash_collected"] = float(q2(D(payment["amount_usd"]) - D(dispute["amount_usd"])))
        b["customer_wallet_balance"] = float(q2(D(credit["amount_usd"])))
        b["recognized_revenue"] = float(rec)
        b["deferred_revenue"] = float(deferred)
        out["final_subscription_status"] = "SUSPENDED_DISPUTE"

    else:
        raise ValueError(f"Unknown oracle engine: {engine}")

    # Deterministic ordering of all reported reconciling items.
    out["reconciling_items"] = sorted(recon, key=lambda r: (r["event_id"], r["category"], r["amount_impact_usd"]))
    return out


def _dry_run_mutations(reference: dict[str, Any]) -> dict[str, dict[str, float]]:
    gold = {k: D(v) for k, v in reference["ledger_balances_usd"].items()}
    def changed(**deltas: str) -> dict[str, float]:
        values = dict(gold)
        for key, delta in deltas.items():
            values[key] = q2(values[key] + D(delta))
        return {key: float(q2(values[key])) for key in BALANCE_FIELDS}
    return {
        "SIMULATED_LEDGER_OFFSET_A": changed(net_cash_collected="1.11", recognized_revenue="-1.11", deferred_revenue="1.11"),
        "SIMULATED_LEDGER_OFFSET_B": changed(customer_wallet_balance="25.00", net_cash_collected="-25.00"),
    }


def write_all() -> None:
    (ROOT / "tasks").mkdir(parents=True, exist_ok=True)
    (ROOT / "reference").mkdir(parents=True, exist_ok=True)
    for task in build_tasks():
        reference = solve_task(task)
        task["metadata"]["dry_run_balance_mutations"] = _dry_run_mutations(reference)
        task["prompt"] = make_prompt(task)
        task_file = ROOT / "tasks" / f"{task['task_id']}.json"
        ref_file = ROOT / "reference" / f"{task['task_id']}_reference.json"
        task_file.write_text(json.dumps(task, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        ref_file.write_text(json.dumps(reference, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated 8 task definitions and 8 reference outputs in {ROOT}")


if __name__ == "__main__":
    write_all()
