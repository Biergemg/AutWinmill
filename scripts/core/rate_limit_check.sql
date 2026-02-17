WITH cfg AS (
  SELECT max_per_min FROM rate_limits WHERE source = :source
),
recent AS (
  SELECT COUNT(*) AS hits
  FROM rate_limit_hits
  WHERE source = :source
    AND ts > NOW() - INTERVAL '60 seconds'
)
SELECT
  CASE WHEN COALESCE((SELECT hits FROM recent),0) < COALESCE((SELECT max_per_min FROM cfg),0) THEN TRUE ELSE FALSE END AS allowed,
  COALESCE((SELECT hits FROM recent),0) AS hits,
  COALESCE((SELECT max_per_min FROM cfg),0) AS limit;
