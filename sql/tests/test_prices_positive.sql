-- Prices must be positive. Returns offending rows.
SELECT ticker, date, close FROM staging.clean_prices WHERE close IS NULL OR close <= 0;
