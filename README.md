# Credit Risk & Collections Analytics

Independent project analyzing a 60,000-loan synthetic portfolio to quantify NPA risk,
credit-score-driven default patterns, and collections efficiency — built to demonstrate
credit risk analytics using SQL, Python, and Power BI. Structurally mirrors real
NBFC/bank risk monitoring (NPA rate, vintage analysis, collections efficiency).

**Live dashboard:** see `dashboard/index.html` or the hosted version on my
[portfolio site](https://devsahni03.github.io/fintech-dashboard.html).

## Key findings

| Metric | Value |
|---|---|
| Total loan accounts | 60,000 |
| Total disbursed | Rs. 3,864.33 Cr |
| Total outstanding | Rs. 2,420.13 Cr |
| NPA rate | 2.29% |
| NPA exposure | Rs. 42.68 Cr |
| Collection efficiency | 92.5% |
| Riskiest loan type | Consumer Durable (3.37% NPA) |
| Credit score risk multiple | Below-600 borrowers default at 8.60% vs 0.37% for 800+ (~23x) |

## Dataset

`data/loan_portfolio.csv` — synthetically generated (see `python/generate_data.py`) to
mirror realistic lending risk patterns: default probability driven primarily by credit
score, with loan-type and regional modifiers layered on top. Not real borrower data —
built for portfolio/learning purposes.

Columns: `loan_id`, `borrower_id`, `loan_type`, `region`, `disbursal_date`, `loan_amount`,
`tenure_months`, `credit_score`, `outstanding_principal`, `collections_amount`,
`dpd_bucket`, `written_off`.

## Repo structure

```
├── data/
│   └── loan_portfolio.csv          # 60,000-row synthetic dataset
├── sql/
│   └── credit_risk_analysis.sql    # 6 analysis queries: portfolio summary, NPA by
│                                     type, risk by score band, regional collections,
│                                     vintage trend, recovery opportunity
├── python/
│   ├── generate_data.py            # Synthetic data generator
│   └── analysis.py                 # pandas reproduction + matplotlib charts
├── dashboard/
│   └── assets/                     # Static chart PNGs + KPI JSON
├── POWER_BI_GUIDE.md               # DAX measures + report build guide
└── README.md
```

## Methods

- **SQL** (SQLite): multi-table joins, subqueries, a CASE-based risk segmentation, and
  a benchmark-based recovery opportunity estimate.
- **Python**: pandas for analysis validation, matplotlib for static charts.
- **Power BI**: DAX measures for the same metrics — see `POWER_BI_GUIDE.md`.

## Reproduce it yourself

```bash
pip install pandas numpy matplotlib
python python/generate_data.py     # regenerates data/loan_portfolio.csv
python python/analysis.py          # regenerates charts + dashboard/assets/kpi_data.json
```

## Author

Dev Sahni — [LinkedIn](https://www.linkedin.com/in/dev-sahni-39595131a) ·
[Portfolio](https://devsahni03.github.io) · devsahni03@gmail.com
