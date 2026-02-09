"""Visualization helpers for supply chain analysis dataset."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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


def pareto_revenue_by_supplier(df: pd.DataFrame, path: Path) -> None:
    _setup()
    if "supplier_name" not in df.columns or "revenue_generated" not in df.columns:
        return
    agg = (
        df.groupby("supplier_name", dropna=False)["revenue_generated"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    agg["cum_pct"] = agg["revenue_generated"].cumsum() / agg["revenue_generated"].sum()

    fig, ax1 = plt.subplots(figsize=(12, 6))
    sns.barplot(data=agg, x="supplier_name", y="revenue_generated", ax=ax1, color="#4C72B0")
    ax1.tick_params(axis="x", rotation=30)
    ax1.set_title("Pareto: Revenue by Supplier")
    ax1.set_xlabel("Supplier")
    ax1.set_ylabel("Revenue (USD)")

    ax2 = ax1.twinx()
    ax2.plot(agg["supplier_name"], agg["cum_pct"], color="#DD8452", marker="o")
    ax2.set_ylabel("Cumulative %")
    ax2.set_ylim(0, 1.05)

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def cost_to_serve_by_carrier_route(df: pd.DataFrame, path: Path) -> None:
    _setup()
    required = {"shipping_carriers", "routes", "total_logistics_cost", "number_of_products_sold"}
    if not required.issubset(df.columns):
        return

    df = df.copy()
    df["logistics_cost_per_unit"] = df["total_logistics_cost"] / df["number_of_products_sold"].replace(0, 1)
    agg = (
        df.groupby(["shipping_carriers", "routes"], dropna=False)["logistics_cost_per_unit"]
        .mean()
        .sort_values(ascending=False)
        .head(12)
        .reset_index()
    )
    agg["carrier_route"] = agg["shipping_carriers"].astype(str) + " | " + agg["routes"].astype(str)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=agg, x="carrier_route", y="logistics_cost_per_unit", ax=ax, color="#55A868")
    ax.set_title("Cost-to-Serve by Carrier/Route (Top 12)")
    ax.set_xlabel("Carrier | Route")
    ax.set_ylabel("Logistics Cost per Unit (USD)")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def lead_time_breakdown_by_supplier(df: pd.DataFrame, path: Path) -> None:
    _setup()
    required = {"supplier_name", "shipping_times", "manufacturing_lead_time"}
    if not required.issubset(df.columns):
        return

    agg = (
        df.groupby("supplier_name", dropna=False)[["shipping_times", "manufacturing_lead_time"]]
        .mean()
        .sort_values("shipping_times", ascending=False)
        .head(10)
        .reset_index()
    )
    melt = agg.melt(id_vars="supplier_name", var_name="lead_stage", value_name="days")

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=melt, x="supplier_name", y="days", hue="lead_stage", ax=ax)
    ax.set_title("Lead Time Breakdown by Supplier (Top 10)")
    ax.set_xlabel("Supplier")
    ax.set_ylabel("Days")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def defect_rate_heatmap(df: pd.DataFrame, path: Path) -> None:
    _setup()
    if "supplier_name" not in df.columns or "location" not in df.columns or "defect_rate_scaled" not in df.columns:
        return

    top_suppliers = df["supplier_name"].value_counts().head(10).index
    top_locations = df["location"].value_counts().head(10).index
    subset = df[df["supplier_name"].isin(top_suppliers) & df["location"].isin(top_locations)]

    if subset.empty:
        return

    pivot = subset.pivot_table(
        index="supplier_name",
        columns="location",
        values="defect_rate_scaled",
        aggfunc="mean",
    )
    if pivot.shape[0] < 2 or pivot.shape[1] < 2:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot, annot=False, cmap="Reds", ax=ax)
    ax.set_title("Defect Rate Heatmap (Supplier x Location)")
    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def margin_proxy_distribution(df: pd.DataFrame, path: Path) -> None:
    _setup()
    if "unit_margin_proxy" not in df.columns or "product_type" not in df.columns:
        return

    top_products = df["product_type"].value_counts().head(8).index
    subset = df[df["product_type"].isin(top_products)]

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=subset, x="product_type", y="unit_margin_proxy", ax=ax)
    ax.set_title("Unit Margin Proxy by Product Type")
    ax.set_xlabel("Product Type")
    ax.set_ylabel("Unit Margin Proxy (USD)")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def build_figures(df: pd.DataFrame, reports_dir: str | Path) -> list[str]:
    reports_dir = Path(reports_dir)
    fig_dir = reports_dir / "figures"
    ensure_dir(fig_dir)

    outputs = []
    paths = {
        "pareto_revenue_by_supplier": fig_dir / "pareto_revenue_by_supplier.png",
        "cost_to_serve_by_carrier_route": fig_dir / "cost_to_serve_by_carrier_route.png",
        "lead_time_breakdown_by_supplier": fig_dir / "lead_time_breakdown_by_supplier.png",
        "defect_rate_heatmap": fig_dir / "defect_rate_heatmap.png",
        "margin_proxy_distribution": fig_dir / "margin_proxy_distribution.png",
    }

    pareto_revenue_by_supplier(df, paths["pareto_revenue_by_supplier"])
    cost_to_serve_by_carrier_route(df, paths["cost_to_serve_by_carrier_route"])
    lead_time_breakdown_by_supplier(df, paths["lead_time_breakdown_by_supplier"])
    defect_rate_heatmap(df, paths["defect_rate_heatmap"])
    margin_proxy_distribution(df, paths["margin_proxy_distribution"])

    for p in paths.values():
        if p.exists():
            outputs.append(str(p))

    return outputs
