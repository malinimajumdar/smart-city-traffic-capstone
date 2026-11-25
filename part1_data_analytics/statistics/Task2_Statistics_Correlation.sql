SELECT COUNT(*)
FROM metro_traffic_clean;

--Step I- To find five statistics

WITH RECURSIVE
ordered_data AS (
    SELECT
        traffic_volume,
        ROW_NUMBER() OVER (
            ORDER BY traffic_volume
        ) AS rn,
        COUNT(*) OVER () AS n
    FROM metro_traffic_clean
),

median_calc AS (
    SELECT
        AVG(traffic_volume * 1.0) AS median_volume
    FROM ordered_data
    WHERE rn IN (
        (n + 1) / 2,
        (n + 2) / 2
    )
),

stats AS (
    SELECT
        COUNT(*) AS total_hours,
        AVG(traffic_volume) AS mean_volume,
        AVG(traffic_volume * 1.0 * traffic_volume)
          - AVG(traffic_volume) * AVG(traffic_volume)
          AS variance,
        MIN(traffic_volume) AS min_volume,
        MAX(traffic_volume) AS max_volume
    FROM metro_traffic_clean
	
),

sqrt_calc(step, estimate) AS (
    SELECT
        0,
        CASE WHEN variance > 0
             THEN variance
             ELSE 0.0 END
    FROM stats

    UNION ALL

    SELECT
        step + 1,
        (estimate + variance / estimate) / 2.0
    FROM sqrt_calc
    CROSS JOIN stats
    WHERE step < 30
      AND estimate > 0
)

SELECT
    s.total_hours,
    ROUND(s.mean_volume, 2) AS mean,
    ROUND(m.median_volume, 2) AS median,
    ROUND(q.estimate, 2) AS standard_deviation,
    ROUND(s.variance, 2) AS variance,
    s.min_volume AS minimum,
    s.max_volume AS maximum,
    s.max_volume - s.min_volume AS range

FROM stats s
CROSS JOIN median_calc m
CROSS JOIN sqrt_calc q
WHERE q.step = (
    SELECT MAX(step)
    FROM sqrt_calc
);

--Step II Correlation Analysis – Temperature and Traffic Volume
WITH RECURSIVE

-- Step 1: Exclude invalid temperature values
valid_data AS (
    SELECT
        temp - 273.15 AS temperature_c,
        traffic_volume
    FROM metro_traffic_clean
    WHERE temp > 0
      AND traffic_volume is NOT NULL
),

-- Step 2: Calculate statistical components
statistics AS (
    SELECT
        COUNT(*) AS total_observations,

        AVG(temperature_c) AS avg_temp,
        AVG(traffic_volume) AS avg_traffic,

        AVG(temperature_c * traffic_volume)
            AS avg_xy,

        AVG(temperature_c * temperature_c)
            AS avg_x2,

        AVG(traffic_volume * 1.0 * traffic_volume)
            AS avg_y2

    FROM valid_data
),

-- Step 3: Calculate covariance and variances
components AS (
    SELECT
        total_observations,

        avg_xy - avg_temp * avg_traffic
            AS covariance,

        avg_x2 - avg_temp * avg_temp
            AS variance_x,

        avg_y2 - avg_traffic * avg_traffic
            AS variance_y

    FROM statistics
),

-- Step 4: Calculate the denominator squared
denominator AS (
    SELECT
        total_observations,
        covariance,
        variance_x * variance_y AS denominator_squared
    FROM components
),

-- Step 5: Calculate square root using Newton's method
sqrt_calc(step, estimate) AS (
    SELECT
        0,
        CASE
            WHEN denominator_squared > 0
            THEN denominator_squared
            ELSE 0.0
        END
    FROM denominator

    UNION ALL

    SELECT
        step + 1,
        (estimate + denominator_squared / estimate) / 2.0
    FROM sqrt_calc
    CROSS JOIN denominator
    WHERE step < 50
      AND estimate > 0
),

-- Step 6: Select the final square-root estimate
final_sqrt AS (
    SELECT estimate
    FROM sqrt_calc
    ORDER BY step DESC
    LIMIT 1
)

-- Step 7: Calculate Pearson correlation coefficient
SELECT
    d.total_observations,
    ROUND(
        d.covariance / NULLIF(f.estimate, 0),
        4
    ) AS pearson_correlation

FROM denominator d
CROSS JOIN final_sqrt f;


