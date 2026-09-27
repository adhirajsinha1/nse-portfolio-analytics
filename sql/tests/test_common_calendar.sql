-- Every ticker must have exactly as many trading days as the Nifty index. Returns tickers that don't.
SELECT ticker, COUNT(*) AS days
FROM marts.daily_returns
GROUP BY ticker
HAVING COUNT(*) <> (SELECT COUNT(*) FROM marts.daily_returns WHERE ticker = '^NSEI');
