"""Load utilities (thin wrappers around data_loading)."""
from __future__ import annotations

from .data_loading import detect_csv, load_raw

__all__ = ["detect_csv", "load_raw"]
