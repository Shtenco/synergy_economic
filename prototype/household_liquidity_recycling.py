"""Household liquidity-recycling policy experiment for the IO prototype.

This is an additive research overlay. It leaves the canonical IO baseline and
its assumptions untouched. At each period boundary it transfers a configured
share of each firm's *positive net cash flow during that period* to households.
It is a policy sensitivity, not accounting profit, dividends under law, or a
claim that this transfer rule is optimal.

The transfer is recorded as a separate between-period event so that the next
period's household budget can use the additional cash. No money is created.
"""
from __future__ import annotations

import json
from decimal import Decimal as D
from hashlib import sha256
from typing import Iterable

from io_economy import EconomyError, InputOutputEconomy, ZERO, cash, dec


class HouseholdLiquidityRecyclingEconomy(InputOutputEconomy):
    """IO economy with a bounded, cash-funded household recycling overlay."""

    def __init__(self, *args, household_recycling_rate=D("0"), **kwargs):
        rate = dec(household_recycling_rate)
        if not rate.is_finite() or not ZERO <= rate <= D("1"):
            raise EconomyError("household_recycling_rate must be finite and in [0, 1]")
        super().__init__(*args, **kwargs)
        self.household_recycling_rate = rate
        self.recycling_history = []

    def step(self, period):
        opening_firm_cash = {firm_id: state.cash
                             for firm_id, state in self.firms.items()}
        result = super().step(period)

        firm_transfers = {}
        household_transfers = {household_id: ZERO
                               for household_id in self.households}
        households = [self.households[key] for key in sorted(self.households)]
        total_transferred = ZERO

        if self.household_recycling_rate > 0 and households:
            for firm_id, state in sorted(self.firms.items()):
                net_cash_flow = state.cash - opening_firm_cash[firm_id]
                if net_cash_flow <= 0:
                    continue
                proposed = cash(net_cash_flow * self.household_recycling_rate)
                transfer = min(proposed, state.cash)
                if transfer <= 0:
                    continue
                state.cash -= transfer
                shares = [cash(transfer / D(len(households)))
                          for _ in households]
                shares[-1] += transfer - sum(shares, ZERO)
                if any(share < 0 for share in shares):
                    raise EconomyError("household recycling rounding produced a negative share")
                for household, share in zip(households, shares):
                    household.cash += share
                    household_transfers[household.config.household_id] += share
                firm_transfers[firm_id] = transfer
                total_transferred += transfer

        if total_transferred > 0:
            self._event(f"p{period}:between-period-household-recycling",
                        "between_period_household_recycling", {
                "rate": str(self.household_recycling_rate),
                "firm_transfers": {key: str(value)
                                   for key, value in sorted(firm_transfers.items())},
                "household_transfers": {key: str(value)
                                        for key, value in sorted(household_transfers.items())},
                "total_transferred": str(total_transferred),
                "funding_rule": "configured_share_of_positive_firm_net_period_cash_flow",
            })

        if self._system_cash() != self.initial_cash:
            raise EconomyError("household recycling violated system cash conservation")
        if any(state.cash < 0 for state in self.firms.values()):
            raise EconomyError("household recycling caused negative firm cash")
        if any(state.cash < 0 for state in self.households.values()):
            raise EconomyError("household recycling caused negative household cash")

        self.recycling_history.append({
            "period": period,
            "rate": str(self.household_recycling_rate),
            "firm_transfers": {key: str(value)
                               for key, value in sorted(firm_transfers.items())},
            "household_transfers": {key: str(value)
                                    for key, value in sorted(household_transfers.items())},
            "total_transferred": str(total_transferred),
        })
        if total_transferred > 0:
            payload = json.dumps(self.events, sort_keys=True, separators=(",", ":"))
            result.event_digest = sha256(payload.encode("utf-8")).hexdigest()
        return result

    def summary(self):
        result = super().summary()
        total_transferred = sum(
            (dec(row["total_transferred"]) for row in self.recycling_history), ZERO)
        household_cash = sum((h.cash for h in self.households.values()), ZERO)
        result.update({
            "household_recycling_rate": str(self.household_recycling_rate),
            "cumulative_household_recycling": str(total_transferred),
            "final_household_cash_share": (
                str(household_cash / self.initial_cash)
                if self.initial_cash > 0 else "0"
            ),
            "final_household_cash_by_id": {
                key: str(state.cash) for key, state in sorted(self.households.items())
            },
            "final_firm_cash_by_id": {
                key: str(state.cash) for key, state in sorted(self.firms.items())
            },
            "recycling_history": list(self.recycling_history),
        })
        return result


def run_recycling_sensitivity(periods: int = 12,
                              rates: Iterable[D] = (D("0"), D("0.10"), D("0.25"), D("0.50"))):
    """Run identical opening economies under alternative recycling rates."""
    if not isinstance(periods, int) or isinstance(periods, bool) or periods < 1:
        raise EconomyError("periods must be a positive integer")
    rows = []
    seen = set()
    for raw_rate in rates:
        rate = dec(raw_rate)
        if rate in seen:
            raise EconomyError("recycling sensitivity rates must be unique")
        seen.add(rate)
        model = HouseholdLiquidityRecyclingEconomy(
            household_recycling_rate=rate)
        summary = model.run(periods)
        rows.append({
            "rate": str(rate),
            "summary": summary,
            "periods": [row.__dict__ for row in model.period_results],
        })
    if not rows:
        raise EconomyError("at least one recycling rate is required")
    return {
        "experiment": "household_liquidity_recycling_sensitivity",
        "periods": periods,
        "opening_conditions": "identical default IO prototype configuration",
        "interpretation": (
            "Cash transfers are funded only from positive firm net period cash flow; "
            "they are not calibrated dividends or a welfare optimum."
        ),
        "scenarios": rows,
    }
