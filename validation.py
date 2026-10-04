"""CSV validation and deterministic cleaning for VyapaarIQ."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = ("Date", "Item_Name", "Category", "Amount_INR")
MAX_FILE_BYTES = 10 * 1024 * 1024


@dataclass
class ValidationResult:
    """Validation outcome and a cleaned dataframe suitable for analysis."""

    valid: bool
    cleaned_data: pd.DataFrame = field(default_factory=pd.DataFrame)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rows_uploaded: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    date_range: str = "Unavailable"
    categories_detected: int = 0


def validate_and_clean_csv(source: Any, max_file_bytes: int = MAX_FILE_BYTES) -> ValidationResult:
    """Read, validate, and clean CSV data without mutating the source object."""
    try:
        if hasattr(source, "getvalue"):
            raw = source.getvalue()
        elif isinstance(source, bytes):
            raw = source
        else:
            raw = source.read()
        if len(raw) > max_file_bytes:
            return ValidationResult(False, errors=[f"This file is larger than the current {max_file_bytes // (1024 * 1024)} MB limit."])
        if not raw.strip():
            return ValidationResult(False, errors=["The CSV file is empty."])
        frame = pd.read_csv(BytesIO(raw))
    except pd.errors.ParserError:
        return ValidationResult(False, errors=["Something went wrong while reading the CSV. Please check its structure."])
    except Exception:
        return ValidationResult(False, errors=["Something went wrong while reading the CSV."])

    result = ValidationResult(valid=False, rows_uploaded=len(frame))
    frame.columns = [str(column).strip() for column in frame.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        result.errors.append(f"Missing required column(s): {', '.join(missing)}.")
        return result
    if frame.empty:
        result.errors.append("The CSV does not contain any rows.")
        return result

    result.duplicate_rows = int(frame.duplicated().sum())
    if result.duplicate_rows:
        result.warnings.append(f"{result.duplicate_rows} duplicate row(s) were removed.")

    cleaned = frame.copy()
    cleaned["Date"] = pd.to_datetime(cleaned["Date"], errors="coerce", format="mixed")
    cleaned["Amount_INR"] = pd.to_numeric(
        cleaned["Amount_INR"].astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False).str.strip(),
        errors="coerce",
    )
    cleaned["Item_Name"] = cleaned["Item_Name"].astype("string").str.strip()
    cleaned["Category"] = cleaned["Category"].astype("string").str.strip()
    invalid_mask = (
        cleaned["Date"].isna()
        | cleaned["Amount_INR"].isna()
        | (cleaned["Amount_INR"] < 0)
        | cleaned["Item_Name"].isna()
        | cleaned["Category"].isna()
        | cleaned["Item_Name"].eq("")
        | cleaned["Category"].eq("")
    )
    invalid_count = int(invalid_mask.sum())
    if invalid_count:
        result.warnings.append(f"{invalid_count} unusable row(s) were excluded from analysis.")
    cleaned = cleaned.loc[~invalid_mask].drop_duplicates().reset_index(drop=True)
    result.valid_rows = len(cleaned)
    result.invalid_rows = result.rows_uploaded - result.valid_rows
    result.categories_detected = int(cleaned["Category"].nunique()) if not cleaned.empty else 0
    if cleaned.empty:
        result.errors.append("No usable rows remain after validation. Check dates, categories, item names, and Amount_INR values.")
        return result
    start = cleaned["Date"].min().strftime("%d %b %Y")
    end = cleaned["Date"].max().strftime("%d %b %Y")
    result.date_range = start if start == end else f"{start} - {end}"
    result.cleaned_data = cleaned
    result.valid = True
    return result