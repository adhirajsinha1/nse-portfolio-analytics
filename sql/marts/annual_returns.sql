-- annual_returns: one row per ticker per calendar year
-- return = last close of the year / last close of the previous year - 1
-- (the first year, 2016, is measured from the first trading day instead)
CREATE OR REPLACE TABLE marts.annual_returns AS
WITH year_end AS (
    SELECT ticker, name, sector, YEAR(date) AS year,
           ARG_MAX(close, date) AS year_end_close,     -- close on the last trading day of the year
           ARG_MIN(close, date) AS year_start_close,   -- close on the first trading day of the year
           MAX(date)            AS last_date
    FROM marts.daily_returns
    GROUP BY ticker, name, sector, YEAR(date)
)
SELECT ticker, name, sector, year, last_date,
       year_end_close / COALESCE(LAG(year_end_close) OVER (PARTITION BY ticker ORDER BY year), year_start_close) - 1
           AS annual_return,
       year = YEAR(CURRENT_DATE) OR last_date < MAKE_DATE(year, 12, 20) AS is_partial_year
FROM year_end;
