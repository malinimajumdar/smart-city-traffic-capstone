"""
NUS Capstone - Part 2, Task 2
Reproducible Traffic Feature Engineering
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def configure_logging(log_path, debug=False):
    """Configure console and file logging."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(
        logging.DEBUG if debug else logging.INFO
    )
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(
        logging.DEBUG if debug else logging.INFO
    )
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(
        log_path, mode="a", encoding="utf-8"
    )
    file_handler.setLevel(
    logging.DEBUG if debug else logging.INFO
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)


def load_and_validate(input_path):
    """Load cleaned hourly data and validate inputs."""
    df = pd.read_csv(input_path)

    required = [
        "date_time", "traffic_volume",
        "temp_c", "clouds_all",
        "rain_1h", "snow_1h", "weather_main"
    ]

    missing = [c for c in required if c not in df]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    logger.info(
        "Dataset before feature engineering: "
        "%d rows, %d columns", *df.shape
    )

    df["date_time"] = pd.to_datetime(
        df["date_time"], errors="raise"
    )

    if df["date_time"].isna().any():
        raise ValueError("Invalid timestamps")

    if df["date_time"].duplicated().any():
        raise ValueError("Duplicate timestamps")

    for col in [
        "traffic_volume", "temp_c",
        "clouds_all", "rain_1h", "snow_1h"
    ]:
        if not np.isfinite(
            pd.to_numeric(df[col], errors="raise")
            .to_numpy(dtype=float)
        ).all():
            raise ValueError(
                f"Invalid numeric values in {col}"
            )

    logger.info(
        "Input schema and datetime validation passed"
    )
    return df


def engineer_features(df):
    """Create time, weather and numerical features."""
    df = df.copy()

    # Time features
    df["hour"] = df["date_time"].dt.hour
    df["day_of_week"] = df["date_time"].dt.dayofweek
    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype(int)

    logger.info("Time features created")

    # Cyclical time features
    df["hour_sin"] = np.sin(
        2 * np.pi * df["hour"] / 24
    )
    df["hour_cos"] = np.cos(
        2 * np.pi * df["hour"] / 24
    )

    logger.info("Hourly cyclical encoding completed")

    # Weather one-hot encoding
    weather_dummies = pd.get_dummies(
        df["weather_main"].astype(str).str.strip().str.lower(),
        prefix="weather",
        dtype=int
    )

    df = pd.concat([df, weather_dummies], axis=1)

    logger.info(
        "Weather encoding completed: %d binary features",
        weather_dummies.shape[1]
    )

    # Derived weather indicators
    df["is_raining"] = (
        df["rain_1h"] > 0
    ).astype(int)

    df["is_snowing"] = (
        df["snow_1h"] > 0
    ).astype(int)

    weather_lower = (
        df["weather_main"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["is_low_visibility_weather"] = (
        weather_lower.isin([
            "fog", "mist", "haze", "smoke"
        ])
    ).astype(int)

    logger.info("Derived weather indicators created")

    # Numerical scaling
    for col in ["temp_c", "clouds_all"]:
        minimum = df[col].min()
        maximum = df[col].max()

        logger.debug(
            "%s scaling: min=%.4f max=%.4f",
            col, minimum, maximum
        )

        if maximum == minimum:
            raise ValueError(
                f"Cannot scale constant column: {col}"
            )

        df[f"{col}_scaled"] = (
            (df[col] - minimum)
            / (maximum - minimum)
        )

        logger.info("Scaled numerical feature: %s", col)

    # Weekday cyclical encoding
    df["weekday_sin"] = np.sin(
        2 * np.pi * df["day_of_week"] / 7
    )
    df["weekday_cos"] = np.cos(
        2 * np.pi * df["day_of_week"] / 7
    )

    # Severe-weather indicator
    df["is_severe_weather"] = (
        weather_lower.isin([
            "thunderstorm", "snow", "squall"
        ])
    ).astype(int)

    logger.info(
        "Weekday encoding and severe-weather "
        "indicator completed"
    )

    # Quartile-based congestion target
    q1, q2, q3 = df["traffic_volume"].quantile(
        [0.25, 0.50, 0.75]
    ).to_numpy()

    logger.debug(
        "Congestion quartiles: Q1=%.2f, "
        "Q2=%.2f, Q3=%.2f",
        q1, q2, q3
    )

    if not (q1 < q2 < q3):
        raise ValueError("Invalid quartile thresholds")

    df["congestion_category"] = pd.cut(
        df["traffic_volume"],
        bins=[-np.inf, q1, q2, q3, np.inf],
        labels=["Low", "Moderate", "High", "Severe"],
        include_lowest=True
    )

    logger.info("Quartile-based congestion target created")

    return df


def validate_and_save(df, output_path):
    """Validate output and save engineered dataset."""
    required = [
        "hour", "day_of_week", "is_weekend",
        "hour_sin", "hour_cos",
        "weekday_sin", "weekday_cos",
        "is_raining", "is_snowing",
        "is_low_visibility_weather",
        "is_severe_weather",
        "temp_c_scaled", "clouds_all_scaled",
        "congestion_category"
    ]

    if df[required].isna().any().any():
        raise ValueError("Missing engineered values")

    if df["date_time"].duplicated().any():
        raise ValueError("Duplicate hourly timestamps")

    for col in ["temp_c_scaled", "clouds_all_scaled"]:
        if not df[col].between(0, 1).all():
            raise ValueError(f"Invalid scaling: {col}")

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True, exist_ok=True
    )

    df.to_csv(output_path, index=False)

    logger.info(
        "Dataset after feature engineering: "
        "%d rows, %d columns", *df.shape
    )
    logger.info(
        "Feature-engineered dataset saved: %s",
        output_path
    )


def main():
    parser = argparse.ArgumentParser(
        description="NUS traffic feature engineering"
    )
    parser.add_argument(
        "--input",
        default="data/processed/traffic_clean.csv"
    )
    parser.add_argument(
        "--output",
        default="data/processed/traffic_features.csv"
    )
    parser.add_argument(
        "--log",
        default="logs/feature_engineering.log"
    )
    parser.add_argument(
        "--debug", action="store_true"
    )

    args = parser.parse_args()

    try:
        configure_logging(args.log, args.debug)

        df = load_and_validate(args.input)
        result = engineer_features(df)
        validate_and_save(result, args.output)

        logger.info(
            "Feature engineering completed successfully"
        )
        return 0

    except Exception:
        logger.error(
            "Feature engineering failed",
            exc_info=True
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
