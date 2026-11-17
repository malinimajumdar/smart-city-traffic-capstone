-- Task 3.1: Basic Probability Analysis

SELECT
    COUNT(*) AS total_hours,

    SUM(CASE
        WHEN traffic_volume > 5500
        THEN 1 ELSE 0
    END) AS congestion_hours,

    SUM(CASE
        WHEN weather_main = 'Clear'
        THEN 1 ELSE 0
    END) AS clear_weather_hours,

    SUM(CASE
        WHEN traffic_volume > 5500
         AND weather_main = 'Clear'
        THEN 1 ELSE 0
    END) AS congestion_and_clear_hours,

    ROUND(AVG(CASE
        WHEN traffic_volume > 5500
        THEN 1.0 ELSE 0.0
    END), 4) AS p_congestion,

    ROUND(AVG(CASE
        WHEN weather_main = 'Clear'
        THEN 1.0 ELSE 0.0
    END), 4) AS p_clear_weather,

    ROUND(AVG(CASE
        WHEN traffic_volume > 5500
         AND weather_main = 'Clear'
        THEN 1.0 ELSE 0.0
    END), 4) AS p_congestion_and_clear

FROM metro_traffic_clean;

-- Task 3.2: Conditional Probabilities

SELECT
    SUM(CASE
        WHEN traffic_volume > 5500
        THEN 1 ELSE 0
    END) AS congestion_hours,

    ROUND(
        1.0 * SUM(CASE
            WHEN traffic_volume > 5500
             AND weather_main = 'Clear'
            THEN 1 ELSE 0
        END)
        /
        NULLIF(SUM(CASE
            WHEN traffic_volume > 5500
            THEN 1 ELSE 0
        END), 0),
        4
    ) AS p_clear_given_congestion,

    ROUND(
        1.0 * SUM(CASE
            WHEN traffic_volume > 5500
             AND temp > 292
            THEN 1 ELSE 0
        END)
        /
        NULLIF(SUM(CASE
            WHEN traffic_volume > 5500
            THEN 1 ELSE 0
        END), 0),
        4
    ) AS p_high_temp_given_congestion

FROM metro_traffic_clean;


-- Task 3.2: Independence Test

WITH probabilities AS (
    SELECT
        AVG(CASE
            WHEN traffic_volume > 5500
            THEN 1.0 ELSE 0.0
        END) AS p_congestion,

        AVG(CASE
            WHEN weather_main = 'Clear'
            THEN 1.0 ELSE 0.0
        END) AS p_clear,

        AVG(CASE
            WHEN traffic_volume > 5500
             AND weather_main = 'Clear'
            THEN 1.0 ELSE 0.0
        END) AS p_joint
    FROM metro_traffic_clean
)
SELECT
    ROUND(p_joint, 5)
        AS observed_joint_probability,

    ROUND(p_congestion * p_clear, 5)
        AS expected_if_independent,

    ROUND(
        p_joint - (p_congestion * p_clear),
        5
    ) AS difference,

    CASE
        WHEN ABS(
            p_joint - p_congestion * p_clear
        ) < 0.000001
        THEN 'Independent'
        ELSE 'Not Independent'
    END AS independence_result

FROM probabilities;


-- Task 3.2: Odds Ratio
-- Clear Weather vs Cloudy Weather

WITH counts AS (
    SELECT
        SUM(CASE
            WHEN weather_main = 'Clear'
             AND traffic_volume > 5500
            THEN 1 ELSE 0
        END) AS clear_congested,

        SUM(CASE
            WHEN weather_main = 'Clear'
             AND traffic_volume <= 5500
            THEN 1 ELSE 0
        END) AS clear_not_congested,

        SUM(CASE
            WHEN weather_main = 'Clouds'
             AND traffic_volume > 5500
            THEN 1 ELSE 0
        END) AS cloudy_congested,

        SUM(CASE
            WHEN weather_main = 'Clouds'
             AND traffic_volume <= 5500
            THEN 1 ELSE 0
        END) AS cloudy_not_congested

    FROM metro_traffic_clean
)
SELECT
    clear_congested,
    clear_not_congested,
    cloudy_congested,
    cloudy_not_congested,

    ROUND(
        (1.0 * clear_congested
         * cloudy_not_congested)
        /
        NULLIF(
            clear_not_congested
            * cloudy_congested, 0
        ),
        4
    ) AS odds_ratio

FROM counts;
