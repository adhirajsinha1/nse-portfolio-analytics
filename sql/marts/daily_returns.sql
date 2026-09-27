-- daily_returns: one row per ticker per trading day with its daily return
--
-- simple return = today's close / yesterday's close - 1   (e.g. 0.012 = +1.2%)
-- log return    = ln(today / yesterday)                   (adds up nicely over time; used in some risk maths)
-- The first day of each ticker has no previous close, so its return is NULL.
CREATE OR REPLACE TABLE marts.daily_returns AS
SELECT
    p.date,
    p.ticker,
    u.name,
    u.sector,
    p.close,
    p.close / LAG(p.close) OVER w - 1   AS daily_return,
    LN(p.close / LAG(p.close) OVER w)   AS log_return
FROM staging.clean_prices p
JOIN raw.universe u ON p.ticker = u.ticker
WINDOW w AS (PARTITION BY p.ticker ORDER BY p.date);
