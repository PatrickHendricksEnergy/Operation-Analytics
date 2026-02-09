"""Markdown and data dictionary generators."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

from .common_etl import ensure_dir


def generate_data_dictionary(
    df: pd.DataFrame,
    descriptions: Dict[str, str] | None = None,
    table_name: str | None = None,
) -> pd.DataFrame:
    descriptions = descriptions or {}
    rows = []
    for col in df.columns:
        series = df[col]
        example = series.dropna().iloc[0] if series.notna().any() else ""
        row = {
            "column": col,
            "type": str(series.dtype),
            "nullable": bool(series.isna().any()),
            "%missing": float(series.isna().mean() * 100),
            "description": descriptions.get(col, ""),
            "example_value": example,
        }
        if table_name:
            row["table"] = table_name
        rows.append(row)
    return pd.DataFrame(rows)


def write_data_dictionary(path: str | Path, dictionaries: List[pd.DataFrame]) -> None:
    df = pd.concat(dictionaries, ignore_index=True)
    ensure_dir(Path(path).parent)
    df.to_csv(path, index=False)


def render_star_schema_md(
    fact_name: str,
    fact_grain: str,
    dims: List[Dict[str, str]],
    relationships: List[str],
) -> str:
    lines = [
        f"# Star Schema: {fact_name}",
        "",
        "## Fact Grain",
        fact_grain,
        "",
        "## Dimensions",
    ]
    for d in dims:
        lines.append(f"- {d['name']}: key `{d['key']}`, attributes: {d['attributes']}")
    lines.extend(["", "## Relationships"])
    lines.extend([f"- {rel}" for rel in relationships])
    return "\n".join(lines)


def render_bi_model_snapshot(
    fact_grain: str,
    measures: List[str],
    dims: List[str],
    join_keys: List[str],
) -> str:
    lines = [
        "## BI Model Snapshot",
        f"- Fact grain: {fact_grain}",
        f"- Measures: {', '.join(measures)}",
        f"- Dimensions: {', '.join(dims)}",
        f"- Join keys: {', '.join(join_keys)}",
    ]
    return "\n".join(lines)


def write_text(path: str | Path, content: str) -> None:
    ensure_dir(Path(path).parent)
    Path(path).write_text(content)
