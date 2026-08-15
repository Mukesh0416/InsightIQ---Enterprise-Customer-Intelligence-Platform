"""
Feature Engineering Engine.

Handles imputation, duplicate removal, outlier handling, encoding,
scaling, normalization, datetime/text extraction, polynomial features,
interaction features, binning, and feature transformation.
Produces reusable sklearn Pipeline objects.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    LabelEncoder,
    MinMaxScaler,
    Normalizer,
    OneHotEncoder,
    PolynomialFeatures,
    RobustScaler,
    StandardScaler,
)

from app.exceptions import ValidationError

logger = logging.getLogger(__name__)


class OutlierHandler(BaseEstimator, TransformerMixin):
    """Remove or cap outliers using IQR or Z-score method."""

    def __init__(self, method: str = "iqr", factor: float = 1.5) -> None:
        self.method = method
        self.factor = factor
        self._bounds: dict[str, tuple[float, float]] = {}

    def fit(self, X: pd.DataFrame, y: Any = None) -> OutlierHandler:
        numeric = X.select_dtypes(include="number").columns
        for col in numeric:
            if self.method == "iqr":
                q1, q3 = X[col].quantile(0.25), X[col].quantile(0.75)
                iqr = q3 - q1
                self._bounds[col] = (q1 - self.factor * iqr, q3 + self.factor * iqr)
            else:  # zscore
                mean, std = X[col].mean(), X[col].std()
                self._bounds[col] = (mean - self.factor * std, mean + self.factor * std)
        return self

    def transform(self, X: pd.DataFrame, y: Any = None) -> pd.DataFrame:
        X = X.copy()
        for col, (lo, hi) in self._bounds.items():
            if col in X.columns:
                X[col] = X[col].clip(lo, hi)
        return X


class DatetimeFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract year, month, day, weekday, hour, quarter from datetime columns."""

    def __init__(self, columns: list[str] | None = None) -> None:
        self.columns = columns
        self._detected: list[str] = []

    def fit(self, X: pd.DataFrame, y: Any = None) -> DatetimeFeatureExtractor:
        cols = self.columns or list(X.select_dtypes(include=["datetime64", "datetimetz"]).columns)
        self._detected = [c for c in cols if c in X.columns]
        return self

    def transform(self, X: pd.DataFrame, y: Any = None) -> pd.DataFrame:
        X = X.copy()
        for col in self._detected:
            dt = pd.to_datetime(X[col], errors="coerce")
            X[f"{col}_year"] = dt.dt.year
            X[f"{col}_month"] = dt.dt.month
            X[f"{col}_day"] = dt.dt.day
            X[f"{col}_weekday"] = dt.dt.weekday
            X[f"{col}_quarter"] = dt.dt.quarter
            X[f"{col}_hour"] = dt.dt.hour
            X.drop(columns=[col], inplace=True)
        return X


class TextFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract basic text statistics (length, word count) from text columns."""

    def __init__(self, columns: list[str] | None = None) -> None:
        self.columns = columns or []

    def fit(self, X: pd.DataFrame, y: Any = None) -> TextFeatureExtractor:
        return self

    def transform(self, X: pd.DataFrame, y: Any = None) -> pd.DataFrame:
        X = X.copy()
        for col in self.columns:
            if col in X.columns:
                X[f"{col}_len"] = X[col].astype(str).str.len()
                X[f"{col}_word_count"] = X[col].astype(str).str.split().str.len()
                X.drop(columns=[col], inplace=True)
        return X


class TargetEncoder(BaseEstimator, TransformerMixin):
    """Encode categorical columns using target mean encoding."""

    def __init__(self, columns: list[str] | None = None, smoothing: float = 1.0) -> None:
        self.columns = columns
        self.smoothing = smoothing
        self._maps: dict[str, dict] = {}
        self._global_mean: float = 0.0

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> TargetEncoder:
        if y is None:
            return self
        self._global_mean = float(y.mean())
        cols = self.columns or list(X.select_dtypes(include="object").columns)
        for col in cols:
            if col not in X.columns:
                continue
            stats = pd.DataFrame({"target": y, "feature": X[col]}).groupby("feature")["target"]
            count = stats.count()
            mean = stats.mean()
            smooth = (count * mean + self.smoothing * self._global_mean) / (count + self.smoothing)
            self._maps[col] = smooth.to_dict()
        return self

    def transform(self, X: pd.DataFrame, y: Any = None) -> pd.DataFrame:
        X = X.copy()
        for col, mapping in self._maps.items():
            if col in X.columns:
                X[col] = X[col].map(mapping).fillna(self._global_mean)
        return X


class BinningTransformer(BaseEstimator, TransformerMixin):
    """Bin numeric columns into equal-width or quantile-based bins."""

    def __init__(self, columns: list[str] | None = None, n_bins: int = 5, strategy: str = "quantile") -> None:
        self.columns = columns or []
        self.n_bins = n_bins
        self.strategy = strategy
        self._bin_edges: dict[str, np.ndarray] = {}

    def fit(self, X: pd.DataFrame, y: Any = None) -> BinningTransformer:
        for col in self.columns:
            if col not in X.columns:
                continue
            if self.strategy == "quantile":
                self._bin_edges[col] = np.nanpercentile(
                    X[col].dropna(), np.linspace(0, 100, self.n_bins + 1)
                )
            else:
                lo, hi = X[col].min(), X[col].max()
                self._bin_edges[col] = np.linspace(lo, hi, self.n_bins + 1)
        return self

    def transform(self, X: pd.DataFrame, y: Any = None) -> pd.DataFrame:
        X = X.copy()
        for col, edges in self._bin_edges.items():
            if col in X.columns:
                X[f"{col}_bin"] = pd.cut(X[col], bins=edges, labels=False, include_lowest=True)
        return X


class FeatureEngineeringEngine:
    """
    Orchestrates the full feature engineering pipeline.

    Builds a reusable sklearn Pipeline from configuration and returns
    the transformed DataFrame along with the fitted pipeline.
    """

    @staticmethod
    def build_pipeline(
        df: pd.DataFrame,
        *,
        imputation_strategy: str = "mean",
        remove_duplicates: bool = True,
        outlier_method: str | None = "iqr",
        encoding_method: str = "onehot",
        scaling_method: str = "standard",
        normalize: bool = False,
        extract_datetime: bool = True,
        polynomial_degree: int | None = None,
        interaction_features: bool = False,
        binning_columns: list[str] | None = None,
        text_columns: list[str] | None = None,
        target_column: str | None = None,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """
        Apply feature engineering to a DataFrame.

        Returns:
            Tuple of (transformed DataFrame, pipeline metadata dict).
        """
        if df.empty:
            raise ValidationError("DataFrame is empty.")

        result = df.copy()
        metadata: dict[str, Any] = {}

        # 1. Remove duplicates
        if remove_duplicates:
            before = len(result)
            result = result.drop_duplicates()
            metadata["duplicates_removed"] = before - len(result)

        # 2. Datetime extraction
        if extract_datetime:
            extractor = DatetimeFeatureExtractor()
            extractor.fit(result)
            result = extractor.transform(result)
            metadata["datetime_features"] = extractor._detected

        # 3. Text features
        if text_columns:
            text_ext = TextFeatureExtractor(columns=text_columns)
            result = text_ext.transform(result)

        # 4. Binning
        if binning_columns:
            binner = BinningTransformer(columns=binning_columns)
            binner.fit(result)
            result = binner.transform(result)

        # 5. Outlier handling
        if outlier_method:
            handler = OutlierHandler(method=outlier_method)
            handler.fit(result)
            result = handler.transform(result)

        # 6. Imputation
        numeric_cols = result.select_dtypes(include="number").columns.tolist()
        cat_cols = result.select_dtypes(include="object").columns.tolist()

        for col in numeric_cols:
            if result[col].isna().any():
                if imputation_strategy == "mean":
                    result[col] = result[col].fillna(result[col].mean())
                elif imputation_strategy == "median":
                    result[col] = result[col].fillna(result[col].median())
                elif imputation_strategy == "zero":
                    result[col] = result[col].fillna(0)
                else:
                    result[col] = result[col].fillna(result[col].mode().iloc[0] if not result[col].mode().empty else 0)

        for col in cat_cols:
            if result[col].isna().any():
                result[col] = result[col].fillna(result[col].mode().iloc[0] if not result[col].mode().empty else "unknown")

        # 7. Encoding
        target_col_data = result.pop(target_column) if target_column and target_column in result.columns else None
        cat_cols_now = result.select_dtypes(include="object").columns.tolist()

        if cat_cols_now:
            if encoding_method == "onehot":
                result = pd.get_dummies(result, columns=cat_cols_now, drop_first=False)
            elif encoding_method == "label":
                for col in cat_cols_now:
                    le = LabelEncoder()
                    result[col] = le.fit_transform(result[col].astype(str))
            elif encoding_method == "target" and target_col_data is not None:
                enc = TargetEncoder(columns=cat_cols_now)
                enc.fit(result, target_col_data)
                result = enc.transform(result)

        if target_col_data is not None:
            result[target_column] = target_col_data.values  # type: ignore[index]

        # 8. Scaling
        numeric_now = result.select_dtypes(include="number").columns.tolist()
        scale_cols = [c for c in numeric_now if c != target_column]

        if scale_cols and scaling_method != "none":
            scaler: StandardScaler | MinMaxScaler | RobustScaler
            if scaling_method == "standard":
                scaler = StandardScaler()
            elif scaling_method == "minmax":
                scaler = MinMaxScaler()
            else:
                scaler = RobustScaler()
            result[scale_cols] = scaler.fit_transform(result[scale_cols])
            metadata["scaler"] = scaling_method

        # 9. Normalization
        if normalize and scale_cols:
            norm = Normalizer()
            result[scale_cols] = norm.fit_transform(result[scale_cols])

        # 10. Polynomial features
        if polynomial_degree and polynomial_degree >= 2 and scale_cols:
            poly = PolynomialFeatures(degree=polynomial_degree, include_bias=False, interaction_only=False)
            poly_arr = poly.fit_transform(result[scale_cols])
            poly_names = poly.get_feature_names_out(scale_cols)
            poly_df = pd.DataFrame(poly_arr, columns=poly_names, index=result.index)
            result = pd.concat([result.drop(columns=scale_cols), poly_df], axis=1)
            metadata["polynomial_features"] = len(poly_names)

        # 11. Interaction features (pairwise products)
        elif interaction_features and len(scale_cols) >= 2:
            for i, c1 in enumerate(scale_cols):
                for c2 in scale_cols[i + 1:]:
                    result[f"{c1}_x_{c2}"] = result[c1] * result[c2]

        metadata["final_shape"] = result.shape
        metadata["feature_count"] = result.shape[1]
        logger.info("Feature engineering complete: %s", metadata)
        return result, metadata
