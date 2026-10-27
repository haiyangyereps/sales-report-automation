# Local verification

Fictional sample data; commands executed successfully. Temporary database paths shown below are ephemeral.

```text
python3 report.py examples/sales.csv --output /var/folders/zg/sd0lgkgn0q71mm5sgl66mkkc0000gn/T/tmpy88ixv7h/report.html
{
  "status": "ok",
  "currency": "USD",
  "transactions": 4,
  "sales_transactions": 3,
  "refund_transactions": 1,
  "gross": "500.00",
  "refunds": "20.00",
  "net": "480.00",
  "average_positive_sale": "166.67",
  "refund_value_rate": "4.00",
  "daily": {
    "2026-10-01": "200.00",
    "2026-10-02": "0",
    "2026-10-03": "280.00"
  }
}
```
