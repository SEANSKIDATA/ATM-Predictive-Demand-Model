USE atm_predictive_model;
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
WHERE t.transaction_date >= '2024-12-01'
ORDER BY t.atm_id, t.transaction_date;