-- One row per ticker per date. Returns duplicates.
SELECT ticker, date, COUNT(*) FROM marts.daily_returns GROUP BY ticker, date HAVING COUNT(*) > 1;
