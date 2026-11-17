# NUS Capstone - Part 2, Task 4
## Mini Traffic Analytics CLI Application

### Objective
Develop a command-line application using Python argparse
to retrieve and analyse historical traffic information.

### Dataset
- Source: Metro Interstate Traffic Volume
- Processed dataset: data/processed/traffic_features.csv
- Records: 40,575 hourly observations
- Columns: 36
- Processing: Tasks 1 and 2

### Four CLI Commands

1. query
   Retrieve traffic volume and weather for a specified datetime.

2. peak-hours
   Identify the highest average traffic hours for weekdays
   or weekends.

3. compare
   Compare average weekday and weekend traffic volumes.

4. recommend
   Identify historically lower-traffic hours for weekdays
   or weekends. Recommendations are not live forecasts.

### Example Commands

Run from the repository root:

```bash
python part2_python/cli_app/traffic_cli.py query --datetime "2017-06-01 08:00"

python part2_python/cli_app/traffic_cli.py peak-hours --day-type weekday --top 3

python part2_python/cli_app/traffic_cli.py compare

python part2_python/cli_app/traffic_cli.py recommend --day-type weekend --top 3
```

### Error Handling
The application validates required arguments, input files,
dataset columns, timestamps, and requested hour counts.

Invalid dates, missing datasets, and nonexistent timestamps
produce friendly error messages and nonzero exit codes.

No raw traceback is presented for these handled errors.

### Logging
Log location: part2_python/logs/cli_app.log

Logging levels:
- INFO: command invocation, arguments, successful data loading,
  and successful command completion.
- ERROR: invalid CLI arguments, invalid dates, missing files,
  nonexistent timestamps, and other handled failures.
- DEBUG: detailed diagnostics where enabled; not required
  for normal CLI operation.
- WARNING: nonfatal issues requiring attention, if applicable.

The application uses logging.getLogger(__name__).
Logging includes timestamp, level, module and message.
Both console and file handlers are configured.

Status information is logged rather than printed.
print() is reserved for user-facing results and errors.

### Verification Results

Step 13C: Query command verified.
Step 13D: Peak-hours command verified.
Step 13E: Weekday/weekend comparison verified.
Step 13F: Recommendation command verified.
Step 13G: Invalid-date error handling verified.
Step 13H: CLI logging verified.
Step 13I: Final CLI code quality verified.
Step 13K: Four robustness tests passed (4/4).

### Robustness Tests
- Missing input dataset: PASSED
- Nonexistent timestamp: PASSED
- Invalid CLI command: PASSED
- Missing required datetime: PASSED

### Key Historical Findings
- Average weekday traffic: 3,557.44
- Average weekend traffic: 2,624.49
- Weekend traffic is approximately 26.23% lower.
- Peak weekday hour: 16:00.
- Peak weekend hour: 13:00.

### Limitations
The dataset contains historical coverage gaps.
Results are historical averages, not real-time predictions.
A nonexistent timestamp is treated as an unsuccessful query.

### Deliverables
- cli_app/traffic_cli.py
- logs/cli_app.log
- TASK4_REPORT.md
- README.md
