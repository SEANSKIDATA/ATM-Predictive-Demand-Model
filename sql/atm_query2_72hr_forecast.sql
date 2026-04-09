USE atm_predictive_model;

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
    WHERE t.transaction_date >= '2024-12-01'
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
        ROUND(db.cash_balance_eod, 2)                                          AS current_balance,
        ROUND(db.rolling_7d_burn, 2)                                         AS avg_daily_burn,
        ROUND(db.cash_balance_eod - (db.rolling_7d_burn * 3), 2)  AS projected_72hr_balance,                
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