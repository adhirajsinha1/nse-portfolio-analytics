-- No zero-volume rows with an unchanged price should remain (index volume is often 0, so stocks only).
SELECT ticker, date FROM (
    SELECT ticker, date, volume, close, LAG(close) OVER (PARTITION BY ticker ORDER BY date) AS prev
    FROM staging.clean_prices
) WHERE volume = 0 AND close = prev AND ticker <> '^NSEI';
