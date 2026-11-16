from __future__ import annotations

import math

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose


def run_forecast(
    sales: pd.Series,
    horizon: int,
    seasonal_period: int,
) -> dict[str, object]:
    """Evaluate Holt-Winters on a chronological holdout and forecast future demand."""
    minimum_observations = 3 * seasonal_period
    if len(sales) < minimum_observations:
        raise ValueError(
            f"At least {minimum_observations} daily observations are needed for a "
            f"{seasonal_period}-day seasonal model; the dataset has {len(sales)}."
        )
    if horizon < 1:
        raise ValueError("Forecast horizon must be at least one day.")

    test_size = max(seasonal_period, math.ceil(len(sales) * 0.2))
    train_size = len(sales) - test_size
    if train_size < 2 * seasonal_period:
        test_size = len(sales) - 2 * seasonal_period
        train_size = len(sales) - test_size

    train = sales.iloc[:train_size]
    test = sales.iloc[train_size:]

    try:
        evaluation_model = ExponentialSmoothing(
            train,
            trend="add",
            seasonal="add",
            seasonal_periods=seasonal_period,
            initialization_method="estimated",
        ).fit()
        evaluation_predictions = np.maximum(evaluation_model.forecast(len(test)), 0.0)

        final_model = ExponentialSmoothing(
            sales,
            trend="add",
            seasonal="add",
            seasonal_periods=seasonal_period,
            initialization_method="estimated",
        ).fit()
        future_predictions = np.maximum(final_model.forecast(horizon), 0.0)
        decomposition = seasonal_decompose(
            sales,
            model="additive",
            period=seasonal_period,
            extrapolate_trend="freq",
        )
    except (ValueError, ArithmeticError, np.linalg.LinAlgError) as exc:
        raise ValueError(
            f"The Holt-Winters model could not fit this dataset: {exc}"
        ) from exc

    actual = test.to_numpy(dtype=float)
    predicted = np.asarray(evaluation_predictions, dtype=float)
    errors = actual - predicted

    evaluation = pd.DataFrame(
        {
            "Actual": actual,
            "Predicted": predicted,
        },
        index=test.index,
    )
    evaluation.index.name = "Date"

    forecast_dates = pd.date_range(
        sales.index[-1] + pd.Timedelta(days=1),
        periods=horizon,
        freq="D",
    )
    forecast = pd.DataFrame(
        {"Forecast": np.asarray(future_predictions, dtype=float)},
        index=forecast_dates,
    )
    forecast.index.name = "Date"

    components = pd.DataFrame(
        {
            "Trend": decomposition.trend,
            "Seasonal": decomposition.seasonal,
            "Residual": decomposition.resid,
        },
        index=sales.index,
    )
    components.index.name = "Date"

    return {
        "evaluation": evaluation,
        "forecast": forecast,
        "components": components,
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(np.square(errors)))),
        "test_size": len(test),
    }


def add_inventory_projection(
    forecast: pd.DataFrame,
    available_stock: float | None,
) -> tuple[pd.DataFrame, str | None]:
    """Add cumulative demand and optional stock risk to forecast rows."""
    result = forecast.copy()
    result["Cumulative Forecast Demand"] = result["Forecast"].cumsum()

    if available_stock is None:
        result["Projected Stock Remaining"] = np.nan
        result["Inventory Status"] = "Inventory not provided"
        return result, None
    if not np.isfinite(available_stock) or available_stock < 0:
        raise ValueError("Available stock must be a non-negative number.")

    result["Projected Stock Remaining"] = (
        available_stock - result["Cumulative Forecast Demand"]
    )
    total_demand = float(result["Forecast"].sum())
    if total_demand > 0 and available_stock > 1.25 * total_demand:
        overall_status = "Overstock risk"
        result["Inventory Status"] = "Overstock risk"
    else:
        overall_status = (
            "Stockout risk"
            if (result["Projected Stock Remaining"] < 0).any()
            else "Stock covers forecast"
        )
        result["Inventory Status"] = np.where(
            result["Projected Stock Remaining"] < 0,
            "Stockout risk",
            "Stock covers forecast",
        )
    return result, overall_status
