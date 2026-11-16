"""
NUS Capstone - Part 2, Task 3
Reproducible Traffic Pattern Visualisations

Creates four Matplotlib figures and records an INFO
message with the file path after every successful save.
"""

import argparse
import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def configure_logging(log_path):
    """Configure INFO logging to console and file."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(
        log_path, mode="a", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)


def load_and_validate(input_path):
    """Load and validate the engineered dataset."""
    input_path = Path(input_path)

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Input dataset not found: {input_path}"
        )

    df = pd.read_csv(input_path)

    required = [
        "date_time", "hour", "day_of_week",
        "is_weekend", "weather_main",
        "temp_c", "traffic_volume",
        "congestion_category"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df["date_time"] = pd.to_datetime(
        df["date_time"], errors="raise"
    )

    if df["date_time"].isna().any():
        raise ValueError("Missing timestamps detected")

    numeric = [
        "hour", "day_of_week", "is_weekend",
        "temp_c", "traffic_volume"
    ]

    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="raise")

    if not np.isfinite(
        df[numeric].to_numpy(dtype=float)
    ).all():
        raise ValueError("Invalid numeric values detected")

    if df["weather_main"].isna().any():
        raise ValueError("Missing weather categories")

    if df["hour"].lt(0).any() or df["hour"].gt(23).any():
        raise ValueError("Invalid hour values")

    if not df["is_weekend"].isin([0, 1]).all():
        raise ValueError("Invalid weekend indicators")

    logger.info(
        "Dataset loaded and validated: %d rows, %d columns",
        *df.shape
    )

    return df


def save_figure(fig, output_dir, filename):
    """Save a figure and log the successful file path."""
    path = output_dir / filename

    fig.savefig(
        path,
        dpi=300,
        bbox_inches="tight"
    )

    if not path.is_file() or path.stat().st_size == 0:
        raise IOError(f"Figure saving failed: {path}")

    logger.info(
        "Figure successfully saved: %s",
        path.resolve()
    )

    plt.close(fig)
    return path


def plot_hourly_traffic(df, output_dir):
    """Figure 1: Average traffic demand by hour."""
    hourly = (
        df.groupby("hour")["traffic_volume"]
        .mean()
        .reindex(range(24))
    )

    if hourly.isna().any():
        raise ValueError("Missing hourly traffic data")

    peak_hour = int(hourly.idxmax())
    lowest_hour = int(hourly.idxmin())

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        hourly.index, hourly.values,
        marker="o", linewidth=2,
        color="steelblue",
        label="Average hourly traffic"
    )

    ax.scatter(
        peak_hour, hourly.loc[peak_hour],
        color="darkred", s=110,
        zorder=5, label="Peak demand"
    )

    ax.scatter(
        lowest_hour, hourly.loc[lowest_hour],
        color="green", s=110,
        zorder=5, label="Lowest demand"
    )

    ax.set_title(
        "Average Traffic Demand by Hour",
        fontsize=15, fontweight="bold"
    )
    ax.set_xlabel("Hour of Day (0-23)")
    ax.set_ylabel(
        "Average Traffic Volume (vehicles/hour)"
    )
    ax.set_xticks(range(24))
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    logger.info(
        "Hourly traffic: peak=%02d:00, lowest=%02d:00",
        peak_hour, lowest_hour
    )

    return save_figure(
        fig, output_dir,
        "01_hourly_traffic_demand.png"
    )


def plot_weekday_weekend(df, output_dir):
    """Figure 2: Weekday versus weekend traffic."""
    grouped = (
        df.groupby(["hour", "is_weekend"])["traffic_volume"]
        .mean()
        .unstack("is_weekend")
        .reindex(range(24))
    )

    if not {0, 1}.issubset(grouped.columns):
        raise ValueError("Missing weekday or weekend data")

    if grouped[[0, 1]].isna().any().any():
        raise ValueError("Incomplete hourly day-type data")

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        grouped.index, grouped[0],
        marker="o", linewidth=2,
        color="steelblue", label="Weekday"
    )

    ax.plot(
        grouped.index, grouped[1],
        marker="s", linewidth=2,
        color="darkorange", label="Weekend"
    )

    ax.set_title(
        "Weekday vs Weekend Traffic Patterns",
        fontsize=15, fontweight="bold"
    )
    ax.set_xlabel("Hour of Day (0-23)")
    ax.set_ylabel(
        "Average Traffic Volume (vehicles/hour)"
    )
    ax.set_xticks(range(24))
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    averages = (
        df.groupby("is_weekend")["traffic_volume"].mean()
    )

    logger.info(
        "Average traffic: weekday=%.2f, weekend=%.2f",
        averages.loc[0], averages.loc[1]
    )

    return save_figure(
        fig, output_dir,
        "02_weekday_vs_weekend.png"
    )


def plot_weather_traffic(df, output_dir):
    """Figure 3: Average traffic by weather condition."""
    weather = (
        df.groupby("weather_main")["traffic_volume"]
        .agg(["mean", "count"])
        .sort_values("mean", ascending=False)
    )

    if weather.empty or weather["mean"].isna().any():
        raise ValueError("Invalid weather summary")

    fig, ax = plt.subplots(figsize=(12, 7))

    bars = ax.barh(
        weather.index, weather["mean"],
        color="steelblue",
        edgecolor="black", alpha=0.85
    )

    ax.invert_yaxis()
    ax.set_title(
        "Average Traffic Volume by Weather Condition",
        fontsize=15, fontweight="bold"
    )
    ax.set_xlabel(
        "Average Traffic Volume (vehicles/hour)"
    )
    ax.set_ylabel("Weather Condition")
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    ax.bar_label(
        bars,
        labels=[f"{v:,.0f}" for v in weather["mean"]],
        padding=4, fontsize=9
    )

    ax.set_xlim(0, weather["mean"].max() * 1.18)
    fig.tight_layout()

    rare = weather[weather["count"] < 30]

    if not rare.empty:
        logger.warning(
            "Weather categories with fewer than 30 "
            "observations: %s",
            rare["count"].to_dict()
        )

    return save_figure(
        fig, output_dir,
        "03_traffic_by_weather.png"
    )


def plot_temperature_traffic(df, output_dir):
    """Figure 4: Temperature versus traffic volume."""
    data = df[["temp_c", "traffic_volume"]].dropna()

    if len(data) < 2:
        raise ValueError("Insufficient observations")

    x = data["temp_c"].to_numpy(dtype=float)
    y = data["traffic_volume"].to_numpy(dtype=float)

    if np.std(x) == 0 or np.std(y) == 0:
        raise ValueError("Insufficient numeric variation")

    correlation = np.corrcoef(x, y)[0, 1]
    slope, intercept = np.polyfit(x, y, 1)

    x_line = np.linspace(x.min(), x.max(), 200)
    y_line = slope * x_line + intercept

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.scatter(
        x, y, alpha=0.12, s=9,
        color="steelblue",
        label="Hourly observations"
    )

    ax.plot(
        x_line, y_line,
        color="darkred",
        linewidth=2.5,
        label="Linear trend"
    )

    ax.set_title(
        "Temperature vs Traffic Volume",
        fontsize=15, fontweight="bold"
    )
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel(
        "Traffic Volume (vehicles/hour)"
    )
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax.text(
        0.02, 0.96,
        f"Pearson correlation (r) = {correlation:.3f}",
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=dict(
            facecolor="white",
            edgecolor="gray",
            alpha=0.9
        )
    )

    fig.tight_layout()

    logger.info(
        "Temperature-traffic Pearson correlation: %.4f",
        correlation
    )

    return save_figure(
        fig, output_dir,
        "04_temperature_vs_traffic.png"
    )


def main():
    parser = argparse.ArgumentParser(
        description="NUS traffic visualisation pipeline"
    )

    parser.add_argument(
        "--input",
        default="data/processed/traffic_features.csv"
    )

    parser.add_argument(
        "--output-dir",
        default="part2_python/figures"
    )

    parser.add_argument(
        "--log",
        default="part2_python/logs/visualisation.log"
    )

    args = parser.parse_args()

    try:
        configure_logging(args.log)

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        df = load_and_validate(args.input)

        figures = [
            plot_hourly_traffic(df, output_dir),
            plot_weekday_weekend(df, output_dir),
            plot_weather_traffic(df, output_dir),
            plot_temperature_traffic(df, output_dir)
        ]

        if len(figures) != 4:
            raise RuntimeError("Incomplete figure generation")

        logger.info(
            "Task 3 completed: %d figures generated",
            len(figures)
        )

        return 0

    except Exception:
        logger.exception("Task 3 visualisation failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
