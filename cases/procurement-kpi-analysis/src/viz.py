"""Visualization helpers for procurement KPI dataset."""
from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter
import numpy as np

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

def _scale_info(values: pd.Series | list | np.ndarray) -> tuple[float, str]:
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


def _make_scaled_formatter(scale: float):
    def _fmt(x, pos):
        try:
            return _space_thousands(x / scale, pos)
        except Exception:
            return str(x)
    return FuncFormatter(_fmt)


def _apply_scaled_axis(ax, axis: str, label: str, values, currency: bool = False) -> None:
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


def savings_by_supplier(df: pd.DataFrame, path: Path) -> None:
    if "supplier" not in df.columns or "realized_savings" not in df.columns:
        return
    _setup()
    agg = (
        df.groupby("supplier", dropna=False)["realized_savings"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=agg, x="supplier", y="realized_savings", ax=ax, color="#4C72B0")
    ax.set_title("Realized Savings by Supplier")
    ax.set_xlabel("Supplier")
    ax.tick_params(axis="x", rotation=30)
    _apply_scaled_axis(ax, "y", "Realized Savings", agg["realized_savings"], currency=True)
    _save(fig, path)


def order_value_by_supplier(df: pd.DataFrame, path: Path) -> None:
    if "supplier" not in df.columns or "negotiated_po_value" not in df.columns:
        return
    _setup()
    agg = (
        df.groupby("supplier", dropna=False)["negotiated_po_value"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    if agg.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=agg, y="supplier", x="negotiated_po_value", ax=ax, color="#4C72B0")
    ax.set_title("Order Value by Supplier")
    ax.set_ylabel("Supplier")

    # Format axis and labels in millions ($M)
    def _fmt_millions(x, _pos):
        return f"{x/1e6:,.1f}M"

    ax.xaxis.set_major_formatter(FuncFormatter(_fmt_millions))
    ax.set_xlabel("Order Value (USD, Millions)")
    ax.set_xlim(left=4e6)

    # Add value labels at end of bars
    for i, row in agg.iterrows():
        ax.annotate(
            f"{row['negotiated_po_value']/1e6:,.1f}M",
            (row["negotiated_po_value"], i),
            textcoords="offset points",
            xytext=(4, 0),
            ha="left",
            va="center",
            fontsize=9,
        )

    _save(fig, path)


def savings_by_category(df: pd.DataFrame, path: Path) -> None:
    if "item_category" not in df.columns or "realized_savings" not in df.columns:
        return
    _setup()
    agg = (
        df.groupby("item_category", dropna=False)["realized_savings"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=agg, x="item_category", y="realized_savings", ax=ax, color="#55A868")
    ax.set_title("Realized Savings by Category")
    ax.set_xlabel("Category")
    ax.tick_params(axis="x", rotation=30)
    _apply_scaled_axis(ax, "y", "Realized Savings", agg["realized_savings"], currency=True)
    _save(fig, path)


def order_value_trend_monthly(df: pd.DataFrame, path: Path) -> None:
    required = {"order_date", "negotiated_po_value"}
    if not required.issubset(df.columns):
        return

    temp = df.copy()
    temp["order_date"] = pd.to_datetime(temp["order_date"], errors="coerce")
    temp = temp.dropna(subset=["order_date", "negotiated_po_value"])
    if temp.empty:
        return

    temp["month"] = temp["order_date"].dt.to_period("M").dt.to_timestamp()
    # End chart at 2023 Q4 (exclude 2024+)
    temp = temp[temp["month"] <= pd.Timestamp("2023-12-01")]
    monthly = (
        temp.groupby("month", dropna=False)["negotiated_po_value"]
        .sum()
        .reset_index()
        .sort_values("month")
    )

    # Identify partial months (edge months with incomplete coverage)
    coverage = temp.groupby("month", dropna=False)["order_date"].agg(["min", "max"]).reset_index()
    coverage["month_start"] = coverage["month"]
    coverage["month_end"] = coverage["month"] + pd.offsets.MonthEnd(0)
    coverage["is_partial"] = (coverage["min"] > coverage["month_start"]) | (coverage["max"] < coverage["month_end"])
    partial_months = set(coverage.loc[coverage["is_partial"], "month"])

    # Keep partial months in the trend (no exclusion)
    excluded_partial = False

    monthly["rolling_3m"] = monthly["negotiated_po_value"].rolling(window=3, min_periods=1).mean()

    _setup()
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(
        monthly["month"],
        monthly["negotiated_po_value"],
        marker="o",
        linewidth=2,
        color="#4C72B0",
        label="Monthly order value",
    )
    ax.plot(
        monthly["month"],
        monthly["rolling_3m"],
        linewidth=2.5,
        color="#DD8452",
        label="3-month rolling avg",
    )

    # Format Y-axis in millions
    def _fmt_millions(x, _pos):
        return f"{x/1e6:,.1f}M"

    ax.yaxis.set_major_formatter(FuncFormatter(_fmt_millions))
    ax.set_ylabel("Order Value (USD, Millions)")
    ax.set_xlabel("Quarter")
    ax.set_title("Order Value Trend (Monthly)")

    # Quarterly ticks (Q1, Q2, ...)
    months = monthly["month"]
    quarter_mask = months.dt.month.isin([1, 4, 7, 10])
    quarter_ticks = months[quarter_mask]
    if quarter_ticks.empty:
        quarter_ticks = months
    quarter_labels = [f"{d.year} Q{((d.month - 1) // 3) + 1}" for d in quarter_ticks]
    ax.set_xticks(quarter_ticks)
    ax.set_xticklabels(quarter_labels, rotation=0)

    ax.legend(loc="upper left")

    if excluded_partial:
        fig.text(0.01, 0.01, "Partial months excluded", fontsize=9, color="#666666")

    _save(fig, path)


def defect_cost_vs_savings(df: pd.DataFrame, path: Path) -> None:
    required = {"realized_savings", "defective_cost_exposure", "supplier"}
    if not required.issubset(df.columns):
        return

    group_cols = ["supplier"]
    if "item_category" in df.columns:
        # Optional: switch to supplier + category by uncommenting next line
        # group_cols = ["supplier", "item_category"]
        pass

    agg = (
        df.groupby(group_cols, dropna=False)[["realized_savings", "defective_cost_exposure"]]
        .sum()
        .reset_index()
    )

    if agg.empty:
        return

    x_med = agg["realized_savings"].median()
    y_med = agg["defective_cost_exposure"].median()

    def quadrant(row):
        high_savings = row["realized_savings"] >= x_med
        high_defects = row["defective_cost_exposure"] >= y_med
        if high_savings and not high_defects:
            return "Strategic (High Savings / Low Defects)"
        if high_savings and high_defects:
            return "False Savings (High Savings / High Defects)"
        if not high_savings and not high_defects:
            return "Stable Low Impact (Low Savings / Low Defects)"
        return "Replace/Exit (Low Savings / High Defects)"

    agg["quadrant"] = agg.apply(quadrant, axis=1)

    palette = {
        "Strategic (High Savings / Low Defects)": "#2ca02c",
        "False Savings (High Savings / High Defects)": "#ffbf00",
        "Stable Low Impact (Low Savings / Low Defects)": "#1f77b4",
        "Replace/Exit (Low Savings / High Defects)": "#d62728",
    }

    _setup()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(
        data=agg,
        x="realized_savings",
        y="defective_cost_exposure",
        hue="quadrant",
        palette=palette,
        ax=ax,
        s=90,
        alpha=0.85,
        edgecolor="white",
        linewidth=0.6,
    )
    # Label each point by supplier for quick identification
    for _, row in agg.iterrows():
        ax.annotate(
            str(row.get("supplier", "")),
            (row["realized_savings"], row["defective_cost_exposure"]),
            textcoords="offset points",
            xytext=(4, 4),
            ha="left",
            va="bottom",
            fontsize=8,
        )
    ax.axvline(x_med, color="grey", linestyle="--", linewidth=1)
    ax.axhline(y_med, color="grey", linestyle="--", linewidth=1)
    ax.set_title("Quadrant: Value vs Risk (Supplier Level)")
    ax.set_xlabel("Realized Savings")
    ax.set_ylabel("Defective Cost Exposure")
    ax.legend(
        title="Quadrant",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=True,
        fontsize=7,
        title_fontsize=8,
        markerscale=0.7,
        borderpad=0.3,
        labelspacing=0.3,
        handletextpad=0.4,
    )
    _apply_scaled_axis(ax, "x", "Realized Savings", agg["realized_savings"], currency=True)
    _apply_scaled_axis(ax, "y", "Defective Cost Exposure", agg["defective_cost_exposure"], currency=True)
    _save(fig, path)


def lead_time_distribution(df: pd.DataFrame, path: Path) -> None:
    if "procurement_lead_time_days" not in df.columns:
        return
    _setup()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(df["procurement_lead_time_days"].dropna(), bins=20, ax=ax)
    ax.set_title("Procurement Lead Time Distribution")
    ax.set_xlabel("Lead Time (Days)")
    ax.set_ylabel("Count")
    _apply_scaled_axis(ax, "x", "Lead Time (Days)", df["procurement_lead_time_days"])
    _apply_scaled_axis(ax, "y", "Count", ax.get_yticks())
    _save(fig, path)


def lead_time_heatmap(df: pd.DataFrame, path: Path) -> None:
    required = {"supplier", "item_category", "procurement_lead_time_days"}
    if not required.issubset(df.columns):
        return

    temp = df.copy()
    status_label = "All Orders"
    if "order_status" in temp.columns:
        delivered_mask = temp["order_status"].astype(str).str.strip().str.lower().eq("delivered")
        if delivered_mask.any():
            temp = temp[delivered_mask]
            status_label = "Delivered Orders"

    temp = temp.dropna(subset=["procurement_lead_time_days"])
    if temp.empty:
        return

    pivot = temp.pivot_table(
        index="supplier",
        columns="item_category",
        values="procurement_lead_time_days",
        aggfunc="mean",
    )
    if pivot.empty:
        return

    _setup()
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(
        pivot,
        cmap="YlOrRd",
        ax=ax,
        cbar_kws={"label": "Avg Lead Time (Days)"},
    )
    ax.set_title(f"Lead Time Heatmap by Supplier x Category ({status_label})")
    ax.set_xlabel("Item Category")
    ax.set_ylabel("Supplier")
    ax.tick_params(axis="x", rotation=30)
    _save(fig, path)


def order_status_impact(df: pd.DataFrame, path: Path) -> None:
    if "order_status" not in df.columns or "negotiated_po_value" not in df.columns:
        return
    _setup()
    agg = (
        df.groupby("order_status", dropna=False)["negotiated_po_value"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=agg, x="order_status", y="negotiated_po_value", ax=ax, color="#C44E52")
    ax.set_title("Spend by Order Status")
    ax.set_xlabel("Order Status")
    ax.tick_params(axis="x", rotation=30)
    _apply_scaled_axis(ax, "y", "Negotiated PO Value", agg["negotiated_po_value"], currency=True)
    _save(fig, path)


def order_status_distribution(df: pd.DataFrame, path: Path) -> None:
    if "order_status" not in df.columns:
        return

    _setup()
    counts = df["order_status"].value_counts(dropna=False)
    if counts.empty:
        return

    labels = counts.index.astype(str).tolist()
    values = counts.values
    total = values.sum()
    percents = (values / total) * 100 if total else values

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = sns.color_palette("Set2", n_colors=len(labels))

    def _autopct(pct):
        count = int(round(pct * total / 100.0)) if total else 0
        return f"{pct:.1f}%\n({count})"

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct=_autopct,
        startangle=90,
        colors=colors,
        textprops={"fontsize": 10},
    )
    ax.set_title("Order Status Distribution (%, Count)")
    _save(fig, path)


def compliance_spend(df: pd.DataFrame, path: Path) -> None:
    if "compliance" not in df.columns or "negotiated_po_value" not in df.columns:
        return
    _setup()
    agg = (
        df.groupby("compliance", dropna=False)["negotiated_po_value"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    if agg.empty:
        return

    labels = agg["compliance"].astype(str).tolist()
    values = agg["negotiated_po_value"].values
    total = values.sum()

    scale, suffix = _scale_info(values)
    def _autopct(pct):
        val = (pct / 100.0) * total
        scaled = val / scale if scale else val
        return f"{pct:.1f}%\n({_space_thousands(scaled, None)} USD)"

    fig, ax = plt.subplots(figsize=(7, 6))
    colors = sns.color_palette("Set2", n_colors=len(labels))
    ax.pie(
        values,
        labels=labels,
        autopct=_autopct,
        startangle=90,
        colors=colors,
        textprops={"fontsize": 10},
    )
    title = "Spend by Compliance"
    if suffix:
        title += f" (values in {suffix} USD)"
    else:
        title += " (values in USD)"
    ax.set_title(title)
    _save(fig, path)


def supplier_risk_score(df: pd.DataFrame, path: Path) -> None:
    if "supplier" not in df.columns or "supplier_risk_score" not in df.columns:
        return
    _setup()
    agg = df.sort_values("supplier_risk_score", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=agg, x="supplier", y="supplier_risk_score", ax=ax, color="#937860")
    ax.set_title("Supplier Risk Score")
    ax.set_xlabel("Supplier")
    ax.tick_params(axis="x", rotation=30)
    _apply_scaled_axis(ax, "y", "Risk Score", agg["supplier_risk_score"])
    _save(fig, path)


def supplier_risk_matrix(df: pd.DataFrame, path: Path) -> None:
    required = {"supplier", "spend_at_risk", "defect_rate_pct"}
    if not required.issubset(df.columns):
        return

    temp = df[list(required)].dropna()
    if temp.empty:
        return

    x = temp["spend_at_risk"]
    y = temp["defect_rate_pct"]

    # Base ranges to avoid empty bands/margins
    x_min = 0.0
    y_min = 0.0
    x_max = 3_500_000.0
    y_max = 0.12
    if x_max <= 0:
        x_max = 1.0
    if y_max <= 0:
        y_max = 0.01

    # Tertile thresholds for low/med/high buckets (ensure increasing)
    x1, x2 = x.quantile([0.33, 0.66]).tolist()
    y1, y2 = y.quantile([0.33, 0.66]).tolist()
    if x1 <= x_min:
        x1 = x_min + (x_max - x_min) / 3
    if x2 <= x1:
        x2 = x_min + 2 * (x_max - x_min) / 3
    if y1 <= y_min:
        y1 = y_min + (y_max - y_min) / 3
    if y2 <= y1:
        y2 = y_min + 2 * (y_max - y_min) / 3

    _setup()
    fig, ax = plt.subplots(figsize=(10, 6))

    # Background risk grid (low -> high)
    x_bins = [x_min, x1, x2, x_max]
    y_bins = [y_min, y1, y2, y_max]
    colors = [
        ["#d9f2d9", "#fff2cc", "#ffd9cc"],
        ["#c7e6c7", "#ffe5b4", "#ffc9b3"],
        ["#a8d5a8", "#ffd28a", "#ffb399"],
    ]
    y_span = y_bins[-1] - y_bins[0]
    for i in range(3):
        for j in range(3):
            ax.axvspan(
                x_bins[j],
                x_bins[j + 1],
                ymin=(y_bins[i] - y_bins[0]) / y_span,
                ymax=(y_bins[i + 1] - y_bins[0]) / y_span,
                facecolor=colors[i][j],
                alpha=0.6,
                edgecolor="white",
            )

    # Points
    sns.scatterplot(
        data=temp,
        x="spend_at_risk",
        y="defect_rate_pct",
        ax=ax,
        s=90,
        color="#4C72B0",
        edgecolor="white",
        linewidth=0.6,
    )

    # Labels
    for _, row in temp.iterrows():
        ax.annotate(
            str(row["supplier"]),
            (row["spend_at_risk"], row["defect_rate_pct"]),
            textcoords="offset points",
            xytext=(4, 4),
            ha="left",
            va="bottom",
            fontsize=8,
        )

    ax.set_title("Supplier Risk Matrix (Defect Rate vs Spend at Risk)")
    _apply_scaled_axis(ax, "x", "Spend at Risk", x, currency=True)
    ax.set_ylabel("Defect Rate (%)")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.margins(0)

    _save(fig, path)


def pareto_metric(df: pd.DataFrame, metric: str, path: Path, title: str) -> None:
    if metric not in df.columns or "supplier" not in df.columns:
        return
    _setup()
    temp = df[["supplier", metric]].copy()
    temp = temp.sort_values(metric, ascending=False).reset_index(drop=True)
    total = temp[metric].sum()
    temp["cum_pct"] = temp[metric].cumsum() / total if total else 0

    fig, ax1 = plt.subplots(figsize=(12, 6))
    sns.barplot(data=temp.head(15), x="supplier", y=metric, ax=ax1, color="#4C72B0")
    ax1.tick_params(axis="x", rotation=30)
    ax1.set_title(title)
    ax1.set_xlabel("Supplier")
    is_currency = metric in ["realized_savings", "negotiated_po_value", "gross_po_value"]
    _apply_scaled_axis(ax1, "y", metric.replace("_", " ").title(), temp.head(15)[metric], currency=is_currency)

    ax2 = ax1.twinx()
    ax2.plot(temp.head(15)["supplier"], temp.head(15)["cum_pct"], color="#DD8452", marker="o")
    ax2.set_ylabel("Cumulative %")
    ax2.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax2.set_ylim(0, 1.05)

    _save(fig, path)


def build_figures(df: pd.DataFrame, supplier_df: pd.DataFrame, reports_dir: str | Path) -> list[str]:
    reports_dir = Path(reports_dir)
    fig_dir = reports_dir / "figures"
    ensure_dir(fig_dir)

    outputs = []
    paths = {
        "order_value_by_supplier": fig_dir / "order_value_by_supplier.png",
        "order_value_trend_monthly": fig_dir / "order_value_trend_monthly.png",
        "savings_by_supplier": fig_dir / "savings_by_supplier.png",
        "savings_by_category": fig_dir / "savings_by_category.png",
        "defect_cost_vs_savings": fig_dir / "defect_cost_vs_savings.png",
        "lead_time_distribution": fig_dir / "lead_time_distribution.png",
        "lead_time_heatmap": fig_dir / "lead_time_heatmap.png",
        "order_status_distribution": fig_dir / "order_status_distribution.png",
        "order_status_impact": fig_dir / "order_status_impact.png",
        "compliance_spend": fig_dir / "compliance_spend.png",
        "supplier_risk_score": fig_dir / "supplier_risk_score.png",
        "supplier_risk_matrix": fig_dir / "supplier_risk_matrix.png",
        "pareto_savings": fig_dir / "pareto_savings.png",
    }

    order_value_by_supplier(df, paths["order_value_by_supplier"])
    order_value_trend_monthly(df, paths["order_value_trend_monthly"])
    savings_by_supplier(df, paths["savings_by_supplier"])
    savings_by_category(df, paths["savings_by_category"])
    defect_cost_vs_savings(df, paths["defect_cost_vs_savings"])
    lead_time_distribution(df, paths["lead_time_distribution"])
    lead_time_heatmap(df, paths["lead_time_heatmap"])
    order_status_distribution(df, paths["order_status_distribution"])
    order_status_impact(df, paths["order_status_impact"])
    compliance_spend(df, paths["compliance_spend"])

    if not supplier_df.empty:
        supplier_risk_score(supplier_df, paths["supplier_risk_score"])
        supplier_risk_matrix(supplier_df, paths["supplier_risk_matrix"])
        pareto_metric(supplier_df, "realized_savings", paths["pareto_savings"], "Pareto: Savings by Supplier")

    for p in paths.values():
        if p.exists():
            outputs.append(str(p))

    return outputs
