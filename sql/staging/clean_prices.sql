-- clean_prices: one row per ticker per trading day, on a common calendar, with the Day 1 fixes applied
--
--   1. Drop provider-filled holiday rows (volume = 0 AND price unchanged from the previous row).
--   2. Build a common trading calendar: dates where the Nifty index traded AND at least 90% of
--      stocks have a real price (this removes glitch days like 18 Mar 2025, when 26 stocks were phantoms).
--   3. Put every ticker on that calendar. If a single stock has no real price on a calendar day,
--      carry forward its last price (= 0% return that day) and flag it as is_filled.
CREATE OR REPLACE TABLE staging.clean_prices AS
WITH flagged AS (
    SELECT *,
           volume = 0 AND close = LAG(close) OVER (PARTITION BY ticker ORDER BY date) AS is_phantom
    FROM raw.prices
),
real_rows AS (
    SELECT date, ticker, open, high, low, close, volume
    FROM flagged
    WHERE NOT COALESCE(is_phantom, FALSE)
),
calendar AS (
    SELECT date
    FROM real_rows
    GROUP BY date
    HAVING SUM(CASE WHEN ticker = '^NSEI' THEN 1 ELSE 0 END) = 1                         -- index traded
       AND SUM(CASE WHEN ticker <> '^NSEI' THEN 1 ELSE 0 END)
           >= 0.9 * (SELECT COUNT(*) FROM raw.universe WHERE ticker <> '^NSEI')          -- ≥90% of stocks traded
),
grid AS (
    -- every ticker × every calendar date (CROSS JOIN = all combinations)
    SELECT c.date, u.ticker
    FROM calendar c CROSS JOIN raw.universe u
)
SELECT
    g.date,
    g.ticker,
    r.open, r.high, r.low,
    -- LAST_VALUE(... IGNORE NULLS) = the most recent non-missing close up to this row
    LAST_VALUE(r.close IGNORE NULLS) OVER (PARTITION BY g.ticker ORDER BY g.date
                                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS close,
    r.volume,
    r.close IS NULL AS is_filled
FROM grid g
LEFT JOIN real_rows r ON g.date = r.date AND g.ticker = r.ticker;
