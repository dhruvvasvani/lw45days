from __future__ import annotations

from io import BytesIO
import re

import numpy as np
import pandas as pd


DATE_COLUMN_ALIASES = {
    "date",
    "day",
    "dteday",
    "datetime",
    "timestamp",
    "ds",
    "orderdate",
    "transactiondate",
    "dateofsale",
}
SALES_COLUMN_ALIASES = {
    "sales",
    "sale",
    "demand",
    "quantity",
    "qty",
    "units",
    "unitssold",
    "revenue",
    "amount",
    "total",
    "cnt",
    "births",
}


def _read_csv(file_bytes: bytes, *, header_only: bool = False) -> pd.DataFrame:
    try:
        return pd.read_csv(
            BytesIO(file_bytes),
            nrows=0 if header_only else None,
        )
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
        OSError,
    ) as exc:
        raise ValueError(f"Could not read the CSV file: {exc}") from exc


def get_sales_csv_columns(file_bytes: bytes) -> list[str]:
    """Return CSV headers so the UI can let users map their own column names."""
    columns = [str(column) for column in _read_csv(file_bytes, header_only=True).columns]
    if not columns:
        raise ValueError("The uploaded CSV needs a header row with column names.")
    return columns


def guess_sales_columns(columns: list[str]) -> tuple[str | None, str | None]:
    """Guess date and demand columns using common names, including bike-share data."""
    normalized = {
        re.sub(r"[^a-z0-9]", "", str(column).casefold()): str(column)
        for column in columns
    }
    date_column = next(
        (normalized[name] for name in DATE_COLUMN_ALIASES if name in normalized),
        None,
    )
    sales_column = next(
        (normalized[name] for name in SALES_COLUMN_ALIASES if name in normalized),
        None,
    )
    return date_column, sales_column


def load_sales_csv(
    file_bytes: bytes,
    date_column: str | None = None,
    sales_column: str | None = None,
) -> tuple[pd.Series, list[str]]:
    """Load selected date and demand columns and normalize them to daily sales."""
    frame = _read_csv(file_bytes)
    if frame.empty:
        raise ValueError("The uploaded CSV does not contain any rows.")

    guessed_date, guessed_sales = guess_sales_columns(
        [str(column) for column in frame.columns]
    )
    date_column = date_column or guessed_date
    sales_column = sales_column or guessed_sales
    if date_column not in frame.columns or sales_column not in frame.columns:
        raise ValueError(
            "Choose the column containing dates and the numeric column to forecast. "
            "For example, `dteday` and `cnt` in the common bike-sharing day.csv."
        )
    if date_column == sales_column:
        raise ValueError("Date and demand must come from two different columns.")

    dates = pd.to_datetime(frame[date_column], errors="coerce")
    sales = pd.to_numeric(frame[sales_column], errors="coerce")
    invalid_dates = int(dates.isna().sum())
    invalid_sales = int(sales.isna().sum())
    if invalid_dates or invalid_sales:
        details = []
        if invalid_dates:
            details.append(f"{invalid_dates} invalid or missing date value(s)")
        if invalid_sales:
            details.append(f"{invalid_sales} invalid or missing sales value(s)")
        raise ValueError("Fix the CSV data and upload it again: " + ", ".join(details) + ".")
    if not np.isfinite(sales.to_numpy(dtype=float)).all():
        raise ValueError("Sales values must be finite numbers.")
    if (sales < 0).any():
        raise ValueError("Sales values cannot be negative.")

    clean = pd.DataFrame(
        {
            "Date": dates.dt.normalize(),
            "Sales": sales.astype(float),
        }
    )
    duplicate_count = int(clean["Date"].duplicated(keep=False).sum())
    clean = clean.groupby("Date", as_index=True)["Sales"].sum().sort_index()
    notes: list[str] = []
    if duplicate_count:
        notes.append(
            "Multiple sales rows on the same date were added together."
        )

    full_dates = pd.date_range(clean.index.min(), clean.index.max(), freq="D")
    missing_days = len(full_dates.difference(clean.index))
    clean = clean.reindex(full_dates, fill_value=0.0)
    clean.index.name = "Date"
    clean.name = "Sales"
    if missing_days:
        notes.append(
            f"{missing_days} calendar date(s) missing from the CSV were filled with "
            "zero sales. Change this assumption if those dates are missing records."
        )

    if not clean.index.is_monotonic_increasing:
        raise ValueError("Dates could not be sorted into chronological order.")
    return clean, notes
