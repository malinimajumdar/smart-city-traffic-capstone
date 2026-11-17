# NUS Capstone - Part 2
## Smart City Traffic Analytics: Python Pipeline and CLI

### Project Overview

This project analyses the Metro Interstate Traffic Volume dataset
using a reproducible Python workflow covering data cleaning,
feature engineering, visualisation and a command-line application.

### Dataset and Processing

- Original dataset: 48,204 rows and 9 columns.
- Cleaned dataset: 40,575 rows and 11 columns.
- Feature-engineered dataset: 40,575 rows and 36 columns.
- Duplicate timestamps and invalid sensor readings were addressed.
- Missing or invalid numeric observations were handled using
  appropriate monthly-median imputation.

### Project Structure

```text
capstone_part2/
├── pipeline.py
├── feature_engineering.py
├── visualizations.py
├── cli_app/
│   └── traffic_cli.py
├── data/
│   └── processed/
│       ├── traffic_clean.csv
│       └── traffic_features.csv
├── figures/
│   ├── 01_hourly_traffic_demand.png
│   ├── 02_weekday_vs_weekend.png
│   ├── 03_traffic_by_weather.png
│   └── 04_temperature_vs_traffic.png
├── logs/
│   ├── pipeline.log
│   ├── feature_engineering.log
│   ├── feature_engineering_debug.log
│   ├── visualisation.log
│   └── cli_app.log
├── TASK4_REPORT.md
└── README.md
```

### Python Dependencies

Install the required libraries:

```bash
pip install pandas numpy matplotlib
```

### Running the Project

Run these commands from the repository root.

**Task 1: Data Cleaning**

Place the original Metro Interstate Traffic Volume CSV
in the repository root.

```bash
python pipeline.py --input Metro_Interstate_Traffic_Volume.csv --output data/processed/traffic_clean.csv --log logs/pipeline.log
```

**Task 2: Feature Engineering**

```bash
python feature_engineering.py --input data/processed/traffic_clean.csv --output data/processed/traffic_features.csv --log logs/feature_engineering.log
```

**Task 3: Visualisations**

```bash
python visualizations.py --input data/processed/traffic_features.csv --output-dir figures --log logs/visualisation.log
```

**Task 4: CLI Application**

The application supports four commands:

- `query`: Retrieve traffic and weather for a specified datetime.
- `peak-hours`: Identify peak traffic hours.
- `compare`: Compare weekday and weekend traffic.
- `recommend`: Recommend lower-traffic travel hours.

Example:

```bash
python cli_app/traffic_cli.py query --datetime "2017-06-01 08:00"
python cli_app/traffic_cli.py peak-hours
python cli_app/traffic_cli.py compare
python cli_app/traffic_cli.py recommend
```

### Logging Configuration

All Python modules use `logging.getLogger(__name__)`.

Logging uses console and file handlers configured by the
application entry point.

The logging formatter includes:

- Timestamp
- Log level
- Module name
- Message

**Logging levels**

- DEBUG: Detailed intermediate values used for troubleshooting.
- INFO: Normal execution milestones and successful operations.
- WARNING: Recoverable issues such as dropped rows, imputation,
  outliers or insufficient observations.
- ERROR: Failures preventing successful execution.

**Log files**

- `logs/pipeline.log`: Data loading, validation and cleaning.
- `logs/feature_engineering.log`: Feature creation milestones.
- `logs/feature_engineering_debug.log`: Detailed diagnostic output.
- `logs/visualisation.log`: Figure generation and saved file paths.
- `logs/cli_app.log`: CLI command execution and errors.

Internal status and progress messages are recorded through logging.
The CLI uses print statements only for direct user-facing results
and error messages.

### Key Analytical Findings

**Hourly demand:** Traffic peaks at approximately 16:00
(5,708.61 vehicles/hour) and is lowest at 03:00
(373.21 vehicles/hour).

**Weekday versus weekend:** Mean weekday traffic is 3,557.44,
compared with 2,624.49 on weekends, approximately 26.23% lower.

**Weather:** Mean traffic differs across weather conditions.
These are descriptive associations rather than causal effects.
Very small weather categories require cautious interpretation.

**Temperature:** Pearson correlation between temperature
and traffic volume is approximately 0.1396, indicating
a weak positive linear association.

### Reproducibility and Git Version Control

The project uses Git with separate descriptive commits
for Tasks 1, 2, 3 and 4.

The processing sequence is:

1. Load and clean the raw traffic dataset.
2. Generate engineered temporal and weather features.
3. Produce four Matplotlib visualisations.
4. Run the CLI application against the processed dataset.

Generated logs and figures provide evidence of successful execution.

### Documentation

- `TASK4_REPORT.md`: CLI implementation, testing and findings.
- `README.md`: Project structure, execution and logging guidance.

### Submission Notes

The repository contains the Python scripts, CLI application,
processed datasets, four figures, sample logs and documentation.

The original raw CSV must be supplied separately or placed
in the repository root for full raw-data reproducibility.
