import unittest
from decimal import Decimal as D

from io_economy import EconomyError, InputOutputEconomy
from household_liquidity_recycling import (
    HouseholdLiquidityRecyclingEconomy,
    run_recycling_sensitivity,
)


class HouseholdLiquidityRecyclingTests(unittest.TestCase):
    def test_zero_rate_is_exact_baseline_control(self):
        baseline = InputOutputEconomy()
        baseline_summary = baseline.run(12)

        control = HouseholdLiquidityRecyclingEconomy(
            household_recycling_rate=D("0"))
        control_summary = control.run(12)

        for key in (
            "final_household_cash", "final_firm_cash", "external_supplier_cash",
            "system_cash", "cash_conservation_error",
            "max_abs_physical_balance_error", "cumulative_wages",
            "cumulative_household_expenditure", "cumulative_import_expenditure",
            "cumulative_gross_value_added_proxy", "event_count", "event_log_digest",
        ):
            self.assertEqual(control_summary[key], baseline_summary[key], key)
        self.assertEqual(control_summary["cumulative_household_recycling"], "0")

    def test_recycling_is_cash_funded_and_conserves_money_each_period(self):
        model = HouseholdLiquidityRecyclingEconomy(
            household_recycling_rate=D("0.25"))
        initial = model.initial_cash
        model.run(24)

        total = D(model.summary()["cumulative_household_recycling"])
        self.assertGreater(total, 0)
        self.assertEqual(model._system_cash(), initial)
        self.assertEqual(D(model.summary()["cash_conservation_error"]), 0)
        self.assertEqual(D(model.summary()["max_abs_physical_balance_error"]), 0)
        self.assertTrue(all(state.cash >= 0 for state in model.firms.values()))
        self.assertTrue(all(state.cash >= 0 for state in model.households.values()))

        for row in model.recycling_history:
            paid = sum((D(value) for value in row["firm_transfers"].values()), D("0"))
            received = sum((D(value) for value in row["household_transfers"].values()), D("0"))
            self.assertEqual(paid, received)
            self.assertEqual(paid, D(row["total_transferred"]))
            self.assertGreaterEqual(paid, 0)

    def test_distribution_is_not_paid_from_negative_firm_net_cash_flow(self):
        model = HouseholdLiquidityRecyclingEconomy(
            household_recycling_rate=D("1"))
        model.run(3)
        for row in model.recycling_history:
            self.assertTrue(all(D(value) >= 0 for value in row["firm_transfers"].values()))
            self.assertTrue(all(D(value) >= 0 for value in row["household_transfers"].values()))

    def test_invalid_recycling_rates_are_rejected(self):
        for rate in ("-0.01", "1.01", "NaN", "Infinity"):
            with self.subTest(rate=rate):
                with self.assertRaises(EconomyError):
                    HouseholdLiquidityRecyclingEconomy(
                        household_recycling_rate=D(rate))

    def test_sensitivity_requires_unique_rates_and_positive_periods(self):
        with self.assertRaises(EconomyError):
            run_recycling_sensitivity(periods=0)
        with self.assertRaises(EconomyError):
            run_recycling_sensitivity(rates=(D("0.1"), D("0.1")))
        result = run_recycling_sensitivity(
            periods=3, rates=(D("0"), D("0.2")))
        self.assertEqual(len(result["scenarios"]), 2)
        self.assertEqual(result["periods"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
