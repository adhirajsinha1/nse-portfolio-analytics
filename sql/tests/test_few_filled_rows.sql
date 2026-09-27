-- Carried-forward prices should be rare (< 0.1% of rows). Returns a row if there are too many.
SELECT SUM(CASE WHEN is_filled THEN 1 ELSE 0 END) AS filled, COUNT(*) AS total
FROM staging.clean_prices
HAVING SUM(CASE WHEN is_filled THEN 1 ELSE 0 END) > 0.001 * COUNT(*);
