"""Shared paths and configuration for supply chain analysis."""
from __future__ import annotations

from pathlib import Path

CASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = CASE_DIR / "reports"
VISUALS_DIR = CASE_DIR / "visuals"
