# Household Liquidity Recycling Experiment

## Purpose

The general input-output prototype conserves aggregate cash, but its baseline
can concentrate cash in firms while household cash and household expenditure
fall. This experiment tests one explicit income-recycling rule without changing
the canonical baseline model.

The baseline 12-period reference previously inspected had opening household
cash of 10,900 and ending household cash of 985.86, while firm cash rose to
61,614.14. Aggregate cash remained 62,600. This is a distribution/liquidity
problem in that prototype, not money destruction.

## Policy rule

For each firm and period:

`netCashFlow_i = closingCash_i - openingCash_i`

Only positive net period cash flow is eligible. The transfer is:

`transfer_i = floor_to_cent(max(0, netCashFlow_i) * recyclingRate)`

The transfer rate must be in [0, 1]. A firm with non-positive net cash flow pays
nothing. The transfer cannot exceed the positive cash flow and cannot make
firm cash negative. The amount is divided equally across the model's synthetic
households, with cent-rounding residual assigned deterministically to the last
household.

Transfers are posted as separate between-period events after market/production
period close and before the next period begins. Thus the next period's household
budget can use the transferred cash. The transfer is funded by existing money;
it creates no money and does not alter physical stocks.

## Experiment design

The CI runner executes 24 periods with identical opening conditions at rates
0%, 10%, 25% and 50%. The zero-rate case is the control and must reproduce the
existing IO prototype's balances, expenditure, output, event count and event
digest exactly.

Reported measures include:
- cumulative household recycling;
- final household, firm and external-supplier cash shares;
- final household cash Gini;
- household expenditure, wages, production, imports and shortages;
- aggregate cash conservation and physical stock reconciliation.

## Acceptance tests

- Zero recycling rate is exactly equivalent to the unmodified IO baseline.
- Every period preserves aggregate cash exactly.
- No household or firm cash balance becomes negative.
- Each household distribution equals the sum paid by firms.
- Each firm payout is no greater than its positive net cash flow multiplied by
  the configured rate, rounded down to cents.
- Physical stock balances remain unchanged by the monetary overlay.
- Invalid rates, duplicate sensitivity rates and invalid period counts fail
  closed.

## Interpretation limits

This is a policy sensitivity, not a calibrated dividend, profit-sharing
contract, tax rule, or normative recommendation. The firm funding measure is
net period cash flow, not accounting profit: the IO prototype does not yet
provide full accrual accounting, cost-of-goods-sold inventory valuation,
investment, taxes, or ownership entitlements.

The underlying IO prototype also splits wages evenly across three synthetic
households rather than linking workers to employers. This overlay equally
distributes transfers to those households. Neither allocation rule should be
mistaken for a real labour-market or ownership model.

The experiment does not integrate the six-register coordinator, GOLD SFC
financial journal, legal-rights register, or physical SCCE household needs
engine. It tests whether a simple cash-recycling mechanism reduces household
liquidity concentration while preserving the existing IO model's invariants.
A positive result would justify a more complete cross-register design; it
would not prove that the policy is optimal or that the full SYNERGY economy is
monetarily closed.
