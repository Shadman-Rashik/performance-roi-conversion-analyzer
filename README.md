# Performance ROI & Conversion Drop-off Analyzer

An interactive analytics dashboard that compares marketing spend with attributed revenue, shows where potential customers drop off in the conversion funnel, and compares checkout completion and payment failures across markets and payment methods.

> **Synthetic data notice:** every number in this project is randomly generated for portfolio purposes (fixed random seed, so it is reproducible). It is *inspired by* Bangladesh and international e-commerce markets but is **not** real company, campaign or market data. Findings describe the synthetic dataset only.

## What it answers

1. How does marketing spend compare with attributed revenue?
2. Which channels and campaigns perform better on selected metrics (ROI, CPA, conversion rate)?
3. At which funnel step do the most people drop off?
4. How do checkout completion and payment failure rates differ by market and payment method?
5. What data-supported patterns might a business investigate next?

## Tech stack

| Tool | Used for |
|---|---|
| SQLite + SQL | Storing the data and answering business questions (`sql/`) |
| Python + Pandas | Generating, validating and analysing data |
| Streamlit | The interactive dashboard (runs locally, opens in your browser) |
| Plotly | Interactive charts |
| Git / GitHub | Version control and portfolio hosting |

## Dashboard features

- **Executive Overview:** Marketing Spend, Attributed Revenue, Revenue-Based ROI, Purchases, CPA, Purchase Conversion Rate.
- **Marketing Performance:** ROI and CPA by channel, spend vs revenue, campaign scatter with break-even line, sortable campaign ranking.
- **Conversion Funnel:** Landing Page Visitors -> Product Interactions -> Add to Cart -> Checkout Started -> Purchases, with step drop-off rates, the largest drop-off highlighted, and a drop-off heatmap by market or channel.
- **Checkout & Payments:** completion rate, failure rate, comparison by market and payment method, market x method heatmap.
- **Filters:** Market, Marketing channel, Campaign (cascading). Campaign and channel filters are *not* applied to payment data because the payment table has no campaign-level link.
- **Recommendations:** rule-based observations recalculated from the current filters. Nothing is hardcoded to a particular campaign or channel.

## Project structure

```
performance-roi-conversion-analyzer/
|-- app.py                 Streamlit dashboard
|-- generate_data.py       Creates the synthetic CSV files
|-- build_database.py      Loads the CSVs into SQLite
|-- validate_data.py       Data-quality checks
|-- run_queries.py         Runs all SQL queries and prints results
|-- metrics.py             Metric calculations (safe division)
|-- recommendations.py     Rule-based recommendations
|-- test_project.py        Automated checks
|-- requirements.txt
|-- sql/
|   |-- schema.sql         Tables and CHECK rules
|   `-- queries.sql        7 business questions in SQL, each explained
|-- data/
|   |-- campaigns.csv
|   |-- payments.csv
|   `-- analytics.db       SQLite database (generated)
`-- docs/
    |-- START_HERE_WINDOWS.md    Step-by-step beginner guide
    |-- GITHUB_UPLOAD.md         How to publish the project
    |-- CV_and_LinkedIn.md       Honest CV and LinkedIn text
    `-- screenshots/             Put dashboard screenshots here
```

## Setup and run (Windows)

1. Install **Python 3.11 or newer** from python.org. Tick **"Add python.exe to PATH"** in the installer.
2. Open **PowerShell** in the project folder (in File Explorer, click the address bar, type `powershell`, press Enter).
3. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once and try again.
4. Install the libraries:
   ```
   python -m pip install -r requirements.txt
   ```
5. Build the data and database, then check them:
   ```
   python generate_data.py
   python build_database.py
   python validate_data.py
   python test_project.py
   ```
6. (Optional) See the SQL answers in the terminal:
   ```
   python run_queries.py
   ```
7. Start the dashboard:
   ```
   python -m streamlit run app.py
   ```
   Your browser opens at `http://localhost:8501`. Press `Ctrl + C` in PowerShell to stop it.

If `python` is not recognised, try `py` instead (for example `py -m streamlit run app.py`).

## How the pieces fit together

- **SQLite database** (`data/analytics.db`): a single file that stores the tables. No server is needed.
- **Python app** (`app.py`): runs on your computer, reads the database, calculates metrics, builds charts.
- **Browser**: just the window that displays the page Streamlit serves from your own computer.

An online SQL editor cannot reach files on your computer, so this project runs locally. The same queries in `sql/queries.sql` can be pasted into any SQLite tool, such as DB Browser for SQLite.

## Metric definitions

| Metric | Formula |
|---|---|
| Revenue-Based ROI (%) | (Attributed Revenue - Marketing Spend) / Marketing Spend x 100 |
| CPA | Marketing Spend / Purchases |
| CTR (%) | Clicks / Impressions x 100 |
| Purchase Conversion Rate (%) | Purchases / Landing Page Visitors x 100 |
| Funnel step drop-off (%) | 100 - (people at a stage / people at the previous stage x 100) |
| Checkout Completion Rate (%) | Successful Payments / Checkout Attempts x 100 |
| Payment Failure Rate (%) | Failed Payments / Checkout Attempts x 100 |

Totals are computed by summing raw counts first and dividing afterwards. A zero or missing denominator returns "N/A" rather than an error or infinity.

**Revenue-based ROI is not net-profit ROI.** Product costs, operating costs, fees and other expenses are not included, so a positive ROI here does not mean a campaign was profitable.

## Data dictionary

**campaigns** (48 rows, one per campaign): `campaign_id`, `campaign_name`, `market`, `marketing_channel`, `campaign_objective`, `reporting_currency` (USD), `marketing_spend`, `impressions`, `clicks`, `landing_page_visitors`, `product_interactions`, `add_to_cart`, `checkout_started`, `purchases`, `attributed_revenue`.
Funnel counts never increase from one stage to the next (enforced by `CHECK` rules and by `validate_data.py`). One campaign intentionally has spend but zero purchases, to demonstrate safe handling of zero denominators.

**payments** (15 rows, one per market and payment method): `market`, `payment_method`, `checkout_attempts`, `successful_payments`, `failed_payments`, `completed_orders`.
`successful_payments + failed_payments = checkout_attempts`, and `completed_orders <= successful_payments`. For *Cash on Delivery*, "failed" means the order was not confirmed (a synthetic definition).

**Currency:** all money values use one reporting currency, USD. No exchange-rate conversion is applied, and the amounts are synthetic.

**No campaign-payment link:** the payment table is aggregated by market and payment method. It cannot be joined to campaigns, so campaign and channel filters do not affect payment charts.

## SQL queries (`sql/queries.sql`)

| # | Business question |
|---|---|
| Q1 | Which campaigns generate the highest attributed revenue? |
| Q2 | Which channels have the lowest CPA? |
| Q3 | Which campaigns have high spend but comparatively low attributed revenue? |
| Q4 | Which markets show the largest conversion drop-off? |
| Q5 | Which payment methods have the highest observed failure rates? |
| Q6 | Which market + payment method combinations fail most often? |
| Q7 | What is the best campaign in each market by ROI? (window function) |

Each query has a plain-language comment explaining what it does and why a business would care.

## Methodology

1. `generate_data.py` simulates campaigns with channel- and market-specific assumptions and builds each funnel stage as a random subset of the previous stage, so counts can only shrink.
2. `build_database.py` creates SQLite tables from `sql/schema.sql` (with integrity `CHECK` rules) and loads the CSVs.
3. `validate_data.py` checks missing values, duplicates, negative values, funnel order, currency consistency and payment reconciliation.
4. `metrics.py` calculates every metric; `test_project.py` checks the formulas and compares Pandas results with SQL results.
5. `app.py` presents the results; `recommendations.py` turns the filtered numbers into rule-based observations.

## Limitations

- Synthetic data: no real customers, campaigns or markets.
- Revenue-based ROI ignores costs other than marketing spend.
- Simplified attribution (each purchase credited to one campaign) and no time dimension.
- Payment data is not linked to campaigns.
- Observed patterns indicate areas to investigate and do not establish causes.
- Small groups can give unstable percentages.

## Business value (what a real analyst could do with this approach)

The same structure could be applied to real campaign and checkout exports to spot underperforming spend, find the funnel step with the largest loss, and compare payment reliability across markets. This project demonstrates the method, not real results.

## Suggested screenshots (save in `docs/screenshots/`)

1. `01-executive-overview.png` - KPI cards with the "Synthetic data" banner visible
2. `02-marketing-performance.png` - ROI by channel and the campaign scatter
3. `03-conversion-funnel.png` - funnel chart with the largest drop-off highlighted
4. `04-checkout-payments.png` - failure-rate chart and market x method heatmap
5. `05-recommendations.png` - the recommendations tab
6. `06-filters-applied.png` - a single market selected, showing KPIs changing

## Possible future improvements

Add a date dimension for trends, a net-profit view with cost inputs, CSV upload for your own data, and deployment to Streamlit Community Cloud.
