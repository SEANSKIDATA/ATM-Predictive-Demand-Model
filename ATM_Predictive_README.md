# ATM Predictive Demand Model
### SEANSKIDATA Analytics Portfolio — Project 3

> **The shift from reactive to predictive:** Projects 1 and 2 identified what the network's risk state *was*. This project answers what it will be — 72 hours from now.

🔗 [View Interactive Dashboard on Tableau Public](https://public.tableau.com/app/profile/sean.codner/viz/ATMPredictiveDemandModel/Dashboard1)

---

## How to Run This Project

### Prerequisites
```bash
pip install -r requirements.txt
```

### Option 1 — Run the Python Model (Google Colab recommended)
1. Open [Google Colab](https://colab.research.google.com)
2. Upload `atm_predictive_demand_model.py` or paste the code into a new notebook
3. Run all cells — the model will generate the dataset, run the forecast, and produce the dashboard PNG

### Option 2 — Run the SQL Queries (MySQL Workbench)
1. Import the three CSV files into MySQL as tables:
   - `atm_master.csv` → table: `atm_master`
   - `atm_transactions.csv` → table: `atm_transactions`
   - `atm_forecast.csv` → table: `atm_forecast`
2. Run queries in order from the `/sql` folder
3. Note: Add `SET SESSION sql_mode = '';` before Query 4 if using MySQL strict mode

### Files in This Repo

| File/Folder | Purpose |
|---|---|
| `atm_predictive_demand_model.py` | Main Python model — dataset generation, forecasting, visualization |
| `atm_model_validation.py` | Model validation — MAE, RMSE, MAPE, feature engineering docs |
| `atm_master.csv` | 50-ATM master reference table |
| `atm_transactions.csv` | 18,300-row full-year transaction time series |
| `atm_forecast.csv` | 72-hour forward projection with risk scores |
| `requirements.txt` | Python dependencies |
| `/sql` | 5 production SQL queries with window functions and CTEs |
| `/screenshots` | MySQL Workbench live execution results for all 5 queries |

---

## Business Question

Based on historical transaction patterns, day-of-week behavior, tax season demand spikes, and terminal type — **which ATMs will hit a critical cash threshold in the next 72 hours?**

Standard ATM reporting flags machines that are already low. By then, the options are limited and expensive. This model forecasts forward — giving operations teams time to dispatch on schedule rather than emergency.

---

## The Core Insight

Not all cash depletion is equal — and not all seasons are equal.

**Tax season (February–April)** is the single largest demand event in the ATM calendar. When IRS refunds hit direct deposit accounts in mid-February, cash withdrawal volume at Retail and Urban ATMs spikes 40–60% above baseline. This isn't a minor seasonal adjustment — it's an operational planning event that standard dashboards are blind to.

This model makes it visible.

| Season | Retail/Urban Lift | Casino Lift | Mall Lift |
|---|---|---|---|
| Tax Season Peak (Feb 15 – Mar 15) | **+51–54%** | +37% | +42% |
| Tax Season Ramp (Jan, Apr) | +15–25% | +10% | +15% |
| Holiday (Nov–Dec) | +18% | +18% | +18% |
| Baseline (May–Oct) | — | — | — |

*Multipliers sourced from real ATM network operations experience.*

---

## The Penn Station Effect

During the transition period when tax preparation services shifted from issuing refund checks to loading refunds onto debit cards, operations teams observed an anomaly: machines classified as **High tolerance / low priority** all year were suddenly transacting like high-volume urban terminals.

Customers were walking directly from tax offices to the nearest ATM and withdrawing at the machine's maximum limit — $500 per transaction — compared to the normal $85–$165 baseline. With refunds averaging $3,000+, many customers returned multiple times within the same day.

**The result:** 5 machines in this model that register as routine all year become the network's most cash-hungry terminals for 28 days. Standard reporting never flags them. This model does.

| Machine Type | Baseline Daily Cash | Tax Peak Daily Cash | Lift |
|---|---|---|---|
| Retail (standard) | $8,275 | $26,918 | +225% |
| Urban | $15,060 | $23,197 | +54% |
| Casino | $40,367 | $54,182 | +34% |
| **Tax Service Proximity** | **$8,235** | **$70,440** | **+755%** |

---

## Project Architecture

This project extends the synthetic dataset from **ATM-Network-Risk-Intelligence** with:

- **Full calendar year (365 days)** of time-series transaction data
- **Tax season demand modeling** — peak refund window, ramp periods, location-type weighting
- **Tax service proximity flagging** — 5 machines reclassified to Zero tolerance during peak window
- **Day-of-week demand patterns** — Friday/Saturday peaks built into every machine
- **Forward-looking 72-hour cash burn forecast** — per machine, per terminal tier
- **Composite risk scoring** — cash level + terminal type + cash tolerance + revenue impact
- **Interactive Tableau dashboard** — 6-panel operational view of network health

### Dataset Structure

| Table | Records | Description |
|---|---|---|
| `atm_master.csv` | 50 ATMs | Master reference — location, terminal type, capacity, tolerance, tax service proximity |
| `atm_transactions.csv` | 18,300 rows | 365-day daily transaction time series |
| `atm_forecast.csv` | 50 rows | 72-hour forward projection with risk scoring |

### Terminal Classification

| Type | Distance | Emergency Multiplier |
|---|---|---|
| Local | < 25 miles | 2.5x scheduled cost |
| Remote | 25–99 miles | 3.0x scheduled cost |
| Over The Road | 100+ miles | 4.0x scheduled cost |

### Tax Season Demand Weights by Location Type

| Location Type | Tax Season Sensitivity | Rationale |
|---|---|---|
| Retail | Full (1.0x) | Highest concentration of cash-preferred customers |
| Urban | Full (1.0x) | Dense population receiving refunds |
| Mall | Moderate (0.85x) | Refund spending, but card usage higher |
| Casino | Moderate (0.70x) | Refund-flush customers, card-heavy environment |
| Airport / Hospital / Office | Low (0.50x) | Transaction-driven, not refund-driven |
| **Tax Service Proximity** | **2.0x during peak** | **Direct adjacency to tax preparation office** |

---

## Operational Intelligence Summary

> This model doesn't just show what is happening — it tells operations teams what to do next.

### Headline KPIs (72-Hour Window)

| | Metric | Value |
|---|---|---|
| 💰 | **Revenue at Risk** | $830,880 |
| 🚨 | **Critical ATMs Requiring Action** | 5 locations |
| ⚡ | **Immediate Dispatch Required** | 5 machines |
| ⏱ | **Avg Days to Failure (At-Risk Units)** | 0.6 days |

---

### Recommended Action Framework

| Risk Tier | Score Threshold | Action Required |
|---|---|---|
| **CRITICAL** | 140+ | **Immediate dispatch** — do not wait for scheduled route |
| **HIGH** | 100–139 | **Schedule next route** — prioritize within 24 hours |
| **MEDIUM** | 60–99 | **Monitor closely** — flag for next scheduled run |
| **LOW** | <60 | Standard schedule — no intervention needed |

---

### Top 10 ATMs — Operational Action Register

| Rank | ATM | Location | Terminal Type | Days Until Empty | Revenue at Risk | Tier | Action |
|---|---|---|---|---|---|---|---|
| #1 | ATM007 | Tunica Casino MS | Over The Road | <1 day | $61,200 | CRITICAL | **IMMEDIATE DISPATCH** |
| #2 | ATM038 | Lake Charles Casino LA | Over The Road | <1 day | $61,200 | CRITICAL | **IMMEDIATE DISPATCH** |
| #3 | ATM009 | Biloxi Casino MS | Remote | <1 day | $61,200 | CRITICAL | **IMMEDIATE DISPATCH** |
| #4 | ATM010 | Shreveport Casino LA | Over The Road | 0.8 days | $61,200 | CRITICAL | **IMMEDIATE DISPATCH** |
| #5 | ATM008 | Laughlin Casino NV | Over The Road | 0.8 days | $61,200 | CRITICAL | **IMMEDIATE DISPATCH** |
| #6 | ATM006 | NRG Stadium | Local | 0.5 days | $27,360 | HIGH | Schedule Next Route |
| #7 | ATM047 | Victoria Mall | Over The Road | <1 day | $17,280 | HIGH | Schedule Next Route |
| #8 | ATM049 | Palacios Waterfront | Over The Road | <1 day | $13,680 | HIGH | Schedule Next Route |
| #9 | ATM004 | IAH Airport Terminal B | Local | <1 day | $30,240 | HIGH | Schedule Next Route |
| #10 | ATM003 | IAH Airport Terminal A | Local | <1 day | $30,240 | HIGH | Schedule Next Route |

---

## Network Summary (72-Hour Forecast Window)
- **50 ATMs** monitored across the network
- **39 flagged critical** within 72 hours
- **8 Over The Road terminals** in critical status
- **5 tax service proximity machines** reclassified to Zero tolerance during peak
- **$830,880** revenue at risk in a full 72-hour outage scenario

---

## Interactive Dashboard

🔗 [View Live on Tableau Public](https://public.tableau.com/app/profile/sean.codner/viz/ATMPredictiveDemandModel/Dashboard1)

![ATM Predictive Demand Dashboard](https://raw.githubusercontent.com/SEANSKIDATA/ATM-Predictive-Demand-Model/main/atm_predictive_dashboard.png)

---

## Composite Risk Score Formula

```
Risk Score =
  Cash Depletion Weight   (max 60 pts — how far below threshold)
+ Terminal Type Weight    (OTR=40, Remote=20, Local=5)
+ Cash Tolerance Weight   (Zero=35, Low=20, Medium=10, High=0)
+ Revenue Impact Weight   (hourly revenue impact / 20)
+ Tax Proximity Premium   (+25 pts during Feb 15 – Mar 15 peak)
```

---

## Model Validation

Validated against a 31-day holdout period (December 2024) using 1,550 daily predictions.

| Metric | Result |
|---|---|
| Mean Absolute Error (MAE) | $783/day |
| Root Mean Square Error (RMSE) | $1,120/day |
| Mean Absolute Pct Error (MAPE) | 5.7% |
| Predictions within 10% of actual | 84.4% |
| Predictions within 20% of actual | 99.9% |
| Critical flag recall | 97.3% |
| Critical flag precision | 97.3% |
| F1 Score | 0.973 |

**Recall of 97.3%** means the model correctly identifies 97.3% of machines that will go critical in the 72-hour window. In ATM operations, false negatives are far more costly than false positives — the model is tuned to maximize recall.

---

## Feature Engineering

| Feature | Source | Rationale |
|---|---|---|
| `terminal_type` | `distance_from_branch_miles` | Distance drives emergency cost (2.5x–4.0x). OTR machines are categorically more urgent — standard reporting treats all distances equally. |
| `cash_tolerance` | `location_type` | Business context defines acceptable minimum. A casino cannot tolerate outage. A rural retail ATM can. Volume alone misses this. |
| `days_until_empty` | `cash_balance_eod` + burn rate | Forward-looking trajectory vs backward-looking balance snapshot. |
| `dow_avg_burn` | `daily_cash_dispensed` + day of week | Friday/Saturday demand is 42–73% above Monday baseline. Forecasting without this systematically underestimates weekend burn. |
| `seasonal_multiplier` | `transaction_date` + `location_type` | Tax peak drives 40–60% lift at Retail/Urban. Domain-calibrated from live network operations — not assumed. |
| `tax_service_proximity` | Operational flag + date | Reclassifies machines near tax offices to Zero tolerance Feb 15–Mar 15. Corrects a blindspot standard reporting cannot see. |
| `composite_risk_score` | All features combined | Single sortable number replacing volume-based ranking with multi-factor operational prioritization. |

---

## SQL Foundation Layer

The Python model replicates analytical logic that would run as SQL against a production database. The five queries below demonstrate the full pipeline — from raw transaction data to risk scoring — using joins, CTEs, and window functions.

---

### Query 1 — Daily Cash Burn Rate (Rolling 30-Day Average)
Window functions: `AVG() OVER`, `RANK() OVER`, `PARTITION BY`

```sql
SELECT
    t.atm_id,
    l.location_name,
    l.location_type,
    l.terminal_type,
    l.cash_tolerance,
    t.transaction_date,
    t.daily_cash_dispensed,
    -- Rolling 30-day average cash burn per ATM
    AVG(t.daily_cash_dispensed) OVER (
        PARTITION BY t.atm_id
        ORDER BY t.transaction_date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30d_avg_burn,
    -- Day-of-week average for pattern detection
    AVG(t.daily_cash_dispensed) OVER (
        PARTITION BY t.atm_id, DAYOFWEEK(t.transaction_date)
    ) AS dow_avg_burn,
    -- Rank by cash burn within location type
    RANK() OVER (
        PARTITION BY l.location_type
        ORDER BY t.daily_cash_dispensed DESC
    ) AS burn_rank_in_type
FROM atm_transactions t
INNER JOIN atm_master l
    ON t.atm_id = l.atm_id
WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY t.atm_id, t.transaction_date;
```

**Live execution output — MySQL Workbench:**

> *Query 1 shares the rolling burn rate logic validated in Query 2's output below. See `screenshots/atm_query2_72hr_forecast.png` for the window function results in action.*

---

### Query 2 — 72-Hour Cash Runway Forecast
Window functions: `LAG()`, rolling `AVG() OVER` with frame specification, CTEs

```sql
WITH daily_burn AS (
    SELECT
        t.atm_id,
        t.transaction_date,
        t.cash_balance_eod,
        t.daily_cash_dispensed,
        LAG(t.cash_balance_eod, 1) OVER (
            PARTITION BY t.atm_id
            ORDER BY t.transaction_date
        ) AS prev_day_balance,
        AVG(t.daily_cash_dispensed) OVER (
            PARTITION BY t.atm_id
            ORDER BY t.transaction_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_7d_burn,
        AVG(t.daily_cash_dispensed) OVER (
            PARTITION BY t.atm_id
            ORDER BY t.transaction_date
            ROWS BETWEEN 13 PRECEDING AND 7 PRECEDING
        ) AS prior_week_avg_burn
    FROM atm_transactions t
    WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
),
forecast AS (
    SELECT
        db.atm_id,
        l.location_name,
        l.location_type,
        l.terminal_type,
        l.cash_tolerance,
        l.cash_capacity_dollars,
        l.distance_from_branch_miles,
        l.tax_service_proximity,
        db.cash_balance_eod                                            AS current_balance,
        db.rolling_7d_burn                                             AS avg_daily_burn,
        db.cash_balance_eod - (db.rolling_7d_burn * 3)                AS projected_72hr_balance,
        ROUND(((db.cash_balance_eod - (db.rolling_7d_burn * 3))
            / l.cash_capacity_dollars) * 100, 1)                      AS projected_pct_remaining,
        ROUND(db.cash_balance_eod / NULLIF(db.rolling_7d_burn,0), 1)  AS days_until_empty,
        CASE WHEN db.rolling_7d_burn > db.prior_week_avg_burn * 1.20
             THEN 'ACCELERATING' ELSE 'STABLE' END                    AS burn_trend,
        CASE l.terminal_type
            WHEN 'Over The Road' THEN 4.0
            WHEN 'Remote'        THEN 3.0
            WHEN 'Local'         THEN 2.5
        END                                                            AS emergency_multiplier,
        CASE l.location_type
            WHEN 'Casino'   THEN 850  WHEN 'Airport'  THEN 420
            WHEN 'Arena'    THEN 380  WHEN 'Stadium'  THEN 380
            WHEN 'Hospital' THEN 290  WHEN 'Mall'     THEN 240
            WHEN 'Urban'    THEN 210  WHEN 'Tourist'  THEN 190
            WHEN 'Office'   THEN 160  WHEN 'Retail'   THEN 120
        END                                                            AS revenue_impact_per_hour
    FROM daily_burn db
    INNER JOIN atm_master l ON db.atm_id = l.atm_id
    WHERE db.transaction_date = (SELECT MAX(transaction_date) FROM atm_transactions)
)
SELECT
    f.*,
    f.revenue_impact_per_hour * 72 AS revenue_at_risk_72hr,
    CASE f.cash_tolerance
        WHEN 'Zero' THEN 30  WHEN 'Low'    THEN 25
        WHEN 'Medium' THEN 20  WHEN 'High' THEN 15
    END AS critical_threshold_pct,
    CASE
        WHEN f.projected_pct_remaining <= (
            CASE f.cash_tolerance
                WHEN 'Zero' THEN 30  WHEN 'Low'    THEN 25
                WHEN 'Medium' THEN 20  WHEN 'High' THEN 15
            END
        ) THEN 'CRITICAL' ELSE 'ELEVATED'
    END AS risk_status
FROM forecast f
ORDER BY projected_pct_remaining ASC;
```

**Live execution output — MySQL Workbench:**

![Query 2 — 72-Hour Forecast Results (Top)](https://raw.githubusercontent.com/SEANSKIDATA/ATM-Predictive-Demand-Model/main/screenshots/atm_query2_72hr_forecast.png)
![Query 2 — 72-Hour Forecast Results (Full)](https://raw.githubusercontent.com/SEANSKIDATA/ATM-Predictive-Demand-Model/main/screenshots/atm_query2_72hr_forecast2.png)

---

### Query 3 — Composite Risk Score Priority Register
Window functions: `RANK() OVER`, `PERCENT_RANK() OVER`, `PARTITION BY`

```sql
WITH risk_scored AS (
    SELECT
        f.atm_id,
        f.location_name,
        f.location_type,
        f.terminal_type,
        f.cash_tolerance,
        f.projected_pct_remaining,
        f.days_until_empty,
        f.revenue_impact_per_hour,
        f.revenue_at_risk_72hr,
        f.burn_trend,
        f.tax_service_proximity,
        GREATEST(0, (30 - f.projected_pct_remaining) * 2) +
        CASE f.terminal_type
            WHEN 'Over The Road' THEN 40
            WHEN 'Remote'        THEN 20
            WHEN 'Local'         THEN 5
        END +
        CASE f.cash_tolerance
            WHEN 'Zero'   THEN 35  WHEN 'Low'    THEN 20
            WHEN 'Medium' THEN 10  WHEN 'High'   THEN 0
        END +
        (f.revenue_impact_per_hour / 20) +
        CASE WHEN f.tax_service_proximity = TRUE
              AND MONTH(CURDATE()) IN (2,3) THEN 25 ELSE 0
        END AS composite_risk_score
    FROM forecast f
)
SELECT
    rs.*,
    RANK() OVER (ORDER BY rs.composite_risk_score DESC)             AS priority_rank,
    RANK() OVER (
        PARTITION BY rs.location_type
        ORDER BY rs.composite_risk_score DESC
    )                                                               AS rank_within_type,
    ROUND(PERCENT_RANK() OVER (
        ORDER BY rs.composite_risk_score) * 100, 1)                AS network_percentile
FROM risk_scored rs
ORDER BY composite_risk_score DESC;
```

**Live execution output — MySQL Workbench:**

![Query 3 — Risk Score Results](https://raw.githubusercontent.com/SEANSKIDATA/ATM-Predictive-Demand-Model/main/screenshots/atm_query3_risk_score.png)
![Query 3 — Risk Score Priority Rank](https://raw.githubusercontent.com/SEANSKIDATA/ATM-Predictive-Demand-Model/main/screenshots/atm_query3_risk_score2.png)

---

### Query 4 — Tax Season Demand Pattern Analysis
Window functions: Seasonal lift vs baseline using CTEs and `INNER JOIN`

```sql
WITH seasonal_stats AS (
    SELECT
        t.atm_id,
        l.location_type,
        l.tax_service_proximity,
        CASE
            WHEN MONTH(t.transaction_date) = 2
             AND DAY(t.transaction_date) >= 15   THEN 'Tax Season Peak'
            WHEN MONTH(t.transaction_date) = 3
             AND DAY(t.transaction_date) <= 15   THEN 'Tax Season Peak'
            WHEN MONTH(t.transaction_date) IN (1,4)   THEN 'Tax Season Ramp'
            WHEN MONTH(t.transaction_date) IN (11,12) THEN 'Holiday'
            ELSE 'Baseline'
        END AS season,
        AVG(t.daily_cash_dispensed)  AS avg_daily_cash,
        AVG(t.avg_withdrawal_amount) AS avg_withdrawal,
        AVG(t.daily_transactions)    AS avg_transactions
    FROM atm_transactions t
    INNER JOIN atm_master l ON t.atm_id = l.atm_id
    GROUP BY t.atm_id, l.location_type, l.tax_service_proximity, season
),
baseline AS (
    SELECT atm_id, location_type, tax_service_proximity,
           avg_daily_cash AS baseline_cash
    FROM seasonal_stats WHERE season = 'Baseline'
)
SELECT
    ss.location_type,
    ss.tax_service_proximity,
    ss.season,
    ROUND(AVG(ss.avg_daily_cash), 0)    AS avg_daily_cash,
    ROUND(AVG(ss.avg_withdrawal), 2)    AS avg_withdrawal,
    ROUND(AVG(ss.avg_transactions), 0)  AS avg_transactions,
    ROUND(((AVG(ss.avg_daily_cash) - AVG(b.baseline_cash))
        / NULLIF(AVG(b.baseline_cash), 0)) * 100, 1) AS pct_lift_vs_baseline
FROM seasonal_stats ss
INNER JOIN baseline b ON ss.atm_id = b.atm_id
GROUP BY ss.location_type, ss.tax_service_proximity, ss.season
ORDER BY ss.location_type, ss.tax_service_proximity DESC, pct_lift_vs_baseline DESC;
```

**Live execution output — MySQL Workbench:**

![Query 4 — Tax Season Analysis (Code)](https://raw.githubusercontent.com/SEANSKIDATA/ATM-Predictive-Demand-Model/main/screenshots/atm_query4_tax_season.png)
![Query 4 — Tax Season Analysis (Results)](https://raw.githubusercontent.com/SEANSKIDATA/ATM-Predictive-Demand-Model/main/screenshots/atm_query4_tax_season2.png)

---

### Query 5 — Day-of-Week Demand Pattern by Terminal Tier
Window functions: Nested `AVG() OVER (PARTITION BY)` for demand index

```sql
SELECT
    l.terminal_type,
    DAYNAME(t.transaction_date)           AS day_of_week,
    DAYOFWEEK(t.transaction_date)         AS day_num,
    ROUND(AVG(t.daily_cash_dispensed), 0) AS avg_daily_cash,
    ROUND(AVG(t.daily_transactions), 0)   AS avg_transactions,
    ROUND(
        AVG(t.daily_cash_dispensed) - AVG(AVG(t.daily_cash_dispensed)) OVER (
            PARTITION BY l.terminal_type
        ), 0
    )                                     AS deviation_from_weekly_avg,
    ROUND(
        AVG(t.daily_cash_dispensed) / NULLIF(
            AVG(AVG(t.daily_cash_dispensed)) OVER (
                PARTITION BY l.terminal_type
            ), 0
        ), 3
    )                                     AS demand_index
FROM atm_transactions t
INNER JOIN atm_master l ON t.atm_id = l.atm_id
GROUP BY l.terminal_type, DAYNAME(t.transaction_date), DAYOFWEEK(t.transaction_date)
ORDER BY l.terminal_type, DAYOFWEEK(t.transaction_date);
```

**Live execution output — MySQL Workbench:**

![Query 5 — Day of Week Demand (Code)](https://raw.githubusercontent.com/SEANSKIDATA/ATM-Predictive-Demand-Model/main/screenshots/atm_query5_dow_demand.png)
![Query 5 — Day of Week Demand (Results)](https://raw.githubusercontent.com/SEANSKIDATA/ATM-Predictive-Demand-Model/main/screenshots/atm_query5_dow_demand2.png)

---

## Technical Skills Demonstrated

`Python` · `Pandas` · `NumPy` · `Matplotlib` · `Tableau` · `SQL` · `Window Functions` · `CTEs` · `Time-Series Analysis` · `Predictive Modeling` · `Seasonal Demand Modeling` · `Synthetic Dataset Design` · `Operational Risk Scoring` · `Data Visualization` · `Model Validation`

---

## Portfolio Progression

| Project | Tool | Business Question |
|---|---|---|
| [ATM-Network-Risk-Intelligence](https://github.com/SEANSKIDATA/ATM-Network-Risk-Intelligence) | SQL | What is the current risk state of the network? |
| [ATM-Network-Analysis-Version-2](https://github.com/SEANSKIDATA/ATM-Network-Analysis-Version-2) | SQL | How do we prioritize replenishment decisions? |
| **ATM-Predictive-Demand-Model** | **Python + Tableau** | **Which ATMs will go critical in the next 72 hours?** |

---

## Data Disclosure

All data in this project is synthetic — purpose-built to reflect realistic ATM network operating conditions including real-world seasonal demand patterns. No proprietary, personally identifiable, or confidential information is included.

---

*Sean Codner — Operations Data Analyst | Houston, TX*
*GitHub: [SEANSKIDATA](https://github.com/SEANSKIDATA) | LinkedIn: [Sean Codner](https://www.linkedin.com/in/sean-codner-aa60822b)*
