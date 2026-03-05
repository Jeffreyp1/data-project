from __future__ import annotations

import os
import uuid
from typing import Optional

import pandas as pd


def load_legacy_csv(csv_path: str) -> pd.DataFrame:
    """
    Load a messy legacy business CSV into a DataFrame.

    Intended behavior:
    - Read CSV with robust defaults (encoding, separators, bad lines)
    - Preserve raw columns for traceability
    - Return a DataFrame for subsequent cleaning
    """
    # TODO: implement robust CSV loading
    return pd.DataFrame()


def clean_legacy_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform the legacy data into a migration-ready shape.

    Intended behavior (examples):
    - Normalize headers (trim, snake_case, dedupe)
    - Coerce datatypes (dates, numbers)
    - Standardize codes (country, currency, units)
    - Handle missing values and obvious outliers
    - Create derived fields required by target SAP structures
    - Return a cleaned DataFrame
    """
    # TODO: implement pandas cleaning pipeline
    return df


def write_clean_excel(
    df: pd.DataFrame,
    output_dir: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    """
    Write the cleaned DataFrame to an Excel file in `outputs/`.

    Intended behavior:
    - Choose output directory (default: project `outputs/`)
    - Generate a unique filename if none provided
    - Write one or more worksheets (clean data, metadata, etc.)
    - Return absolute path to written Excel file
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    resolved_output_dir = output_dir or os.path.join(base_dir, "outputs")
    os.makedirs(resolved_output_dir, exist_ok=True)

    resolved_filename = filename or f"cleaned_{uuid.uuid4().hex}.xlsx"
    out_path = os.path.join(resolved_output_dir, resolved_filename)

    # TODO: actually write excel via pandas/openpyxl
    return out_path

