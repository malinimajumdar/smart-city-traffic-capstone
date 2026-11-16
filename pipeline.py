
expected_columns = [
    "holiday",
    "temp",
    "rain_1h",
    "snow_1h",
    "clouds_all",
    "weather_main",
    "weather_description",
    "date_time",
    "traffic_volume"
]


# NUS Capstone - Part 2, Task 1
# Reproducible Data Cleaning and Validation Pipeline

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def load_data(file_path):
    """Load the raw traffic CSV and log the outcome."""

    try:
        df = pd.read_csv(file_path)

        logger.info(
            "Raw CSV loaded successfully: %d rows and %d columns",
            df.shape[0],
            df.shape[1]
        )

        return df

    except (FileNotFoundError, PermissionError,
            pd.errors.ParserError, UnicodeError, OSError) as error:

        logger.error(
            "Failed to load CSV file: %s",
            error,
            exc_info=True
        )

        return None


def validate_schema(df):
    """Check whether all expected columns are present."""

    if df is None:
        logger.error("Schema validation failed: dataset is not loaded")
        return False

    missing_columns = [
        col for col in expected_columns
        if col not in df.columns
    ]

    if missing_columns:
        logger.error(
            "Schema validation failed. Missing columns: %s",
            missing_columns
        )
        return False

    logger.info(
        "Schema validation successful: all %d expected columns are present",
        len(expected_columns)
    )

    return True


def standardise_categories(df):
    """Standardise weather categories and descriptions."""

    df = df.copy()

    for column in ["weather_main", "weather_description"]:

        original = df[column].copy()

        # Remove unnecessary spaces
        df[column] = df[column].astype("string").str.strip()

        # Apply consistent capitalisation
        if column == "weather_main":
            df[column] = df[column].str.title()
        else:
            df[column] = df[column].str.lower()

        # Count modified rows
        changed_rows = (
            original.fillna("<MISSING>") !=
            df[column].fillna("<MISSING>")
        ).sum()

        if changed_rows > 0:
            logger.warning(
                "Standardised %s in %d rows",
                column,
                changed_rows
            )
        else:
            logger.info(
                "Category validation for %s: no changes required",
                column
            )

    return df


def validate_datetime(df):
    """Convert date_time to datetime and handle invalid values."""

    df = df.copy()

    # Convert text to datetime using the correct date format
    df["date_time"] = pd.to_datetime(
        df["date_time"],
        format="%d/%m/%Y %H:%M",
        errors="coerce"
    )

    # Count invalid or missing datetime values
    invalid_dates = df["date_time"].isna().sum()

    if invalid_dates > 0:
        logger.warning(
            "Dropped %d rows due to invalid or missing datetime values",
            invalid_dates
        )

        df = df.dropna(subset=["date_time"])

    else:
        logger.info(
            "Datetime validation successful: 0 invalid records"
        )

    return df


def remove_duplicates(df):
    """Identify and remove exact duplicate rows."""

    df = df.copy()

    # Count exact duplicate rows
    duplicate_count = df.duplicated().sum()

    if duplicate_count > 0:

        # Remove duplicates, keeping the first occurrence
        df = df.drop_duplicates(keep="first").copy()

        logger.warning(
            "Dropped %d rows: exact duplicate records",
            duplicate_count
        )

    else:
        logger.info(
            "Duplicate validation successful: no exact duplicates found"
        )

    logger.info(
        "Dataset after duplicate removal: %d rows and %d columns",
        df.shape[0],
        df.shape[1]
    )

    return df


def identify_invalid_values(df):
    """Identify missing and physically implausible sensor values."""

    if df is None:
        logger.error("Sensor validation failed: dataset unavailable")
        return None

    # Define rules for invalid sensor readings
    invalid_rules = {
        "temp": (df["temp"].isna() | (df["temp"] <= 0)),
        "rain_1h": (df["rain_1h"].isna() |
                    (df["rain_1h"] < 0) |
                    (df["rain_1h"] > 9000)),
        "snow_1h": (df["snow_1h"].isna() |
                    (df["snow_1h"] < 0)),
        "clouds_all": (df["clouds_all"].isna() |
                       (df["clouds_all"] < 0) |
                       (df["clouds_all"] > 100)),
        "traffic_volume": (df["traffic_volume"].isna() |
                           (df["traffic_volume"] < 0) |
                           ((df["traffic_volume"] == 0) &
                            (df["date_time"].dt.hour.isin([18, 23]))))
    }

    for column, invalid_mask in invalid_rules.items():
        invalid_count = int(invalid_mask.sum())

        if invalid_count > 0:
            logger.warning(
                "Detected %d invalid or missing values in %s",
                invalid_count,
                column
            )
        else:
            logger.info(
                "Sensor validation for %s: no invalid values",
                column
            )

    return invalid_rules


def impute_monthly_medians(df, invalid_rules):
    """Replace invalid sensor readings with monthly medians."""

    df = df.copy()

    # Extract calendar month for grouped imputation
    df["_month"] = df["date_time"].dt.month

    for column, invalid_mask in invalid_rules.items():

        invalid_mask = invalid_mask.reindex(df.index, fill_value=False)
        invalid_count = int(invalid_mask.sum())

        if invalid_count == 0:
            logger.info(
                "No imputation required for %s",
                column
            )
            continue

        # Exclude invalid readings from median calculations
        df.loc[invalid_mask, column] = np.nan

        # Process each month separately
        for month in range(1, 13):

            month_mask = df["_month"] == month
            target_mask = month_mask & invalid_mask

            if not target_mask.any():
                continue

            monthly_median = df.loc[
                month_mask, column
            ].median()

            if pd.notna(monthly_median):
                df.loc[target_mask, column] = monthly_median

        # Check for unresolved missing values
        remaining = int(df.loc[invalid_mask, column].isna().sum())

        if remaining > 0:
            raise ValueError(
                f"Unable to impute {remaining} values in {column}"
            )

        logger.warning(
            "Imputed %d invalid/missing %s values using monthly medians",
            invalid_count,
            column
        )

    # Remove temporary processing column
    df = df.drop(columns=["_month"])

    return df


def correct_holiday_flags(df):
    """Extend holiday indicators to all observed hours of each holiday."""

    df = df.copy()

    # Identify valid holiday labels
    holiday_text = df["holiday"].astype("string").str.strip()

    valid_holiday = (
        holiday_text.notna()
        & holiday_text.ne("")
        & holiday_text.str.lower().ne("none").fillna(False)
    )

    # Extract calendar dates
    dates = df["date_time"].dt.normalize()

    # Identify dates containing a holiday label
    holiday_dates = set(dates.loc[valid_holiday])

    # Create the corrected Boolean indicator
    df["is_holiday"] = dates.isin(holiday_dates)

    original_count = int(valid_holiday.sum())
    corrected_count = int(df["is_holiday"].sum())
    modified_count = int((df["is_holiday"] & ~valid_holiday).sum())

    if modified_count > 0:
        logger.warning(
            "Modified %d rows: extended holiday flags across observed hours",
            modified_count
        )
    else:
        logger.info("Holiday flags required no changes")

    logger.info(
        "Holiday validation: %d originally flagged rows; "
        "%d rows flagged after correction",
        original_count,
        corrected_count
    )

    return df


def consolidate_hourly_records(df):
    """Retain one record per hour using weather severity."""

    df = df.copy()

    # Weather severity ranking: higher number = more severe
    severity_order = {
        "Clear": 1,
        "Clouds": 2,
        "Drizzle": 3,
        "Rain": 4,
        "Mist": 5,
        "Haze": 6,
        "Smoke": 7,
        "Fog": 8,
        "Snow": 9,
        "Squall": 10,
        "Thunderstorm": 11
    }

    # Assign weather severity
    df["_severity"] = df["weather_main"].map(severity_order)

    # Warn about unrecognised weather categories
    unknown_count = int(df["_severity"].isna().sum())

    if unknown_count > 0:
        logger.warning(
            "Found %d rows with unrecognised weather categories",
            unknown_count
        )
        raise ValueError("Unrecognised weather categories found")

    original_rows = len(df)

    # Sort by timestamp and descending weather severity
    df = df.sort_values(
        by=["date_time", "_severity"],
        ascending=[True, False],
        kind="stable"
    )

    # Retain the most severe weather report for each hour
    df = df.drop_duplicates(
        subset=["date_time"],
        keep="first"
    ).copy()

    removed_rows = original_rows - len(df)

    if removed_rows > 0:
        logger.warning(
            "Dropped %d repeated weather-report rows: "
            "retained highest-severity weather per timestamp",
            removed_rows
        )
    else:
        logger.info("Hourly consolidation: no repeated timestamps")

    # Remove temporary severity column
    df = df.drop(columns=["_severity"])

    # Restore chronological order
    df = df.sort_values("date_time").reset_index(drop=True)

    logger.info(
        "Hourly consolidation completed: %d rows, %d unique timestamps",
        len(df),
        df["date_time"].nunique()
    )

    return df


def convert_temperature(df):
    """Create Celsius temperature from cleaned Kelvin readings."""

    df = df.copy()

    df["temp_c"] = (df["temp"] - 273.15).round(2)

    logger.info(
        "Temperature conversion completed: "
        "created temp_c for %d records",
        len(df)
    )

    return df


def validate_cleaned_data(df):
    """Validate the cleaned hourly traffic dataset."""

    if df is None or df.empty:
        logger.error("Final validation failed: dataset is empty")
        return False

    # Check for duplicate timestamps
    duplicate_count = int(
        df["date_time"].duplicated().sum()
    )

    # Check missing numeric values
    numeric_columns = [
        "temp", "rain_1h", "snow_1h",
        "clouds_all", "traffic_volume", "temp_c"
    ]

    missing_count = int(
        df[numeric_columns].isna().sum().sum()
    )

    # Check remaining invalid sensor readings
    invalid_count = int(
        (df["temp"] <= 0).sum()
        + (df["rain_1h"] < 0).sum()
        + (df["rain_1h"] > 9000).sum()
        + (df["snow_1h"] < 0).sum()
        + (~df["clouds_all"].between(0, 100)).sum()
        + (df["traffic_volume"] < 0).sum()
    )

    # Check corrected holiday hours
    holiday_hours = int(df["is_holiday"].sum())

    # Log each validation result
    logger.info(
        "Final dataset: %d rows and %d columns",
        df.shape[0], df.shape[1]
    )

    logger.info(
        "Remaining duplicate timestamps: %d",
        duplicate_count
    )

    logger.info(
        "Missing numeric values: %d",
        missing_count
    )

    logger.info(
        "Remaining invalid sensor values: %d",
        invalid_count
    )

    logger.info(
        "Corrected holiday hours: %d",
        holiday_hours
    )

    # Determine whether validation passed
    if duplicate_count > 0 or missing_count > 0 or invalid_count > 0:
        logger.error("Final data quality validation failed")
        return False

    logger.info("Final data quality validation passed")
    return True


def save_cleaned_data(df, output_path):
    """Save the validated dataset to CSV with logging."""

    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_path, index=False)

        logger.info(
            "Cleaned dataset saved successfully: %d rows, %d columns",
            df.shape[0],
            df.shape[1]
        )

        logger.info("Output file: %s", output_path)
        return True

    except Exception:
        logger.exception("Failed to save cleaned dataset")
        return False



def configure_logging(log_path):
    """Configure console and file logging."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = logging.FileHandler(log_path, mode="w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def main():
    parser = argparse.ArgumentParser(
        description="Metro Interstate Traffic Data Cleaning Pipeline"
    )

    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log", default="logs/pipeline.log")

    args = parser.parse_args()
    configure_logging(args.log)

    try:
        logger.info("Pipeline execution started")

        df = load_data(args.input)
        if df is None or not validate_schema(df):
            raise ValueError("Input loading or schema validation failed")

        df = standardise_categories(df)
        df = validate_datetime(df)
        df = remove_duplicates(df)

        invalid_rules = identify_invalid_values(df)
        if invalid_rules is None:
            raise ValueError("Sensor validation failed")

        df = impute_monthly_medians(df, invalid_rules)
        df = correct_holiday_flags(df)
        df = consolidate_hourly_records(df)
        df = convert_temperature(df)

        if not validate_cleaned_data(df):
            raise ValueError("Final data quality validation failed")

        if not save_cleaned_data(df, args.output):
            raise IOError("Failed to save cleaned dataset")

        logger.info("Pipeline completed successfully")

    except Exception:
        logger.exception("Pipeline execution failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
