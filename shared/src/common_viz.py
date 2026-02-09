"""Shared visualization helpers."""
from __future__ import annotations

from pathlib import Path
import os

if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = str(Path("/tmp") / "matplotlib")
if "MPLBACKEND" not in os.environ:
    os.environ["MPLBACKEND"] = "Agg"

import matplotlib.pyplot as plt
import seaborn as sns

from .common_etl import ensure_dir, set_matplotlib_cache_dir


def setup_style() -> None:
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


def save_bar(df, x, y, title, path, xlabel=None, ylabel=None, rotation=30):
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df, x=x, y=y, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    ax.tick_params(axis="x", rotation=rotation)
    fig.tight_layout()
    path = Path(path)
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_line(df, x, y, title, path, xlabel=None, ylabel=None):
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(data=df, x=x, y=y, ax=ax, marker="o")
    ax.set_title(title)
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    fig.tight_layout()
    path = Path(path)
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_hist(df, x, title, path, xlabel=None):
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(data=df, x=x, kde=True, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel or x)
    fig.tight_layout()
    path = Path(path)
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_scatter(df, x, y, title, path, xlabel=None, ylabel=None):
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=df, x=x, y=y, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    fig.tight_layout()
    path = Path(path)
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150)
    plt.close(fig)
