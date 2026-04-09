USE atm_predictive_model;
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