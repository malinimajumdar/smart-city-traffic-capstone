# NUS Capstone - Part 2
## Methodology and Findings Report

### 1. Project Objective

This project develops a reproducible Python-based traffic
analytics pipeline using the Metro Interstate Traffic Volume
dataset. It integrates data cleaning, feature engineering,
visualisation and a command-line application to analyse
traffic patterns and support travel-time decisions.

### 2. Data Cleaning and Validation

The original dataset contained 48,204 observations and
9 columns. A structured cleaning pipeline validated the
schema, standardised categorical values, parsed timestamps,
removed duplicates and addressed invalid sensor readings.

Monthly-median imputation was applied where appropriate.
Repeated hourly weather observations were consolidated
to obtain one record per timestamp.

The final cleaned dataset contains 40,575 rows and
11 columns, with unique hourly timestamps and no
remaining missing numeric values or invalid sensor values.

### 3. Feature Engineering

The feature-engineering module expanded the cleaned
dataset from 11 to 36 columns.

Features included:
- Hour, day of week and weekend indicators.
- Cyclical time encodings.
- One-hot encoded weather conditions.
- Rain, snow and visibility indicators.
- Normalised temperature and cloud coverage.
- Relative congestion categories based on traffic quartiles.

The traffic-volume quartile thresholds were:
Q1 = 1,249, Q2 = 3,427 and Q3 = 4,952.

These categories represent relative traffic demand,
not independently measured road-capacity congestion.

### 4. Visualisation Findings

Four Matplotlib figures were generated and saved.

**Hourly traffic demand:** Average traffic peaked
at 16:00 with approximately 5,708.61 vehicles/hour,
compared with 373.21 vehicles/hour at 03:00.
This indicates pronounced daily demand variation.

**Weekday versus weekend:** Average weekday traffic
was 3,557.44 vehicles/hour, compared with 2,624.49
on weekends, approximately 26.23% lower.
Weekdays showed stronger commuting peaks.

**Traffic by weather:** Mean traffic differed across
weather categories. However, weather groups with
very small observation counts require cautious
interpretation. The analysis does not establish causality.

**Temperature versus traffic:** Pearson correlation
was approximately 0.1396, indicating a weak positive
linear association. Temperature alone explains little
of the variation in traffic demand.

### 5. Command-Line Application

A Python CLI was developed using argparse with
four commands:

1. query: Retrieve traffic volume and weather
   for a specified datetime.
2. peak-hours: Identify high-demand traffic hours.
3. compare: Compare weekday and weekend traffic.
4. recommend: Identify relatively lower-traffic
   hours to support travel planning.

The CLI was tested for successful execution and
invalid inputs, including missing files, missing
timestamps, invalid commands and missing arguments.

All four robustness tests passed.

### 6. Logging and Reproducibility

Each module uses logging.getLogger(__name__).

Logs record execution timestamps, severity levels,
module names and descriptive messages.

DEBUG captures detailed diagnostic values.
INFO records successful processing milestones.
WARNING identifies recoverable data-quality issues.
ERROR records execution failures.

Log files are retained as evidence of execution.
The CLI prints only direct user-facing results
and errors, rather than internal progress messages.

The Git repository contains separate descriptive
commits for Tasks 1 through 4, supporting
incremental development and traceability.

### 7. Conclusion

The project successfully combines data preparation,
feature engineering, visual analytics and an
interactive CLI into a reproducible workflow.

Results indicate strong hourly and weekday demand
patterns, while weather and temperature associations
require careful interpretation.

The completed solution provides a foundation for
subsequent predictive modelling and smart-city
traffic decision support.
