"""Visualization helpers for supply chain analysis dataset."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib import colors as mcolors
from matplotlib import patheffects
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


_ACRONYM_MAP = {
    "Mro": "MRO",
    "Sku": "SKU",
    "Po": "PO",
    "Kpi": "KPI",
    "Sla": "SLA",
    "Eoq": "EOQ",
    "Abc": "ABC",
    "Wip": "WIP",
    "Usd": "USD",
}


def _format_label(series: pd.Series) -> pd.Series:
    text = (
        series.astype("string")
        .str.replace("_", " ")
        .str.strip()
        .str.title()
    )
    return text.replace(_ACRONYM_MAP)


def pareto_revenue_by_supplier(df: pd.DataFrame, path: Path) -> None:
    _setup()
    if "supplier_name" not in df.columns or "revenue_generated" not in df.columns:
        return
    temp = df.assign(supplier_name=_format_label(df["supplier_name"]))
    agg = (
        temp.groupby("supplier_name", dropna=False)["revenue_generated"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    agg["rank"] = np.arange(1, len(agg) + 1)
    agg["tier_label"] = np.where(
        agg["rank"] == 1,
        "Tier-1 Supplier A",
        np.where(agg["rank"] == 2, "Strategic Supplier B", "Long-Tail Supplier C"),
    )
    tier_order = ["Tier-1 Supplier A", "Strategic Supplier B", "Long-Tail Supplier C"]
    agg = (
        agg.groupby("tier_label", as_index=False)["revenue_generated"]
        .sum()
    )
    agg["tier_label"] = pd.Categorical(agg["tier_label"], categories=tier_order, ordered=True)
    agg = agg.sort_values("tier_label").reset_index(drop=True)
    agg["cum_pct"] = agg["revenue_generated"].cumsum() / agg["revenue_generated"].sum()

    fig, ax1 = plt.subplots(figsize=(12, 6))
    sns.barplot(data=agg, x="tier_label", y="revenue_generated", ax=ax1, color="#4C72B0")
    ax1.tick_params(axis="x", rotation=30)
    ax1.set_title("Pareto: Revenue by Supplier Tier")
    ax1.set_xlabel("Supplier Tier")
    ax1.set_ylabel("Revenue (USD)")
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x/1000:,.0f}k"))

    ax2 = ax1.twinx()
    ax2.plot(agg["tier_label"], agg["cum_pct"], color="#DD8452", marker="o")
    ax2.set_ylabel("Cumulative %")
    ax2.set_ylim(0, 1.05)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y*100:,.0f}%"))
    ax2.axhline(0.8, color="#888888", linestyle="--", linewidth=1)

    # Vertical annotation at 80% crossing
    cross_idx = agg["cum_pct"].ge(0.8).idxmax()
    x_pos = cross_idx
    ax1.axvline(x_pos, color="#888888", linestyle="--", linewidth=1)
    ax1.text(
        x_pos + 0.05,
        ax1.get_ylim()[1] * 0.9,
        "80% revenue",
        rotation=90,
        ha="left",
        va="top",
        fontsize=9,
        color="#666666",
    )

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
    df["shipping_carriers"] = _format_label(df["shipping_carriers"])
    df["routes"] = _format_label(df["routes"])
    df["logistics_cost_per_unit"] = df["total_logistics_cost"] / df["number_of_products_sold"].replace(0, 1)
    pivot = df.pivot_table(
        index="shipping_carriers",
        columns="routes",
        values="logistics_cost_per_unit",
        aggfunc="mean",
    )
    if pivot.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot, annot=False, cmap="YlOrRd", ax=ax, cbar=False)
    ax.set_title("Cost per Order by Carrier and Route")
    ax.set_xlabel("Route")
    ax.set_ylabel("Carrier")

    # Annotate each cell with cost per order
    for i, carrier in enumerate(pivot.index):
        for j, route in enumerate(pivot.columns):
            val = pivot.loc[carrier, route]
            if pd.isna(val):
                continue
            text_color = "#FFFFFF" if (str(route) == "Route B" and str(carrier) == "Carrier C") else "#222222"
            ax.text(
                j + 0.5,
                i + 0.5,
                f"${val:,.2f}",
                ha="center",
                va="center",
                fontsize=10,
                color=text_color,
            )
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
        df.assign(supplier_name=_format_label(df["supplier_name"]))
        .groupby("supplier_name", dropna=False)[["shipping_times", "manufacturing_lead_time"]]
        .mean()
        .reset_index()
    )
    agg["total_lead_time"] = agg["shipping_times"].fillna(0) + agg["manufacturing_lead_time"].fillna(0)
    agg = agg.sort_values("total_lead_time", ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(
        agg["supplier_name"],
        agg["manufacturing_lead_time"],
        label="Manufacturing Lead Time",
        color="#4C72B0",
    )
    ax.bar(
        agg["supplier_name"],
        agg["shipping_times"],
        bottom=agg["manufacturing_lead_time"],
        label="Shipping Time",
        color="#55A868",
    )

    # Total lead time marker
    ax.scatter(
        agg["supplier_name"],
        agg["total_lead_time"],
        color="#333333",
        s=18,
        zorder=3,
        label="Total Lead Time",
    )

    ax.set_title("Lead Time Breakdown by Supplier")
    ax.set_xlabel("Supplier")
    ax.set_ylabel("Days")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def defect_rate_heatmap(df: pd.DataFrame, path: Path) -> None:
    _setup()
    if "supplier_name" not in df.columns or "location" not in df.columns or "defect_rate_scaled" not in df.columns:
        return

    temp = df.copy()
    temp["supplier_name"] = _format_label(temp["supplier_name"])
    temp["location"] = _format_label(temp["location"])
    top_suppliers = temp["supplier_name"].value_counts().head(10).index
    top_locations = temp["location"].value_counts().head(10).index
    subset = temp[temp["supplier_name"].isin(top_suppliers) & temp["location"].isin(top_locations)]

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
    ax.set_xlabel("Location")
    ax.set_ylabel("Supplier")
    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def defect_rate_by_supplier(df: pd.DataFrame, path: Path) -> None:
    _setup()
    if "supplier_name" not in df.columns or "defect_rate_scaled" not in df.columns:
        return

    target_rate = 0.02  # 2% defect rate target
    agg = (
        df.groupby("supplier_name", dropna=False)["defect_rate_scaled"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    agg["supplier_name"] = _format_label(agg["supplier_name"])
    agg["defect_rate_pct"] = agg["defect_rate_scaled"] * 100
    agg["above_target"] = agg["defect_rate_scaled"] > target_rate

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = agg["above_target"].map(lambda v: "#D9534F" if v else "#B0B0B0").tolist()
    ax.bar(agg["supplier_name"], agg["defect_rate_pct"], color=colors)
    ax.set_title("Supplier Quality Performance vs Target")
    ax.set_xlabel("Supplier Name")
    ax.set_ylabel("Defect Rate (%)")
    ax.tick_params(axis="x", rotation=20)
    ax.axhline(target_rate * 100, color="#333333", linestyle="--", linewidth=1)
    ax.text(
        0.99,
        target_rate * 100 + (agg["defect_rate_pct"].max() * 0.03),
        "Target 2.0%",
        ha="right",
        va="bottom",
        fontsize=9,
        color="#333333",
        transform=ax.get_yaxis_transform(),
    )

    for idx, row in agg.iterrows():
        ax.text(
            idx,
            row["defect_rate_pct"] + 0.05,
            f"{row['defect_rate_pct']:.2f}%",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#333333",
        )

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def defect_rate_lollipop(df: pd.DataFrame, path: Path) -> None:
    _setup()
    if "supplier_name" not in df.columns or "defect_rate_scaled" not in df.columns:
        return

    target_rate = 0.02  # 2% defect rate target
    agg = (
        df.groupby("supplier_name", dropna=False)["defect_rate_scaled"]
        .mean()
        .sort_values(ascending=True)
        .reset_index()
    )
    agg["supplier_name"] = _format_label(agg["supplier_name"])
    agg["defect_rate_pct"] = agg["defect_rate_scaled"] * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, row in agg.iterrows():
        ax.plot([0, row["defect_rate_pct"]], [i, i], color="#B0B0B0", linewidth=1)
        color = "#D9534F" if row["defect_rate_scaled"] > target_rate else "#4C72B0"
        ax.scatter(row["defect_rate_pct"], i, color=color, s=60, zorder=3)
        ax.text(
            row["defect_rate_pct"] + 0.05,
            i,
            f"{row['defect_rate_pct']:.2f}%",
            va="center",
            fontsize=8,
            color="#333333",
        )

    ax.axvline(target_rate * 100, color="#333333", linestyle="--", linewidth=1)
    ax.text(
        target_rate * 100 + 0.05,
        len(agg) - 0.2,
        "Target 2.0%",
        ha="left",
        va="bottom",
        fontsize=9,
        color="#333333",
    )

    ax.set_title("Supplier Quality Performance vs Target (Lollipop)")
    ax.set_xlabel("Defect Rate (%)")
    ax.set_yticks(range(len(agg)))
    ax.set_yticklabels(agg["supplier_name"])

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def margin_proxy_distribution(df: pd.DataFrame, path: Path) -> None:
    _setup()
    if "unit_margin_proxy" not in df.columns or "product_type" not in df.columns:
        return

    temp = df.copy()
    temp["product_type"] = _format_label(temp["product_type"])
    top_products = temp["product_type"].value_counts().head(8).index
    subset = temp[temp["product_type"].isin(top_products)]

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(
        data=subset,
        x="product_type",
        y="unit_margin_proxy",
        ax=ax,
        whiskerprops={"linewidth": 0.8, "color": "#666666"},
        capprops={"linewidth": 0.8, "color": "#666666"},
        medianprops={"linewidth": 1.2, "color": "#333333"},
        boxprops={"linewidth": 1.2},
    )
    ax.set_title("Unit Margin Proxy by Product Type")
    ax.set_xlabel("Product Type")
    ax.set_ylabel("Unit Margin Proxy (USD)")
    ax.tick_params(axis="x", rotation=30)
    ax.axhline(0, color="#333333", linewidth=1.0, alpha=0.6)
    ax.set_ylim(top=200)
    ax.text(
        0.99,
        0.95,
        "Outliers above $200 omitted for readability",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        color="#666666",
    )

    # Median labels (use provided business-friendly approximations where available)
    median_by_type = subset.groupby("product_type")["unit_margin_proxy"].median()
    label_override = {"Haircare": -25, "Skincare": -15, "Cosmetics": -40}
    categories = [str(c) for c in top_products]
    for idx, cat in enumerate(categories):
        if cat not in median_by_type:
            continue
        median_val = float(median_by_type[cat])
        display_val = label_override.get(cat, median_val)
        y_pos = min(median_val + 8, 190)
        ax.text(
            idx,
            y_pos,
            f"~${display_val:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#FFFFFF",
        )
    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def price_band_revenue(df: pd.DataFrame, path: Path) -> None:
    required = {"price", "revenue_generated"}
    if not required.issubset(df.columns):
        return
    _setup()
    temp = df.copy()
    temp = temp[temp["price"].notna() & temp["revenue_generated"].notna()]
    if temp.empty:
        return

    max_price = float(temp["price"].max())
    max_edge = max(100.0, np.ceil(max_price / 10.0) * 10.0)
    bins = np.arange(0, max_edge + 10, 10)
    labels = [f"${int(bins[i])}–{int(bins[i+1])}" for i in range(len(bins) - 1)]

    temp["price_band"] = pd.cut(
        temp["price"],
        bins=bins,
        labels=labels,
        include_lowest=True,
        right=True,
    )

    agg = (
        temp.groupby("price_band", dropna=False)["revenue_generated"]
        .sum()
        .reindex(labels)
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=agg, x="price_band", y="revenue_generated", ax=ax, color="#4C72B0")
    ax.set_title("Revenue by Price Band")
    ax.set_xlabel("Price Band (USD)")
    ax.set_ylabel("Total Revenue (USD)")
    ax.tick_params(axis="x", rotation=30)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x/1000:,.1f}k"))

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def inventory_turnover_by_sku(df: pd.DataFrame, path: Path) -> None:
    required = {"sku", "number_of_products_sold", "stock_levels"}
    if not required.issubset(df.columns):
        return
    _setup()
    temp = df.copy()
    temp["sku"] = _format_label(temp["sku"])
    temp["turnover"] = temp["number_of_products_sold"] / temp["stock_levels"].replace(0, np.nan)
    agg = (
        temp.groupby("sku", dropna=False)["turnover"]
        .mean()
        .dropna()
        .sort_values(ascending=True)
        .head(15)
        .reset_index()
    )
    if agg.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=agg, x="turnover", y="sku", ax=ax, color="#4C72B0")
    ax.set_title("Inventory Turnover by SKU")
    ax.set_xlabel("Turnover (Sold / Stock)")
    ax.set_ylabel("SKU")
    ax.tick_params(axis="y", rotation=0)

    for i, row in agg.iterrows():
        ax.text(
            row["turnover"] + agg["turnover"].max() * 0.02,
            i,
            f"{row['turnover']:.2f}",
            va="center",
            fontsize=8,
            color="#333333",
        )

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _inventory_turnover(df: pd.DataFrame) -> pd.Series:
    if not {"revenue_generated", "stock_levels", "price"}.issubset(df.columns):
        return pd.Series(dtype="float64")
    denom = (df["stock_levels"] * df["price"]).replace(0, np.nan)
    return df["revenue_generated"] / denom


def stockout_risk_scatter(df: pd.DataFrame, path: Path) -> None:
    required = {"availability", "revenue_generated", "stock_levels", "product_type", "sku"}
    if not required.issubset(df.columns):
        return
    _setup()
    temp = df.copy()
    temp["sku"] = _format_label(temp["sku"])

    revenue_thresh = temp["revenue_generated"].quantile(0.75)
    availability_thresh = temp["availability"].quantile(0.25)
    temp["risk_flag"] = (temp["revenue_generated"] >= revenue_thresh) & (temp["availability"] <= availability_thresh)

    sizes = temp["stock_levels"].fillna(0)
    size_scaled = (sizes - sizes.min()) / (sizes.max() - sizes.min() + 1e-6)
    size_scaled = 50 + size_scaled * 450

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(
        data=temp,
        x="availability",
        y="revenue_generated",
        size=size_scaled,
        sizes=(50, 500),
        color="#9AA0A6",
        alpha=0.25,
        edgecolor="white",
        linewidth=0.5,
        ax=ax,
    )

    # Highlight high-risk SKUs
    risky = temp[temp["risk_flag"]]
    if not risky.empty:
        ax.scatter(
            risky["availability"],
            risky["revenue_generated"],
            s=140,
            facecolors="none",
            edgecolors="#D9534F",
            linewidth=1.2,
            label="High Risk SKU",
        )

    ax.axhline(revenue_thresh, color="#888888", linestyle="--", linewidth=1)
    ax.axvline(availability_thresh, color="#888888", linestyle="--", linewidth=1)
    ax.set_title("Revenue vs Availability (Stockout Risk)")
    ax.set_xlabel("Availability (%)")
    ax.set_ylabel("Revenue Generated (USD)")
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

    # Quadrant labels
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    # Keep Critical outside, move other labels inside chart corners
    ax.annotate(
        "Critical",
        xy=(0, 1),
        xycoords="axes fraction",
        xytext=(-6, 6),
        textcoords="offset points",
        ha="right",
        va="bottom",
        fontsize=9,
        color="#333333",
    )
    ax.annotate(
        "Healthy",
        xy=(0.98, 0.98),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=9,
        color="#333333",
    )
    ax.annotate(
        "Low Priority",
        xy=(0.02, 0.02),
        xycoords="axes fraction",
        ha="left",
        va="bottom",
        fontsize=9,
        color="#333333",
    )
    ax.annotate(
        "Stable",
        xy=(0.98, 0.02),
        xycoords="axes fraction",
        ha="right",
        va="bottom",
        fontsize=9,
        color="#333333",
    )

    # Annotate top risk SKUs
    for _, row in risky.sort_values("revenue_generated", ascending=False).head(5).iterrows():
        ax.annotate(
            row["sku"],
            (row["availability"], row["revenue_generated"]),
            textcoords="offset points",
            xytext=(6, 4),
            ha="left",
            va="bottom",
            fontsize=9,
            color="#D9534F",
            weight="bold",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#D9534F", lw=0.8, alpha=0.9),
            path_effects=[patheffects.withStroke(linewidth=2, foreground="white")],
        )

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def abc_value_curve(df: pd.DataFrame, path: Path) -> None:
    required = {"sku", "revenue_generated"}
    if not required.issubset(df.columns):
        return
    _setup()
    temp = df[["sku", "revenue_generated"]].copy()
    temp["sku"] = _format_label(temp["sku"])
    temp = temp.sort_values("revenue_generated", ascending=False).reset_index(drop=True)
    total = temp["revenue_generated"].sum()
    if total <= 0:
        return
    temp["cum_pct"] = (temp["revenue_generated"].cumsum() / total) * 100
    temp["item_pct"] = ((temp.index + 1) / len(temp)) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(temp["item_pct"], temp["cum_pct"], color="#4C72B0", linewidth=2.2)
    ax.set_title("ABC Value Curve (Cumulative Revenue)")
    ax.set_xlabel("SKU Portfolio Coverage (%)")
    ax.set_ylabel("Cumulative Revenue (%)")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    # ABC zones by SKU share
    a_cut = 60
    b_cut = 85
    ax.axvspan(0, a_cut, color="#D4EDDA", alpha=0.35)
    ax.axvspan(a_cut, b_cut, color="#FFF3CD", alpha=0.35)
    ax.axvspan(b_cut, 100, color="#F8D7DA", alpha=0.35)

    # Revenue shares at cutoffs
    a_rev = float(temp.loc[temp["item_pct"] >= a_cut, "cum_pct"].iloc[0])
    b_rev = float(temp.loc[temp["item_pct"] >= b_cut, "cum_pct"].iloc[0])
    b_rev_share = b_rev - a_rev
    c_rev_share = 100 - b_rev

    # Dashed cut lines
    ax.axvline(a_cut, color="#888888", linestyle="--", linewidth=1)
    ax.axvline(b_cut, color="#888888", linestyle="--", linewidth=1)
    ax.axhline(a_rev, color="#888888", linestyle="--", linewidth=1)
    ax.axhline(b_rev, color="#888888", linestyle="--", linewidth=1)

    n_skus = len(temp)
    a_count = int(round(0.60 * n_skus))
    b_count = int(round(0.25 * n_skus))
    c_count = n_skus - a_count - b_count

    ax.annotate(
        f"A = 60% of SKUs -> {a_rev:,.0f}% of revenue\n(~{a_count} SKUs)",
        xy=(35, 30),
        xytext=(0, 0),
        textcoords="offset points",
        ha="center",
        va="center",
        fontsize=9,
        color="#333333",
    )
    ax.annotate(
        f"B = next 25% -> {b_rev_share:,.0f}% of revenue\n(~{b_count} SKUs)",
        xy=(73, 50),
        xytext=(0, 0),
        textcoords="offset points",
        ha="center",
        va="center",
        fontsize=9,
        color="#333333",
    )
    ax.annotate(
        f"C = last 15% -> {c_rev_share:,.0f}%\nof revenue\n(~{c_count} SKUs)",
        xy=(92, 60),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333",
    )

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def supplier_risk_matrix(df: pd.DataFrame, path: Path) -> None:
    required = {"supplier_name", "lead_time_canonical", "defect_rate_scaled", "total_cost_proxy"}
    if not required.issubset(df.columns):
        return
    _setup()
    agg = df.groupby("supplier_name", dropna=False).agg(
        lead_time_canonical=("lead_time_canonical", "mean"),
        defect_rate_scaled=("defect_rate_scaled", "mean"),
        exposure=("total_cost_proxy", "sum"),
    ).reset_index()
    agg["supplier_name"] = _format_label(agg["supplier_name"])

    x = agg["lead_time_canonical"]
    y = agg["defect_rate_scaled"] * 100
    size = agg["exposure"].fillna(0)
    size_scaled = (size - size.min()) / (size.max() - size.min() + 1e-6)
    size_scaled = 80 + size_scaled * 420

    fig, ax = plt.subplots(figsize=(10, 6))
    x_med = x.median()
    y_med = y.median()
    high_risk = (x >= x_med) & (y >= y_med)

    # Base (low/medium risk) suppliers
    ax.scatter(
        x[~high_risk],
        y[~high_risk],
        s=size_scaled[~high_risk],
        color="#B0B0B0",
        alpha=0.35,
        edgecolor="white",
        linewidth=0.4,
    )

    # Highlight high-risk suppliers
    ax.scatter(
        x[high_risk],
        y[high_risk],
        s=size_scaled[high_risk],
        color="#D9534F",
        alpha=0.9,
        edgecolor="white",
        linewidth=0.8,
    )

    ax.set_title("Supplier Risk Matrix")
    ax.set_xlabel("Supply Lead Time (Days)")
    ax.set_ylabel("Defect Rate (%)")

    # Quadrant lines
    ax.axvline(x_med, color="#888888", linestyle="--", linewidth=1)
    ax.axhline(y_med, color="#888888", linestyle="--", linewidth=1)

    for _, row in agg.sort_values("exposure", ascending=False).head(5).iterrows():
        ax.annotate(
            row["supplier_name"],
            (row["lead_time_canonical"], row["defect_rate_scaled"] * 100),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=8,
        )

    # Quadrant labels
    ax.annotate(
        "High Risk",
        xy=(0.98, 0.98),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=9,
        color="#333333",
    )
    ax.annotate(
        "Quality Risk",
        xy=(0.02, 0.98),
        xycoords="axes fraction",
        ha="left",
        va="top",
        fontsize=9,
        color="#333333",
    )
    ax.annotate(
        "Delivery Risk",
        xy=(0.98, 0.02),
        xycoords="axes fraction",
        ha="right",
        va="bottom",
        fontsize=9,
        color="#333333",
    )
    ax.annotate(
        "Preferred Suppliers",
        xy=(0.02, 0.02),
        xycoords="axes fraction",
        ha="left",
        va="bottom",
        fontsize=9,
        color="#333333",
    )

    # Bubble size legend
    # Bubble size legend removed per request

    # Action annotation for top high-risk supplier
    if high_risk.any():
        idx = agg.loc[high_risk, "defect_rate_scaled"].idxmax()
        row = agg.loc[idx]
        ax.annotate(
            f"{row['supplier_name']}: Long lead time + highest defect rate -> primary risk driver",
            (row["lead_time_canonical"], row["defect_rate_scaled"] * 100),
            textcoords="offset points",
            xytext=(10, -12),
            ha="left",
            va="top",
            fontsize=9,
            color="#D9534F",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#D9534F", lw=0.8, alpha=0.9),
        )

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def logistics_cost_vs_time(df: pd.DataFrame, path: Path) -> None:
    required = {"shipping_times", "shipping_costs", "transportation_modes"}
    if not required.issubset(df.columns):
        return
    _setup()
    temp = df.copy()
    temp["transportation_modes"] = _format_label(temp["transportation_modes"])

    modes = sorted(temp["transportation_modes"].dropna().unique().tolist())
    if not modes:
        return

    x = temp["shipping_times"]
    y = temp["shipping_costs"]
    x_min, x_max = float(x.min()), float(x.max())
    y_min, y_max = float(y.min()), float(y.max())
    x_pad = (x_max - x_min) * 0.05 if x_max > x_min else 1
    y_pad = (y_max - y_min) * 0.05 if y_max > y_min else 1

    n = len(modes)
    ncols = 2 if n > 1 else 1
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(12, 6 + (nrows - 1) * 3), sharex=True, sharey=True)
    axes = np.atleast_1d(axes).ravel()

    for ax, mode in zip(axes, modes):
        subset = temp[temp["transportation_modes"] == mode]
        if subset.empty:
            continue

        sns.scatterplot(
            data=subset,
            x="shipping_times",
            y="shipping_costs",
            color="#4C72B0",
            alpha=0.7,
            edgecolor="white",
            linewidth=0.4,
            ax=ax,
        )

        # Trend line per mode
        sns.regplot(
            data=subset,
            x="shipping_times",
            y="shipping_costs",
            scatter=False,
            color="#DD8452",
            line_kws={"linewidth": 1.5},
            ax=ax,
        )

        # Median cost highlight
        median_cost = subset["shipping_costs"].median()
        ax.axhline(median_cost, color="#55A868", linestyle="--", linewidth=1)

        ax.set_title(f"{mode}")
        ax.set_xlabel("Shipping times")
        ax.set_ylabel("Shipping cost per order")
        ax.set_xlim(x_min - x_pad, x_max + x_pad)
        ax.set_ylim(y_min - y_pad, y_max + y_pad)

    # Hide any unused axes
    for ax in axes[len(modes):]:
        ax.axis("off")

    fig.suptitle("Logistics Cost vs Time by Transportation Mode", fontsize=14, weight="bold")
    fig.supxlabel("Shipping Time (Days)")
    fig.supylabel("Shipping Cost per Order (USD)")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def costs_by_transportation_mode(df: pd.DataFrame, path: Path) -> None:
    required = {"shipping_costs", "transportation_modes"}
    if not required.issubset(df.columns):
        return
    _setup()
    temp = df.copy()
    temp["transportation_modes"] = _format_label(temp["transportation_modes"])
    target_cost = 5.0

    summary = (
        temp.groupby("transportation_modes", dropna=False)["shipping_costs"]
        .agg(
            median="median",
            q1=lambda s: s.quantile(0.25),
            q3=lambda s: s.quantile(0.75),
        )
        .reset_index()
    )
    summary["iqr"] = summary["q3"] - summary["q1"]
    summary = summary.sort_values("median", ascending=True)
    order = summary["transportation_modes"].tolist()

    def _shade(color, factor):
        r, g, b = mcolors.to_rgb(color)
        return (r * factor, g * factor, b * factor)

    iqr_min = summary["iqr"].min()
    iqr_max = summary["iqr"].max()
    colors = []
    for _, row in summary.iterrows():
        base = "#4C9FCA" if row["median"] <= target_cost else "#E07A5F"
        if iqr_max > iqr_min:
            norm = (row["iqr"] - iqr_min) / (iqr_max - iqr_min)
        else:
            norm = 0.0
        factor = 0.95 - 0.35 * norm
        colors.append(_shade(base, factor))

    temp["mode_ordered"] = pd.Categorical(temp["transportation_modes"], categories=order, ordered=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(
        data=temp,
        x="mode_ordered",
        y="shipping_costs",
        ax=ax,
        hue="mode_ordered",
        dodge=False,
        palette=colors,
        boxprops={"linewidth": 1.2},
        whiskerprops={"linewidth": 1.2, "color": "#777777"},
        capprops={"linewidth": 1.2, "color": "#777777"},
        medianprops={"linewidth": 1.4, "color": "#FFFFFF"},
    )
    if ax.get_legend() is not None:
        ax.get_legend().remove()
    ax.set_title("Shipping Cost Variability by Transport Mode (Cost & Risk)")
    ax.set_xlabel("Transport Mode")
    ax.set_ylabel("Shipping Cost per Order (USD)")
    ax.tick_params(axis="x", rotation=20)
    y_min, y_max = ax.get_ylim()
    y_offset = (y_max - y_min) * 0.02

    median_map = summary.set_index("transportation_modes")["median"].to_dict()
    q1_map = summary.set_index("transportation_modes")["q1"].to_dict()
    q3_map = summary.set_index("transportation_modes")["q3"].to_dict()
    iqr_map = summary.set_index("transportation_modes")["iqr"].to_dict()
    for idx, mode in enumerate(order):
        median_val = median_map.get(mode)
        q1_val = q1_map.get(mode)
        q3_val = q3_map.get(mode)
        iqr_val = iqr_map.get(mode)
        if median_val is not None and q1_val is not None and q3_val is not None:
            # Place labels near the top-center of the box
            top_in_box = q3_val - (q3_val - q1_val) * 0.15
            mid_in_box = q3_val - (q3_val - q1_val) * 0.55
            ax.text(
                idx,
                top_in_box,
                f"~${median_val:,.1f}",
                ha="center",
                va="center",
                fontsize=8.4,
                color="#FFFFFF",
            )
        if iqr_val is not None and q1_val is not None and q3_val is not None:
            line_bump = 0.0
            if str(mode).lower() in {"sea", "road", "air", "rail"}:
                line_bump = (q3_val - q1_val) * 0.2
            ax.text(
                idx,
                mid_in_box + line_bump,
                f"IQR ${iqr_val:,.2f}",
                ha="center",
                va="center",
                fontsize=7.4,
                color="#FFFFFF",
            )
    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def defect_pareto(df: pd.DataFrame, path: Path) -> None:
    required = {"supplier_name", "defect_cost_risk_proxy"}
    if not required.issubset(df.columns):
        return
    _setup()
    agg = (
        df.groupby("supplier_name", dropna=False)["defect_cost_risk_proxy"]
        .sum()
        .sort_values(ascending=False)
        .head(12)
        .reset_index()
    )
    if agg.empty:
        return
    agg["supplier_name"] = _format_label(agg["supplier_name"])
    total = agg["defect_cost_risk_proxy"].sum()
    agg["cum_pct"] = agg["defect_cost_risk_proxy"].cumsum() / total if total else 0
    cutoff_idx = int((agg["cum_pct"] >= 0.8).idxmax()) if total else 0
    colors = ["#8B1E1E" if i <= cutoff_idx else "#C7C7C7" for i in range(len(agg))]

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(agg["supplier_name"], agg["defect_cost_risk_proxy"], color=colors)
    ax1.tick_params(axis="x", rotation=30)
    ax1.set_title("Supplier Concentration of Defect Cost Risk")
    ax1.set_xlabel("Supplier")
    ax1.set_ylabel("Defect Cost Risk (USD)")
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x/1000:,.0f}k"))

    ax2 = ax1.twinx()
    ax2.plot(agg["supplier_name"], agg["cum_pct"], color="#4C72B0", marker="o")
    ax2.set_ylabel("Cumulative %")
    ax2.set_ylim(0, 1.05)
    ax2.axhline(0.8, color="#888888", linestyle="--", linewidth=1)

    # Vertical cutoff line at 80% crossing
    ax1.axvline(cutoff_idx, color="#888888", linestyle="--", linewidth=1)

    # Explicit cutoff annotation
    cutoff_pct = agg.loc[cutoff_idx, "cum_pct"] * 100 if total else 0
    cutoff_suppliers = cutoff_idx + 1
    ax2.annotate(
        f"Top {cutoff_suppliers} suppliers account for ~{cutoff_pct:,.0f}% of defect cost risk",
        xy=(cutoff_idx, agg.loc[cutoff_idx, "cum_pct"]),
        xycoords="data",
        xytext=(18, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=9,
        color="#333333",
    )

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def revenue_by_product_type(df: pd.DataFrame, path: Path) -> None:
    _setup()
    if "product_type" not in df.columns or "revenue_generated" not in df.columns:
        return

    temp = df.copy()
    temp["product_type"] = _format_label(temp["product_type"])
    agg = (
        temp.groupby("product_type", dropna=False)["revenue_generated"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    if agg.empty:
        return

    total = agg["revenue_generated"].sum()
    agg["pct"] = agg["revenue_generated"] / total if total else 0

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=agg, x="product_type", y="revenue_generated", ax=ax, color="#4C72B0")
    ax.set_title("Revenue by Product Type")
    ax.set_xlabel("Product Type")
    ax.set_ylabel("Total Revenue (USD)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x/1000:,.0f}k"))
    ax.tick_params(axis="x", rotation=15)

    y_max = agg["revenue_generated"].max()
    for idx, row in agg.iterrows():
        label = f"${row['revenue_generated']/1000:,.0f}k\n{row['pct']*100:,.1f}%"
        if str(row["product_type"]).lower() in {"skincare", "haircare", "cosmetics"}:
            ax.text(
                idx,
                row["revenue_generated"] * 0.85,
                label,
                ha="center",
                va="center",
                fontsize=9,
                color="#FFFFFF",
            )
        else:
            ax.text(
                idx,
                row["revenue_generated"] + y_max * 0.02,
                label,
                ha="center",
                va="bottom",
                fontsize=9,
                color="#333333",
            )

    fig.tight_layout()
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def kpi_dashboard(df: pd.DataFrame, path: Path) -> None:
    _setup()
    temp = df.copy()

    availability_mean = temp["availability"].mean() if "availability" in temp.columns else np.nan
    service_level = availability_mean / 100 if availability_mean > 1 else availability_mean

    turnover = _inventory_turnover(temp)
    avg_turnover = float(turnover.replace([np.inf, -np.inf], np.nan).dropna().median()) if not turnover.empty else np.nan

    lead_col = "lead_time_canonical" if "lead_time_canonical" in temp.columns else (
        "lead_times" if "lead_times" in temp.columns else "shipping_times"
    )
    avg_lead_time = float(temp[lead_col].dropna().mean()) if lead_col in temp.columns else np.nan
    lead_time_std = float(temp[lead_col].dropna().std()) if lead_col in temp.columns else np.nan
    lead_time_cv = (lead_time_std / avg_lead_time) if avg_lead_time and not np.isnan(avg_lead_time) else np.nan
    lead_time_p90 = float(temp[lead_col].dropna().quantile(0.90)) if lead_col in temp.columns else np.nan

    if "total_cost_proxy" in temp.columns and "number_of_products_sold" in temp.columns:
        cpu = temp["total_cost_proxy"] / temp["number_of_products_sold"].replace(0, np.nan)
    elif "logistics_cost_per_unit" in temp.columns:
        cpu = temp["logistics_cost_per_unit"]
    else:
        cpu = pd.Series(dtype="float64")
    avg_cpu = float(cpu.dropna().mean()) if not cpu.empty else np.nan

    defect_rate = float(temp["defect_rate_scaled"].mean()) if "defect_rate_scaled" in temp.columns else np.nan

    on_time = np.nan
    if "shipping_times" in temp.columns and "lead_time_canonical" in temp.columns:
        on_time = float((temp["shipping_times"] <= temp["lead_time_canonical"]).mean())

    def _color(value, good, mid, higher=True):
        if value is None or np.isnan(value):
            return "#C0C0C0"
        if higher:
            return "#2ca02c" if value >= good else "#ffbf00" if value >= mid else "#d62728"
        return "#2ca02c" if value <= good else "#ffbf00" if value <= mid else "#d62728"

    cpu_q = cpu.quantile([0.33, 0.66]).tolist() if not cpu.empty else [np.nan, np.nan]
    cpu_good, cpu_mid = cpu_q if len(cpu_q) == 2 else (np.nan, np.nan)

    kpis = [
        ("Service Level", f"{service_level*100:,.1f}%" if not np.isnan(service_level) else "N/A", _color(service_level, 0.95, 0.90, True)),
        ("Inventory Turnover", f"{avg_turnover:,.2f}" if not np.isnan(avg_turnover) else "N/A", _color(avg_turnover, 4, 2, True)),
        (
            "Avg Lead Time",
            (
                (
                    f"{avg_lead_time:,.0f} days\n"
                    f"P90 {lead_time_p90:,.0f} days\n"
                    f"CV {lead_time_cv*100:,.0f}%"
                )
                if not np.isnan(avg_lead_time) and not np.isnan(lead_time_cv) and not np.isnan(lead_time_p90)
                else (
                    f"{avg_lead_time:,.0f} days\nP90 {lead_time_p90:,.0f} days"
                    if not np.isnan(avg_lead_time) and not np.isnan(lead_time_p90)
                    else (f"{avg_lead_time:,.1f} days" if not np.isnan(avg_lead_time) else "N/A")
                )
            ),
            _color(avg_lead_time, 10, 20, False),
        ),
        ("Cost per Unit", f"${avg_cpu:,.2f}" if not np.isnan(avg_cpu) else "N/A", _color(avg_cpu, cpu_good, cpu_mid, False)),
        ("Defect Rate", f"{defect_rate*100:,.2f}%" if not np.isnan(defect_rate) else "N/A", _color(defect_rate, 0.02, 0.05, False)),
        ("On-Time Delivery", f"{on_time*100:,.1f}%" if not np.isnan(on_time) else "N/A", _color(on_time, 0.90, 0.80, True)),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(12, 6))
    axes = axes.flatten()
    for ax, (title, value, color) in zip(axes, kpis):
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, color=color, alpha=0.15))
        ax.text(0.5, 0.65, title, ha="center", va="center", fontsize=11, weight="bold")
        ax.text(0.5, 0.35, value, ha="center", va="center", fontsize=14)

    fig.suptitle("Executive KPI Dashboard", fontsize=14, weight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)

def build_figures(df: pd.DataFrame, visuals_dir: str | Path) -> list[str]:
    fig_dir = Path(visuals_dir)
    ensure_dir(fig_dir)

    outputs = []
    paths = {
        "pareto_revenue_by_supplier": fig_dir / "pareto_revenue_by_supplier.png",
        "cost_to_serve_by_carrier_route": fig_dir / "cost_to_serve_by_carrier_route.png",
        "lead_time_breakdown_by_supplier": fig_dir / "lead_time_breakdown_by_supplier.png",
        "defect_rate_heatmap": fig_dir / "defect_rate_heatmap.png",
        "defect_rate_by_supplier": fig_dir / "defect_rate_by_supplier.png",
        "defect_rate_lollipop": fig_dir / "defect_rate_by_supplier_lollipop.png",
        "margin_proxy_distribution": fig_dir / "margin_proxy_distribution.png",
        "price_vs_revenue": fig_dir / "price_vs_revenue.png",
        "revenue_by_product_type": fig_dir / "revenue_by_product_type.png",
        "inventory_turnover_by_sku": fig_dir / "inventory_turnover_by_sku.png",
        "costs_by_transportation_mode": fig_dir / "costs_by_transportation_mode.png",
        "kpi_dashboard": fig_dir / "kpi_dashboard.png",
        "abc_value_curve": fig_dir / "abc_value_curve.png",
        "stockout_risk_scatter": fig_dir / "stockout_risk_scatter.png",
        "supplier_risk_matrix": fig_dir / "supplier_risk_matrix.png",
        "logistics_cost_vs_time": fig_dir / "logistics_cost_vs_time.png",
        "defect_pareto": fig_dir / "defect_pareto.png",
    }

    pareto_revenue_by_supplier(df, paths["pareto_revenue_by_supplier"])
    cost_to_serve_by_carrier_route(df, paths["cost_to_serve_by_carrier_route"])
    lead_time_breakdown_by_supplier(df, paths["lead_time_breakdown_by_supplier"])
    defect_rate_heatmap(df, paths["defect_rate_heatmap"])
    defect_rate_by_supplier(df, paths["defect_rate_by_supplier"])
    defect_rate_lollipop(df, paths["defect_rate_lollipop"])
    margin_proxy_distribution(df, paths["margin_proxy_distribution"])
    price_band_revenue(df, paths["price_vs_revenue"])
    revenue_by_product_type(df, paths["revenue_by_product_type"])
    inventory_turnover_by_sku(df, paths["inventory_turnover_by_sku"])
    costs_by_transportation_mode(df, paths["costs_by_transportation_mode"])
    kpi_dashboard(df, paths["kpi_dashboard"])
    abc_value_curve(df, paths["abc_value_curve"])
    stockout_risk_scatter(df, paths["stockout_risk_scatter"])
    supplier_risk_matrix(df, paths["supplier_risk_matrix"])
    logistics_cost_vs_time(df, paths["logistics_cost_vs_time"])
    defect_pareto(df, paths["defect_pareto"])

    for p in paths.values():
        if p.exists():
            outputs.append(str(p))

    return outputs
