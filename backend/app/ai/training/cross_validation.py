"""
Cross-Validation Engine.

Supports K-Fold, Stratified K-Fold, and Time Series Split
with unified scoring output.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.base import BaseEstimator
from sklearn.model_selection import (
    KFold,
    StratifiedKFold,
    TimeSeriesSplit,
    cross_validate,
)

from app.exceptions import ValidationError

logger = logging.getLogger(__name__)

_CLASSIFICATION_METRICS = ["accuracy", "f1_weighted", "roc_auc_ovr_weighted", "precision_weighted", "recall_weighted"]
_REGRESSION_METRICS = ["r2", "neg_mean_absolute_error", "neg_mean_squared_error"]


class CrossValidator:
    """Unified cross-validation with multiple strategies."""

    @staticmethod
    def _get_splitter(strategy: str, n_splits: int) -> Any:
        if strategy == "kfold":
            return KFold(n_splits=n_splits, shuffle=True, random_state=42)
        if strategy == "stratified_kfold":
            return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        if strategy == "timeseries":
            return TimeSeriesSplit(n_splits=n_splits)
        raise ValidationError(f"Unknown CV strategy: {strategy}")

    @classmethod
    def run(
        cls,
        estimator: BaseEstimator,
        X: Any,
        y: Any,
        model_type: str = "classification",
        strategy: str = "stratified_kfold",
        n_splits: int = 5,
    ) -> dict[str, Any]:
        """
        Run cross-validation and return aggregated scores.

        Returns:
            Dict with mean/std for each metric and per-fold scores.
        """
        splitter = cls._get_splitter(strategy, n_splits)
        scoring = _CLASSIFICATION_METRICS if model_type == "classification" else _REGRESSION_METRICS

        try:
            cv_results = cross_validate(
                estimator, X, y,
                cv=splitter,
                scoring=scoring,
                return_train_score=True,
                n_jobs=-1,
            )
        except Exception as exc:
            logger.warning("CV failed with full scoring; falling back. Error: %s", exc)
            fallback = "accuracy" if model_type == "classification" else "r2"
            cv_results = cross_validate(estimator, X, y, cv=splitter, scoring=fallback, n_jobs=-1)

        summary: dict[str, Any] = {"strategy": strategy, "n_splits": n_splits}
        for key, values in cv_results.items():
            if key.startswith("test_") or key.startswith("train_"):
                metric = key.replace("neg_", "")
                summary[f"{metric}_mean"] = round(float(np.mean(np.abs(values))), 4)
                summary[f"{metric}_std"] = round(float(np.std(np.abs(values))), 4)
                summary[f"{metric}_scores"] = [round(float(abs(v)), 4) for v in values]

        logger.info("CV complete (%s, %d folds): %s", strategy, n_splits, {k: v for k, v in summary.items() if "_mean" in k})
        return summary
