USE atm_predictive_model;

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
    FROM atm_forecast f
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