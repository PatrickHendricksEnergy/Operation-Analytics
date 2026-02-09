"""Visualization helpers for inventory analysis dataset."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter, PercentFormatter

from shared.src.common_etl import ensure_dir, set_matplotlib_cache_dir


def _setup():
    set_matplotlib_cache_dir()
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [
        "Inter",
        "SF Pro Display",
        "SF Pro Text",
        "Helvetica Neue",
        "Helvetica",
        "Arial",
        "sans-serif",
    ]


def _save(fig, path: Path):
    ensure_dir(path.parent)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _space_thousands(x, pos):
    try:
        if x is None:
            return ""
        if abs(x) >= 1000:
            return f"{x:,.2f}".replace(",", " ")
        if abs(x) >= 1:
            return f"{x:.2f}".rstrip("0").rstrip(".")
        return f"{x:.3f}".rstrip("0").rstrip(".")
    except Exception:
        return str(x)


def _scale_info(values):
    try:
        arr = np.array(values, dtype="float64")
        max_val = np.nanmax(np.abs(arr)) if arr.size else 0
    except Exception:
        max_val = 0
    if max_val >= 1e9:
        return 1e9, "billions"
    if max_val >= 1e6:
        return 1e6, "millions"
    if max_val >= 1e3:
        return 1e3, "thousands"
    return 1.0, ""


def _make_scaled_formatter(scale):
    def _fmt(x, pos):
        try:
            return _space_thousands(x / scale, pos)
        except Exception:
            return str(x)
    return FuncFormatter(_fmt)


def _apply_scaled_axis(ax, axis, label, values, currency=False):
    scale, suffix = _scale_info(values)
    formatter = _make_scaled_formatter(scale)
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)
        if suffix:
            unit = f"{suffix} USD" if currency else suffix
            ax.set_xlabel(f"{label} (in {unit})")
        else:
            unit = "USD" if currency else ""
            ax.set_xlabel(f"{label} ({unit})" if unit else label)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
        if suffix:
            unit = f"{suffix} USD" if currency else suffix
            ax.set_ylabel(f"{label} (in {unit})")
        else:
            unit = "USD" if currency else ""
            ax.set_ylabel(f"{label} ({unit})" if unit else label)


def pareto_supplier_spend(vendor_spend: pd.DataFrame, path: Path) -> None:
    if vendor_spend.empty or "purchase_dollars" not in vendor_spend.columns:
        return
    _setup()
    df = vendor_spend.sort_values("purchase_dollars", ascending=False)
    df["cum_pct"] = df["purchase_dollars"].cumsum() / df["purchase_dollars"].sum()

    fig, ax1 = plt.subplots(figsize=(12, 6))
    sns.barplot(data=df.head(15), x="vendor_name", y="purchase_dollars", ax=ax1, color="#4C72B0")
    ax1.tick_params(axis="x", rotation=30)
    ax1.set_title("Pareto: Purchase Spend by Supplier")
    ax1.set_xlabel("Supplier")
    _apply_scaled_axis(ax1, "y", "Purchase Spend", df.head(15)["purchase_dollars"], currency=True)

    ax2 = ax1.twinx()
    ax2.plot(df.head(15)["vendor_name"], df.head(15)["cum_pct"], color="#DD8452", marker="o")
    ax2.set_ylabel("Cumulative %")
    ax2.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax2.set_ylim(0, 1.05)
    _save(fig, path)


def abc_distribution(abc_df: pd.DataFrame, path: Path) -> None:
    if abc_df.empty or "abc_class" not in abc_df.columns:
        return
    _setup()
    counts = abc_df["abc_class"].value_counts().reset_index()
    counts.columns = ["abc_class", "count"]

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(data=counts, x="abc_class", y="count", ax=ax, color="#55A868")
    ax.set_title("ABC Classification (Item Count)")
    ax.set_xlabel("ABC Class")
    _apply_scaled_axis(ax, "y", "Count", counts["count"])
    _save(fig, path)


def monthly_sales_trend(monthly_df: pd.DataFrame, path: Path) -> None:
    if monthly_df.empty or "sales_month" not in monthly_df.columns:
        return
    _setup()
    df = monthly_df.copy()
    df["sales_month"] = pd.to_datetime(df["sales_month"], errors="coerce")
    df = df.sort_values("sales_month")

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=df, x="sales_month", y="sales_dollars", ax=ax, marker="o")
    ax.set_title("Monthly Sales Trend")
    ax.set_xlabel("Month")
    _apply_scaled_axis(ax, "y", "Sales", df["sales_dollars"], currency=True)
    _save(fig, path)


def lead_time_distribution(summary: pd.DataFrame, path: Path) -> None:
    if summary.empty or "avg_lead_time_days" not in summary.columns:
        return
    _setup()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(summary["avg_lead_time_days"].dropna(), bins=20, ax=ax)
    ax.set_title("Average Lead Time Distribution")
    ax.set_xlabel("Lead Time (Days)")
    ax.set_ylabel("Count")
    _apply_scaled_axis(ax, "x", "Lead Time (Days)", summary["avg_lead_time_days"])
    _apply_scaled_axis(ax, "y", "Count", ax.get_yticks())
    _save(fig, path)


def inventory_turnover_top(summary: pd.DataFrame, path: Path) -> None:
    if summary.empty or "inventory_turnover" not in summary.columns:
        return
    _setup()
    top = summary.sort_values("inventory_turnover", ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=top, x="inventory_id", y="inventory_turnover", ax=ax, color="#C44E52")
    ax.set_title("Inventory Turnover (Top 15 Items)")
    ax.set_xlabel("Inventory ID")
    ax.set_ylabel("Turnover")
    ax.tick_params(axis="x", rotation=30)
    _save(fig, path)


def build_figures(summary: pd.DataFrame, monthly_df: pd.DataFrame, abc_df: pd.DataFrame, vendor_spend: pd.DataFrame, reports_dir: str | Path) -> list[str]:
    reports_dir = Path(reports_dir)
    fig_dir = reports_dir / "figures"
    ensure_dir(fig_dir)

    outputs = []
    paths = {
        "pareto_supplier": fig_dir / "pareto_supplier_spend.png",
        "abc_distribution": fig_dir / "abc_distribution.png",
        "monthly_sales": fig_dir / "monthly_sales_trend.png",
        "lead_time": fig_dir / "lead_time_distribution.png",
        "turnover_top": fig_dir / "inventory_turnover_top.png",
    }

    pareto_supplier_spend(vendor_spend, paths["pareto_supplier"])
    abc_distribution(abc_df, paths["abc_distribution"])
    monthly_sales_trend(monthly_df, paths["monthly_sales"])
    lead_time_distribution(summary, paths["lead_time"])
    inventory_turnover_top(summary, paths["turnover_top"])

    for p in paths.values():
        if p.exists():
            outputs.append(str(p))

    return outputs
