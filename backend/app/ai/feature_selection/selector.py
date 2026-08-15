"""
Feature Selection Engine.

Implements correlation-based, variance threshold, SelectKBest, RFE,
tree-based importance, mutual information, and optional PCA selection.
Generates ranked feature lists.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import (
    RFE,
    SelectKBest,
    VarianceThreshold,
    f_classif,
    f_regression,
    mutual_info_classif,
    mutual_info_regression,
)

from app.exceptions import ValidationError

logger = logging.getLogger(__name__)


class FeatureSelector:
    """
    Multi-strategy feature selector with unified ranking output.

    All methods return a dict with keys:
        selected_features, feature_ranking, method, metadata
    """

    @staticmethod
    def variance_threshold(
        df: pd.DataFrame,
        threshold: float = 0.0,
    ) -> dict[str, Any]:
        """Remove features with variance below threshold."""
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            raise ValidationError("No numeric features for variance threshold.")
        sel = VarianceThreshold(threshold=threshold)
        sel.fit(numeric)
        variances = dict(zip(numeric.columns, sel.variances_))
        selected = [c for c, v in variances.items() if v > threshold]
        ranking = sorted(variances.items(), key=lambda x: x[1], reverse=True)
        return {
            "selected_features": selected,
            "feature_ranking": [{"feature": f, "score": round(s, 6)} for f, s in ranking],
            "method": "variance_threshold",
            "metadata": {"threshold": threshold, "n_selected": len(selected)},
        }

    @staticmethod
    def correlation_based(
        df: pd.DataFrame,
        target: pd.Series,
        threshold: float = 0.95,
    ) -> dict[str, Any]:
        """Remove highly correlated features; keep those most correlated with target."""
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            raise ValidationError("No numeric features for correlation selection.")

        corr_matrix = numeric.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = {col for col in upper.columns if any(upper[col] > threshold)}

        remaining = [c for c in numeric.columns if c not in to_drop]
        target_corr = numeric[remaining].corrwith(target).abs()
        ranking = target_corr.sort_values(ascending=False)

        return {
            "selected_features": remaining,
            "feature_ranking": [{"feature": f, "score": round(s, 6)} for f, s in ranking.items()],
            "method": "correlation",
            "metadata": {"dropped_correlated": list(to_drop), "threshold": threshold},
        }

    @staticmethod
    def select_k_best(
        df: pd.DataFrame,
        target: pd.Series,
        k: int = 10,
        model_type: str = "classification",
    ) -> dict[str, Any]:
        """Select top-k features using ANOVA F-test."""
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            raise ValidationError("No numeric features for SelectKBest.")
        k = min(k, numeric.shape[1])
        score_func = f_classif if model_type == "classification" else f_regression
        sel = SelectKBest(score_func=score_func, k=k)
        sel.fit(numeric, target)
        scores = dict(zip(numeric.columns, sel.scores_))
        selected = [c for c, s in scores.items() if not np.isnan(s)]
        selected = sorted(selected, key=lambda c: scores[c], reverse=True)[:k]
        ranking = sorted(scores.items(), key=lambda x: x[1] if not np.isnan(x[1]) else 0, reverse=True)
        return {
            "selected_features": selected,
            "feature_ranking": [{"feature": f, "score": round(float(s), 6)} for f, s in ranking],
            "method": "select_k_best",
            "metadata": {"k": k, "score_func": score_func.__name__},
        }

    @staticmethod
    def rfe(
        df: pd.DataFrame,
        target: pd.Series,
        n_features: int = 10,
        model_type: str = "classification",
    ) -> dict[str, Any]:
        """Recursive Feature Elimination using a Random Forest estimator."""
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            raise ValidationError("No numeric features for RFE.")
        n_features = min(n_features, numeric.shape[1])
        estimator = (
            RandomForestClassifier(n_estimators=50, random_state=42)
            if model_type == "classification"
            else RandomForestRegressor(n_estimators=50, random_state=42)
        )
        selector = RFE(estimator=estimator, n_features_to_select=n_features, step=1)
        selector.fit(numeric, target)
        ranking = dict(zip(numeric.columns, selector.ranking_))
        selected = [c for c, r in ranking.items() if r == 1]
        sorted_ranking = sorted(ranking.items(), key=lambda x: x[1])
        return {
            "selected_features": selected,
            "feature_ranking": [{"feature": f, "rank": r} for f, r in sorted_ranking],
            "method": "rfe",
            "metadata": {"n_features": n_features},
        }

    @staticmethod
    def tree_importance(
        df: pd.DataFrame,
        target: pd.Series,
        threshold: float = 0.01,
        model_type: str = "classification",
    ) -> dict[str, Any]:
        """Select features by tree-based feature importance."""
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            raise ValidationError("No numeric features for tree importance.")
        model = (
            RandomForestClassifier(n_estimators=100, random_state=42)
            if model_type == "classification"
            else RandomForestRegressor(n_estimators=100, random_state=42)
        )
        model.fit(numeric, target)
        importances = dict(zip(numeric.columns, model.feature_importances_))
        selected = [f for f, imp in importances.items() if imp >= threshold]
        ranking = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        return {
            "selected_features": selected,
            "feature_ranking": [{"feature": f, "score": round(s, 6)} for f, s in ranking],
            "method": "tree_importance",
            "metadata": {"threshold": threshold},
        }

    @staticmethod
    def mutual_information(
        df: pd.DataFrame,
        target: pd.Series,
        k: int = 10,
        model_type: str = "classification",
    ) -> dict[str, Any]:
        """Select features by mutual information score."""
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            raise ValidationError("No numeric features for mutual information.")
        k = min(k, numeric.shape[1])
        mi_func = mutual_info_classif if model_type == "classification" else mutual_info_regression
        scores = mi_func(numeric, target, random_state=42)
        score_map = dict(zip(numeric.columns, scores))
        ranking = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
        selected = [f for f, _ in ranking[:k]]
        return {
            "selected_features": selected,
            "feature_ranking": [{"feature": f, "score": round(s, 6)} for f, s in ranking],
            "method": "mutual_information",
            "metadata": {"k": k},
        }

    @staticmethod
    def pca_reduction(
        df: pd.DataFrame,
        n_components: int | None = None,
        variance_ratio: float = 0.95,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Reduce dimensionality with PCA."""
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            raise ValidationError("No numeric features for PCA.")
        n = n_components or min(numeric.shape[1], numeric.shape[0] - 1)
        pca = PCA(n_components=n, random_state=42)
        transformed = pca.fit_transform(numeric)
        cols = [f"pc_{i + 1}" for i in range(transformed.shape[1])]
        pca_df = pd.DataFrame(transformed, columns=cols, index=df.index)
        cumvar = float(np.cumsum(pca.explained_variance_ratio_)[-1])
        return pca_df, {
            "n_components": n,
            "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
            "cumulative_variance": round(cumvar, 4),
            "method": "pca",
        }

    @classmethod
    def select(
        cls,
        df: pd.DataFrame,
        target: pd.Series | None,
        method: str = "tree_importance",
        model_type: str = "classification",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Dispatch to the appropriate selection method."""
        dispatch = {
            "variance_threshold": lambda: cls.variance_threshold(df, **kwargs),
            "correlation": lambda: cls.correlation_based(df, target, **kwargs),  # type: ignore[arg-type]
            "select_k_best": lambda: cls.select_k_best(df, target, model_type=model_type, **kwargs),  # type: ignore[arg-type]
            "rfe": lambda: cls.rfe(df, target, model_type=model_type, **kwargs),  # type: ignore[arg-type]
            "tree_importance": lambda: cls.tree_importance(df, target, model_type=model_type, **kwargs),  # type: ignore[arg-type]
            "mutual_information": lambda: cls.mutual_information(df, target, model_type=model_type, **kwargs),  # type: ignore[arg-type]
        }
        if method not in dispatch:
            raise ValidationError(f"Unknown feature selection method: {method}")
        return dispatch[method]()
