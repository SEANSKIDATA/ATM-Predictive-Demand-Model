USE atm_predictive_model;
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