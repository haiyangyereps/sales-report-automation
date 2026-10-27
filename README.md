# Sales Report Automation

**Turn a transaction export into an inspectable business summary and standalone HTML chart.**

Python portfolio prototype that validates the entire dataset before publishing a report. Includes exact decimal totals, refunds, average positive sale, refund value rate, and daily net sales with zero-activity dates filled in.

## Quick start

Python 3.10+, no third-party dependencies. From the repository root:

```sh
python3 report.py examples/sales.csv --output output/report.html
python3 -m unittest discover -s tests -v
```

Open `output/report.html` in a browser. It works offline, contains no external scripts, and adapts to the viewport. Command output is a machine-readable JSON summary. The report path is written atomically only after validation succeeds; invalid data returns exit code 2 and leaves any existing report untouched.

## Input contract

CSV columns: `transaction_id,date,amount,currency`. IDs must be unique and non-empty. Dates must be ISO calendar dates. Amounts must be finite and exactly representable in cents. One three-letter currency code per file; no currency conversion. Date spans are limited to 3660 days. Currency codes are syntactically checked, not validated against an ISO registry.

## Sample results

| Metric | Fictional sample result |
|---|---:|
| Transactions | 4 |
| Gross sales | USD 500.00 |
| Refund value | USD 20.00 |
| Net sales | USD 480.00 |
| Average positive sale | USD 166.67 |
| Refund value / gross sales | 4.00% |

October 2 has no transactions and appears as zero on the chart. Red bars represent negative daily totals; bar width represents absolute magnitude. A positive transaction is treated as one sale; this is not order-level AOV when orders span multiple transactions. Refund value rate is not a customer/cohort return rate. All-negative inputs have no defined refund value rate.

## Evidence and production limits

[Tests](tests/test_report.py) cover duplicate IDs, invalid dates, mixed currencies, non-finite amounts, fractions of cents, refund-only data, zero-activity dates, and preservation of prior reports on failure.

No real client data is included. Timezones, scheduling, email delivery, accounting reconciliation, taxes, and FX conversion are outside scope. CSV input dates are assumed already normalized to the business reporting timezone. Large datasets and production access controls need separate evaluation.
