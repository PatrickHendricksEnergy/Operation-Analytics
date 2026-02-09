"""Demand forecasting for inventory analysis dataset."""
from __future__ import annotations

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def forecast_monthly_sales(monthly_df: pd.DataFrame, periods: int = 3) -> pd.DataFrame:
    if monthly_df.empty or "sales_month" not in monthly_df.columns or "sales_dollars" not in monthly_df.columns:
        return pd.DataFrame()

    df = monthly_df.copy()
    df["sales_month"] = pd.to_datetime(df["sales_month"], errors="coerce")
    df = df.sort_values("sales_month")
    series = df.set_index("sales_month")["sales_dollars"].asfreq("MS")

    try:
        model = ExponentialSmoothing(series, trend="add", seasonal=None)
        fit = model.fit()
        forecast = fit.forecast(periods)
    except Exception:
        return pd.DataFrame()

    out = pd.DataFrame({
        "month": forecast.index,
        "y_pred": forecast.values,
        "model_name": "ets",
    })
    return out
