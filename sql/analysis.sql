-- 04-finance-portfolio — drawdown anatomy in SQL (window functions).
-- Loads: data/processed/spx.csv -> table `spx` (Date, SP500, real_idx).

-- Drawdown depth per month vs running peak
WITH d AS (
  SELECT Date, SP500,
         MAX(SP500) OVER (ORDER BY Date)                 AS peak_so_far,
         SP500 / MAX(SP500) OVER (ORDER BY Date) - 1.0   AS drawdown
  FROM spx
)
-- Deepest monthly drawdowns (top 10) — full episode detection is in Python (01_analysis.py)
SELECT Date, SP500, peak_so_far, ROUND(drawdown * 100, 1) AS drawdown_pct
FROM d ORDER BY drawdown ASC LIMIT 10;

-- Real vs nominal cumulative growth by decade
SELECT
  CAST(EXTRACT(YEAR FROM Date) / 10 AS INT64) * 10 AS decade,
  ROUND(100.0 * (MAX(SP500) / MIN(SP500) - 1), 1)   AS nominal_growth_pct,
  ROUND(100.0 * (MAX(real_idx) / MIN(real_idx) - 1), 1) AS real_growth_pct
FROM spx GROUP BY decade ORDER BY decade;
