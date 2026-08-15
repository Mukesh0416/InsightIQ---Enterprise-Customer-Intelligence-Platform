"""Automatic data type detection for dataset columns using pandas."""

from __future__ import annotations

import re
import warnings
from typing import Any

import numpy as np
import pandas as pd

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class TypeDetector:
    """Detects column data types from pandas DataFrame values."""

    @classmethod
    def detect_series_type(cls, series: pd.Series) -> str:
        non_null = series.dropna()
        if len(non_null) == 0:
            return "unknown"

        # UUID
        sample = non_null.astype(str).head(50)
        if sample.apply(lambda v: bool(UUID_PATTERN.match(v))).mean() > 0.9:
            return "uuid"

        # Email
        if sample.apply(lambda v: bool(EMAIL_PATTERN.match(v))).mean() > 0.8:
            return "email"

        # Phone
        if sample.apply(lambda v: bool(PHONE_PATTERN.match(v))).mean() > 0.8:
            return "phone"

        # Datetime
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Could not infer format.*", category=UserWarning)
                pd.to_datetime(non_null.head(100), errors="coerce")
            infer_dtype = getattr(pd.api.types, "infer_dtype", None)
            if infer_dtype is not None:
                inferred = infer_dtype(non_null, skipna=True)
            else:
                inferred = pd.api.types.infer_type(non_null)
            if "datetime" in str(inferred) or inferred in {"datetime", "datetime64", "date"}:
                return "datetime"
        except (ValueError, TypeError, AttributeError):
            pass

        # Numeric
        if pd.api.types.is_integer_dtype(non_null):
            return "integer"
        if pd.api.types.is_float_dtype(non_null):
            return "float"
        if pd.api.types.is_bool_dtype(non_null):
            return "boolean"

        # Try numeric coercion
        coerced = pd.to_numeric(non_null, errors="coerce")
        if coerced.notna().mean() > 0.9:
            if (coerced % 1 == 0).all():
                return "integer"
            return "float"

        # Categorical if low cardinality
        unique_ratio = non_null.nunique() / max(len(non_null), 1)
        if unique_ratio < 0.1:
            return "categorical"

        # Date detection
        try:
            if isinstance(non_null.iloc[0], str) and re.match(
                r"^\d{4}-\d{2}-\d{2}$", non_null.iloc[0]
            ):
                return "date"
        except (IndexError, AttributeError):
            pass

        return "string"

    @classmethod
    def detect_column_types(cls, df: pd.DataFrame) -> dict[str, str]:
        result: dict[str, str] = {}
        for col in df.columns:
            result[str(col)] = cls.detect_series_type(df[col])
        return result

    @classmethod
    def infer_currency(cls, series: pd.Series) -> bool:
        sample = series.dropna().astype(str)
        if len(sample) == 0:
            return False
        currency_pattern = re.compile(r"^[\$€£¥]\s?\d[\d,]*(\.\d{2})?$")
        return sample.apply(lambda v: bool(currency_pattern.match(v))).mean() > 0.8

    @classmethod
    def detect_outliers_iqr(cls, series: pd.Series) -> int:
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if len(numeric) < 4:
            return 0
        q1 = numeric.quantile(0.25)
        q3 = numeric.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            return 0
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return int(((numeric < lower) | (numeric > upper)).sum())