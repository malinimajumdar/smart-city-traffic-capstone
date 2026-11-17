select * from Metro_Interstate_Traffic_Volume;

SELECT COUNT(*) AS total_records
FROM Metro_Interstate_Traffic_Volume;

SELECT COUNT(*) AS total_columns
FROM pragma_table_info('Metro_Interstate_Traffic_Volume');

PRAGMA table_info('Metro_Interstate_Traffic_Volume');

--Step 1 – Verify original data

SELECT COUNT(*) AS original_rows,
       COUNT(DISTINCT date_time) AS unique_hours,
       COUNT(*) - COUNT(DISTINCT date_time)
           AS excess_rows
FROM Metro_Interstate_Traffic_Volume;

--Step 2 – Verify whether traffic volumes differ within the same hour

SELECT date_time,
       COUNT(*) AS row_count,
       COUNT(DISTINCT traffic_volume)
           AS distinct_volumes
FROM Metro_Interstate_Traffic_Volume
GROUP BY date_time
HAVING COUNT(DISTINCT traffic_volume) > 1;

--Step 3 – Create a cleaned table

CREATE TABLE metro_traffic_clean AS
WITH ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY date_time
               ORDER BY
                   CASE weather_main
                       WHEN 'Thunderstorm' THEN 1
                       WHEN 'Snow' THEN 2
                       WHEN 'Rain' THEN 3
                       WHEN 'Drizzle' THEN 4
                       WHEN 'Fog' THEN 5
                       WHEN 'Mist' THEN 6
                       WHEN 'Haze' THEN 7
                       WHEN 'Smoke' THEN 8
                       WHEN 'Squall' THEN 9
                       WHEN 'Clouds' THEN 10
                       WHEN 'Clear' THEN 11
                       ELSE 12
                   END,
                   weather_description
           ) AS rn
    FROM Metro_Interstate_Traffic_Volume
)
SELECT
    holiday, temp, rain_1h, snow_1h,
    clouds_all, weather_main,
    weather_description, date_time,
    traffic_volume
FROM ranked
WHERE rn = 1;

--Step 4 – Verify cleaned dataset

SELECT
    COUNT(*) AS cleaned_rows,
    COUNT(DISTINCT date_time) AS unique_hours,
    COUNT(*) - COUNT(DISTINCT date_time)
        AS remaining_duplicates
FROM metro_traffic_clean;

--Step 5 - Analyse annual traffic trends

WITH annual_traffic AS (
    SELECT
        SUBSTR(date_time, 7, 4) AS year,
        COUNT(*) AS recorded_hours,
        SUM(traffic_volume) AS total_volume,
        ROUND(AVG(traffic_volume), 2)
            AS avg_hourly_volume
    FROM metro_traffic_clean
    WHERE SUBSTR(date_time, 7, 4)
          BETWEEN '2012' AND '2017'
    GROUP BY SUBSTR(date_time, 7, 4)
),
comparison AS (
    SELECT *,
        LAG(total_volume) OVER (ORDER BY year)
            AS prev_total,
        LAG(avg_hourly_volume) OVER (ORDER BY year)
            AS prev_avg
    FROM annual_traffic
)
SELECT
    year,
    recorded_hours,
    total_volume,
    avg_hourly_volume,
    total_volume - prev_total AS yoy_change,
    ROUND(
        100.0 * (total_volume - prev_total)
        / NULLIF(prev_total, 0), 2
    ) AS yoy_total_pct,
    ROUND(
        100.0 * (avg_hourly_volume - prev_avg)
        / NULLIF(prev_avg, 0), 2
    ) AS yoy_avg_hourly_pct
FROM comparison
ORDER BY year;


--Step 6 - Temperature Analysis Around Holidays (2015–2017) 

WITH holiday_dates AS (
    SELECT '2015' AS year,
           'New Years Day' AS holiday_name,
           '01/01/2015' AS holiday_date
    UNION ALL SELECT '2016', 'New Years Day', '01/01/2016'
    UNION ALL SELECT '2017', 'New Years Day', '01/01/2017'
    UNION ALL SELECT '2015', 'Labor Day', '07/09/2015'
    UNION ALL SELECT '2016', 'Labor Day', '05/09/2016'
    UNION ALL SELECT '2017', 'Labor Day', '04/09/2017'
),
holiday_analysis AS (
    SELECT
        h.year,
        h.holiday_name,
        COUNT(t.date_time) AS recorded_hours,
        ROUND(AVG(
            CASE WHEN t.temp > 0
                 THEN t.temp - 273.15
            END
        ), 2) AS avg_temperature_c,
        ROUND(AVG(t.traffic_volume), 2)
            AS avg_hourly_traffic
    FROM holiday_dates h
    LEFT JOIN metro_traffic_clean t
        ON SUBSTR(t.date_time, 1, 10)
           = h.holiday_date
    GROUP BY h.year, h.holiday_name
)
SELECT
    year,
    holiday_name,
    recorded_hours,
    avg_temperature_c,
    avg_hourly_traffic
FROM holiday_analysis
ORDER BY holiday_name, year;

--Step 7- Analyse Temperature around holidays inlcuding 2018

WITH holiday_dates AS (
    SELECT '2016' AS year,
           'New Years Day' AS holiday_name,
           '01/01/2016' AS holiday_date
    UNION ALL SELECT '2017', 'New Years Day', '01/01/2017'
    UNION ALL SELECT '2018', 'New Years Day', '01/01/2018'
    UNION ALL SELECT '2016', 'Labor Day', '05/09/2016'
    UNION ALL SELECT '2017', 'Labor Day', '04/09/2017'
    UNION ALL SELECT '2018', 'Labor Day', '03/09/2018'
),
holiday_analysis AS (
    SELECT
        h.year,
        h.holiday_name,
        COUNT(t.date_time) AS recorded_hours,
        ROUND(AVG(
            CASE
                WHEN t.temp > 0
                THEN t.temp - 273.15
            END
        ), 2) AS avg_temperature_c,
        ROUND(AVG(t.traffic_volume), 2)
            AS avg_hourly_traffic
    FROM holiday_dates h
    LEFT JOIN metro_traffic_clean t
        ON SUBSTR(t.date_time, 1, 10)
           = h.holiday_date
    GROUP BY h.year, h.holiday_name
)
SELECT
    year,
    holiday_name,
    recorded_hours,
    avg_temperature_c,
    avg_hourly_traffic
FROM holiday_analysis
ORDER BY holiday_name, year;