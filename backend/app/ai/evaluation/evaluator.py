"""
Model Evaluation Engine.

Computes classification, regression, and clustering metrics.
Generates comparison reports across algorithms.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    calinski_harabasz_score,
    confusion_matrix,
    classification_report,
    davies_bouldin_score,
    f1_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Compute evaluation metrics for all model types."""

    @staticmethod
    def classification_metrics(
        y_true: Any,
        y_pred: Any,
        y_prob: Any = None,
        labels: list | None = None,
    ) -> dict[str, Any]:
        """Compute full classification metric suite."""
        is_binary = len(np.unique(y_true)) == 2
        avg = "binary" if is_binary else "weighted"

        metrics: dict[str, Any] = {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "precision": round(float(precision_score(y_true, y_pred, average=avg, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, average=avg, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_true, y_pred, average=avg, zero_division=0)), 4),
        }

        if y_prob is not None:
            try:
                if is_binary:
                    prob = y_prob[:, 1] if y_prob.ndim == 2 else y_prob
                    metrics["roc_auc"] = round(float(roc_auc_score(y_true, prob)), 4)
                    metrics["pr_auc"] = round(float(average_precision_score(y_true, prob)), 4)
                else:
                    metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_prob, multi_class="ovr", average="weighted")), 4)
            except Exception as exc:
                logger.warning("Could not compute AUC: %s", exc)

        cm = confusion_matrix(y_true, y_pred, labels=labels)
        metrics["confusion_matrix"] = cm.tolist()
        metrics["classification_report"] = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        return metrics

    @staticmethod
    def regression_metrics(y_true: Any, y_pred: Any) -> dict[str, Any]:
        """Compute full regression metric suite."""
        mae = float(mean_absolute_error(y_true, y_pred))
        mse = float(mean_squared_error(y_true, y_pred))
        try:
            mape = float(mean_absolute_percentage_error(y_true, y_pred))
        except Exception:
            mape = float("nan")
        return {
            "mae": round(mae, 4),
            "mse": round(mse, 4),
            "rmse": round(float(np.sqrt(mse)), 4),
            "r2": round(float(r2_score(y_true, y_pred)), 4),
            "mape": round(mape, 4) if not np.isnan(mape) else None,
        }

    @staticmethod
    def clustering_metrics(X: Any, labels: Any) -> dict[str, Any]:
        """Compute clustering evaluation metrics."""
        unique_labels = np.unique(labels)
        if len(unique_labels) < 2:
            return {"error": "Need at least 2 clusters for evaluation."}
        try:
            sil = round(float(silhouette_score(X, labels, sample_size=min(5000, len(X)))), 4)
        except Exception:
            sil = None
        try:
            db = round(float(davies_bouldin_score(X, labels)), 4)
        except Exception:
            db = None
        try:
            ch = round(float(calinski_harabasz_score(X, labels)), 4)
        except Exception:
            ch = None
        return {
            "silhouette_score": sil,
            "davies_bouldin_index": db,
            "calinski_harabasz_score": ch,
            "n_clusters": int(len(unique_labels)),
            "cluster_sizes": {str(k): int(v) for k, v in zip(*np.unique(labels, return_counts=True))},
        }

    @classmethod
    def compare_models(cls, results: list[dict[str, Any]], model_type: str) -> dict[str, Any]:
        """
        Generate a comparison report across multiple algorithm results.

        Args:
            results: List of dicts with keys: algorithm, metrics.
            model_type: classification | regression | clustering.

        Returns:
            Ranked comparison with best model identified.
        """
        if not results:
            return {"comparison": [], "best_model": None}

        primary_metric = {
            "classification": "f1_score",
            "regression": "r2",
            "clustering": "silhouette_score",
        }.get(model_type, "f1_score")

        ranked = sorted(
            results,
            key=lambda r: r.get("metrics", {}).get(primary_metric, -999) or -999,
            reverse=True,
        )
        return {
            "comparison": ranked,
            "best_model": ranked[0]["algorithm"] if ranked else None,
            "primary_metric": primary_metric,
            "n_models": len(ranked),
        }
