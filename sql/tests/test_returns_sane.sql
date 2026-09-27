-- Only the first day per ticker may have a NULL return, and no daily move may exceed ±35%.
SELECT ticker, date, daily_return FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date) AS rn FROM marts.daily_returns
) WHERE (rn > 1 AND daily_return IS NULL) OR ABS(daily_return) > 0.35;
