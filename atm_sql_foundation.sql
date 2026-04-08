-- =============================================================================
-- ATM PREDICTIVE DEMAND MODEL — SQL FOUNDATION LAYER
-- SEANSKIDATA Analytics Portfolio — Project 3
-- =============================================================================
-- PURPOSE:
-- These queries represent the analytical foundation that feeds the Python
-- predictive model. In a production environment, this SQL layer would run
-- against the operational database before the Python forecast is generated.
--
-- The Python model replicates this logic on synthetic data — demonstrating
-- the full analytical pipeline from raw transaction data to risk scoring.
-- =============================================================================


-- =============================================================================
-- QUERY 1 — DAILY CASH BURN RATE BY ATM (Rolling 30-Day Average)
-- Window function: AVG() OVER with ROWS BETWEEN frame
-- Used in Python as: dow_burn calculation for 72-hour forecast
-- =============================================================================

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


-- =============================================================================
-- QUERY 2 — 72-HOUR CASH RUNWAY FORECAST
-- Joins: transactions + locations + replenishment schedule
-- Window function: LAG() to detect burn acceleration
-- =============================================================================

WITH daily_burn AS (
    SELECT
        t.atm_id,
        t.transaction_date,
        t.cash_balance_eod,
        t.daily_cash_dispensed,
        -- Previous day balance for burn rate calculation
        LAG(t.cash_balance_eod, 1) OVER (
            PARTITION BY t.atm_id
            ORDER BY t.transaction_date
        ) AS prev_day_balance,
        -- 7-day rolling burn for forecast smoothing
        AVG(t.daily_cash_dispensed) OVER (
            PARTITION BY t.atm_id
            ORDER BY t.transaction_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_7d_burn,
        -- Detect burn acceleration vs prior week
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
        db.cash_balance_eod AS current_balance,
        db.rolling_7d_burn AS avg_daily_burn,
        -- 72-hour projected balance
        db.cash_balance_eod - (db.rolling_7d_burn * 3) AS projected_72hr_balance,
        -- Percentage remaining after 72 hours
        ROUND(
            ((db.cash_balance_eod - (db.rolling_7d_burn * 3)) / l.cash_capacity_dollars) * 100,
            1
        ) AS projected_pct_remaining,
        -- Days until empty at current burn rate
        ROUND(db.cash_balance_eod / NULLIF(db.rolling_7d_burn, 0), 1) AS days_until_empty,
        -- Burn acceleration flag (>20% increase week over week)
        CASE
            WHEN db.rolling_7d_burn > db.prior_week_avg_burn * 1.20
            THEN 'ACCELERATING'
            ELSE 'STABLE'
        END AS burn_trend,
        -- Emergency replenishment multiplier
        CASE l.terminal_type
            WHEN 'Over The Road' THEN 4.0
            WHEN 'Remote'        THEN 3.0
            WHEN 'Local'         THEN 2.5
        END AS emergency_multiplier,
        -- Revenue impact per hour of outage
        CASE l.location_type
            WHEN 'Casino'   THEN 850
            WHEN 'Airport'  THEN 420
            WHEN 'Arena'    THEN 380
            WHEN 'Stadium'  THEN 380
            WHEN 'Hospital' THEN 290
            WHEN 'Mall'     THEN 240
            WHEN 'Urban'    THEN 210
            WHEN 'Tourist'  THEN 190
            WHEN 'Office'   THEN 160
            WHEN 'Retail'   THEN 120
        END AS revenue_impact_per_hour
    FROM daily_burn db
    INNER JOIN atm_master l
        ON db.atm_id = l.atm_id
    WHERE db.transaction_date = (
        SELECT MAX(transaction_date) FROM atm_transactions
    )
)
SELECT
    f.*,
    -- Revenue at risk over full 72-hour outage
    f.revenue_impact_per_hour * 72 AS revenue_at_risk_72hr,
    -- Critical threshold by cash tolerance
    CASE f.cash_tolerance
        WHEN 'Zero'   THEN 30
        WHEN 'Low'    THEN 25
        WHEN 'Medium' THEN 20
        WHEN 'High'   THEN 15
    END AS critical_threshold_pct,
    -- Critical flag
    CASE
        WHEN f.projected_pct_remaining <= (
            CASE f.cash_tolerance
                WHEN 'Zero'   THEN 30
                WHEN 'Low'    THEN 25
                WHEN 'Medium' THEN 20
                WHEN 'High'   THEN 15
            END
        ) THEN 'CRITICAL'
        ELSE 'ELEVATED'
    END AS risk_status
FROM forecast f
ORDER BY projected_pct_remaining ASC;


-- =============================================================================
-- QUERY 3 — COMPOSITE RISK SCORE PRIORITY REGISTER
-- Combines: cash position + distance + tolerance + revenue impact
-- Window function: RANK() for network-wide priority ordering
-- =============================================================================

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
        -- Composite risk score calculation
        -- Component 1: Cash depletion urgency (0-60 pts)
        GREATEST(0, (30 - f.projected_pct_remaining) * 2) +
        -- Component 2: Terminal type / distance weight (5-40 pts)
        CASE f.terminal_type
            WHEN 'Over The Road' THEN 40
            WHEN 'Remote'        THEN 20
            WHEN 'Local'         THEN 5
        END +
        -- Component 3: Cash tolerance weight (0-35 pts)
        CASE f.cash_tolerance
            WHEN 'Zero'   THEN 35
            WHEN 'Low'    THEN 20
            WHEN 'Medium' THEN 10
            WHEN 'High'   THEN 0
        END +
        -- Component 4: Revenue impact weight
        (f.revenue_impact_per_hour / 20) +
        -- Component 5: Tax service proximity premium (seasonal)
        CASE
            WHEN f.tax_service_proximity = TRUE
            AND MONTH(CURDATE()) IN (2, 3)
            THEN 25
            ELSE 0
        END AS composite_risk_score
    FROM forecast f
)
SELECT
    rs.*,
    -- Network-wide priority rank
    RANK() OVER (
        ORDER BY rs.composite_risk_score DESC
    ) AS priority_rank,
    -- Rank within location type
    RANK() OVER (
        PARTITION BY rs.location_type
        ORDER BY rs.composite_risk_score DESC
    ) AS rank_within_type,
    -- Percentile in network
    ROUND(
        PERCENT_RANK() OVER (
            ORDER BY rs.composite_risk_score
        ) * 100,
        1
    ) AS network_percentile
FROM risk_scored rs
ORDER BY composite_risk_score DESC;


-- =============================================================================
-- QUERY 4 — TAX SEASON DEMAND PATTERN ANALYSIS
-- Window function: seasonal comparison vs baseline
-- Used to validate Python tax season multipliers
-- =============================================================================

WITH seasonal_stats AS (
    SELECT
        t.atm_id,
        l.location_type,
        l.tax_service_proximity,
        -- Season classification
        CASE
            WHEN MONTH(t.transaction_date) = 2
             AND DAY(t.transaction_date) >= 15  THEN 'Tax Season Peak'
            WHEN MONTH(t.transaction_date) = 3
             AND DAY(t.transaction_date) <= 15  THEN 'Tax Season Peak'
            WHEN MONTH(t.transaction_date) = 1  THEN 'Tax Season Ramp'
            WHEN MONTH(t.transaction_date) = 4  THEN 'Tax Season Ramp'
            WHEN MONTH(t.transaction_date) IN (11,12) THEN 'Holiday'
            ELSE 'Baseline'
        END AS season,
        AVG(t.daily_cash_dispensed) AS avg_daily_cash,
        AVG(t.avg_withdrawal_amount) AS avg_withdrawal,
        AVG(t.daily_transactions) AS avg_transactions
    FROM atm_transactions t
    INNER JOIN atm_master l ON t.atm_id = l.atm_id
    GROUP BY
        t.atm_id,
        l.location_type,
        l.tax_service_proximity,
        CASE
            WHEN MONTH(t.transaction_date) = 2
             AND DAY(t.transaction_date) >= 15  THEN 'Tax Season Peak'
            WHEN MONTH(t.transaction_date) = 3
             AND DAY(t.transaction_date) <= 15  THEN 'Tax Season Peak'
            WHEN MONTH(t.transaction_date) = 1  THEN 'Tax Season Ramp'
            WHEN MONTH(t.transaction_date) = 4  THEN 'Tax Season Ramp'
            WHEN MONTH(t.transaction_date) IN (11,12) THEN 'Holiday'
            ELSE 'Baseline'
        END
),
baseline AS (
    SELECT
        atm_id,
        location_type,
        tax_service_proximity,
        avg_daily_cash AS baseline_cash,
        avg_withdrawal AS baseline_withdrawal,
        avg_transactions AS baseline_transactions
    FROM seasonal_stats
    WHERE season = 'Baseline'
)
SELECT
    ss.location_type,
    ss.tax_service_proximity,
    ss.season,
    ROUND(AVG(ss.avg_daily_cash), 0)        AS avg_daily_cash,
    ROUND(AVG(ss.avg_withdrawal), 2)         AS avg_withdrawal,
    ROUND(AVG(ss.avg_transactions), 0)       AS avg_transactions,
    -- Lift vs baseline
    ROUND(
        ((AVG(ss.avg_daily_cash) - AVG(b.baseline_cash))
        / NULLIF(AVG(b.baseline_cash), 0)) * 100,
        1
    ) AS pct_lift_vs_baseline
FROM seasonal_stats ss
INNER JOIN baseline b
    ON ss.atm_id = b.atm_id
GROUP BY
    ss.location_type,
    ss.tax_service_proximity,
    ss.season
ORDER BY
    ss.location_type,
    ss.tax_service_proximity DESC,
    pct_lift_vs_baseline DESC;


-- =============================================================================
-- QUERY 5 — DAY-OF-WEEK DEMAND PATTERN BY TERMINAL TIER
-- Window function: deviation from weekly average
-- =============================================================================

SELECT
    l.terminal_type,
    DAYNAME(t.transaction_date)                      AS day_of_week,
    DAYOFWEEK(t.transaction_date)                    AS day_num,
    ROUND(AVG(t.daily_cash_dispensed), 0)            AS avg_daily_cash,
    ROUND(AVG(t.daily_transactions), 0)              AS avg_transactions,
    -- Deviation from that terminal type's weekly average
    ROUND(
        AVG(t.daily_cash_dispensed) - AVG(AVG(t.daily_cash_dispensed)) OVER (
            PARTITION BY l.terminal_type
        ),
        0
    ) AS deviation_from_weekly_avg,
    -- Index vs weekly average (1.0 = average day)
    ROUND(
        AVG(t.daily_cash_dispensed) / NULLIF(
            AVG(AVG(t.daily_cash_dispensed)) OVER (
                PARTITION BY l.terminal_type
            ),
            0
        ),
        3
    ) AS demand_index
FROM atm_transactions t
INNER JOIN atm_master l ON t.atm_id = l.atm_id
GROUP BY
    l.terminal_type,
    DAYNAME(t.transaction_date),
    DAYOFWEEK(t.transaction_date)
ORDER BY
    l.terminal_type,
    DAYOFWEEK(t.transaction_date);
