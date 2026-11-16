"""
NUS Capstone - Part 2, Task 4
Mini Traffic Analytics Command-Line Application.

Commands:
    query       - Retrieve traffic and weather by datetime
    peak-hours  - Identify the highest-traffic hours
    compare     - Compare weekday and weekend traffic
    recommend   - Recommend historically lower-traffic hours
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd


logger = logging.getLogger(__name__)

DEFAULT_DATA = "data/processed/traffic_features.csv"
DEFAULT_LOG = "part2_python/logs/cli_app.log"


def configure_logging(log_path):
    """Configure console and file logging at the CLI entry point."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers when configuration is repeated.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False


class LoggingArgumentParser(argparse.ArgumentParser):
    """Log invalid CLI arguments and display a friendly error."""

    def error(self, message):
        logger.error("Invalid CLI arguments: %s", message)
        self.exit(2, f"Error: {message}\n")


def build_parser():
    """Create the CLI argument parser and its four subcommands."""
    parser = LoggingArgumentParser(
        description="Mini Traffic Analytics Application"
    )

    parser.add_argument(
        "--data",
        default=DEFAULT_DATA,
        help="Path to the processed traffic dataset"
    )

    parser.add_argument(
        "--log",
        default=DEFAULT_LOG,
        help="Path to the CLI log file"
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=LoggingArgumentParser
    )

    query_parser = commands.add_parser(
        "query",
        help="Retrieve traffic and weather for a specific datetime"
    )
    query_parser.add_argument(
        "--datetime",
        required=True,
        help="Datetime in YYYY-MM-DD HH:MM format"
    )

    peak_parser = commands.add_parser(
        "peak-hours",
        help="Identify highest-traffic hours"
    )
    peak_parser.add_argument(
        "--day-type",
        choices=["weekday", "weekend"],
        required=True
    )
    peak_parser.add_argument(
        "--top",
        type=int,
        default=3
    )

    commands.add_parser(
        "compare",
        help="Compare average weekday and weekend traffic"
    )

    recommend_parser = commands.add_parser(
        "recommend",
        help="Identify historically lower-traffic travel hours"
    )
    recommend_parser.add_argument(
        "--day-type",
        choices=["weekday", "weekend"],
        required=True
    )
    recommend_parser.add_argument(
        "--top",
        type=int,
        default=3
    )

    return parser


def load_data(path):
    """Load and validate the processed hourly traffic dataset."""
    df = pd.read_csv(path)

    required = {
        "date_time",
        "traffic_volume",
        "weather_main",
        "hour",
        "is_weekend"
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing dataset columns: {sorted(missing)}"
        )

    # Parse datetime only after validating the schema.
    df["date_time"] = pd.to_datetime(
        df["date_time"],
        format="%Y-%m-%d %H:%M:%S",
        errors="raise"
    )

    if df["date_time"].isna().any():
        raise ValueError("Dataset contains invalid timestamps.")

    if df["date_time"].duplicated().any():
        raise ValueError(
            "Dataset contains duplicate hourly timestamps."
        )

    if df["traffic_volume"].isna().any():
        raise ValueError(
            "Dataset contains missing traffic volumes."
        )

    df["traffic_volume"] = pd.to_numeric(
        df["traffic_volume"],
        errors="raise"
    )

    df["hour"] = pd.to_numeric(
        df["hour"],
        errors="raise"
    )

    df["is_weekend"] = pd.to_numeric(
        df["is_weekend"],
        errors="raise"
    )

    if not df["is_weekend"].isin([0, 1]).all():
        raise ValueError(
            "Dataset contains invalid weekend indicators."
        )

    logger.info(
        "Processed dataset loaded successfully: %s rows",
        len(df)
    )

    return df


def query_traffic(df, datetime_text):
    """Retrieve traffic and weather at a specified hourly timestamp."""
    try:
        requested = pd.to_datetime(
            datetime_text,
            format="%Y-%m-%d %H:%M",
            exact=True,
            errors="raise"
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(
            "Invalid date. Use YYYY-MM-DD HH:MM, "
            "for example 2017-06-01 08:00."
        ) from exc

    matches = df.loc[df["date_time"] == requested]

    if matches.empty:
        raise ValueError(
            f"No traffic record found for "
            f"{requested:%Y-%m-%d %H:%M}. "
            "The dataset has historical coverage gaps."
        )

    record = matches.iloc[0]

    return (
        f"Date/time: {requested:%Y-%m-%d %H:%M}\n"
        f"Traffic volume: {record['traffic_volume']:,.0f}\n"
        f"Weather: {record['weather_main']}"
    )


def filter_day_type(df, day_type):
    """Select weekday or weekend observations."""
    weekend_flag = 1 if day_type == "weekend" else 0

    return df.loc[
        df["is_weekend"] == weekend_flag
    ]


def validate_top(top):
    """Ensure that the requested number of hours is valid."""
    if top < 1 or top > 24:
        raise ValueError(
            "--top must be an integer between 1 and 24."
        )


def peak_hours(df, day_type, top):
    """Find the highest average hourly traffic by day type."""
    validate_top(top)

    selected = filter_day_type(df, day_type)

    hourly = (
        selected.groupby("hour")["traffic_volume"]
        .mean()
        .sort_values(ascending=False)
        .head(top)
    )

    if hourly.empty:
        raise ValueError(
            f"No traffic records available for {day_type}."
        )

    lines = [
        f"Top {top} traffic hours ({day_type}):"
    ]

    for hour, volume in hourly.items():
        lines.append(
            f"{int(hour):02d}:00 - {volume:,.2f}"
        )

    return "\n".join(lines)


def compare_days(df):
    """Compare average weekday and weekend traffic."""
    weekday = df.loc[
        df["is_weekend"] == 0,
        "traffic_volume"
    ].mean()

    weekend = df.loc[
        df["is_weekend"] == 1,
        "traffic_volume"
    ].mean()

    if pd.isna(weekday) or pd.isna(weekend):
        raise ValueError(
            "Both weekday and weekend records are required."
        )

    if weekday == 0:
        raise ValueError(
            "Cannot calculate the percentage difference "
            "because average weekday traffic is zero."
        )

    difference = (
        (weekday - weekend) / weekday
    ) * 100

    direction = (
        "lower" if difference >= 0 else "higher"
    )

    return (
        f"Average weekday traffic: {weekday:,.2f}\n"
        f"Average weekend traffic: {weekend:,.2f}\n"
        f"Weekend traffic difference: "
        f"{abs(difference):.2f}% {direction} than weekdays"
    )


def recommend_hours(df, day_type, top):
    """Recommend hours with historically lower traffic."""
    validate_top(top)

    selected = filter_day_type(df, day_type)

    hourly = (
        selected.groupby("hour")["traffic_volume"]
        .mean()
        .sort_values(ascending=True)
        .head(top)
    )

    if hourly.empty:
        raise ValueError(
            f"No traffic records available for {day_type}."
        )

    lines = [
        f"Recommended lower-traffic hours ({day_type}):",
        "Based on historical averages, not live traffic forecasts."
    ]

    for hour, volume in hourly.items():
        lines.append(
            f"{int(hour):02d}:00 - {volume:,.2f}"
        )

    return "\n".join(lines)


def main():
    """Run the requested traffic analytics command."""

    # Configure logging before parsing CLI arguments.
    configure_logging(DEFAULT_LOG)

    parser = build_parser()
    args = parser.parse_args()

    if args.log != DEFAULT_LOG:
        configure_logging(args.log)

    logger.info(
        "Command invoked: %s | Arguments: %s",
        args.command,
        vars(args)
    )

    try:
        df = load_data(args.data)

        if args.command == "query":
            result = query_traffic(
                df,
                args.datetime
            )

        elif args.command == "peak-hours":
            result = peak_hours(
                df,
                args.day_type,
                args.top
            )

        elif args.command == "compare":
            result = compare_days(df)

        elif args.command == "recommend":
            result = recommend_hours(
                df,
                args.day_type,
                args.top
            )

        else:
            raise ValueError(
                f"Unsupported command: {args.command}"
            )

        # Direct output intended for the CLI user.
        print(result)

        logger.info(
            "Command completed successfully: %s",
            args.command
        )

        return 0

    except (
        ValueError,
        FileNotFoundError,
        pd.errors.ParserError,
        UnicodeError,
        OSError
    ) as exc:

        logger.error(
            "Command failed: %s | %s",
            args.command,
            str(exc)
        )

        print(
            f"Error: {exc}",
            file=sys.stderr
        )

        return 1



if __name__ == "__main__":
    sys.exit(main())

