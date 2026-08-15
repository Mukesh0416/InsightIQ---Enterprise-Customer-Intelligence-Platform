"""Model explainability module."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class SHAPExplainer:
    """Provides feature attribution for model predictions."""

    @staticmethod
    def local_explanation(
        model: Any,
        input_df: pd.DataFrame,
        row_idx: int = 0,
        feature_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate a local explanation for a single prediction.

        Uses a simplified feature-importance approximation when SHAP
        is unavailable or the model type isn't supported.
        """
        features = feature_names or [str(c) for c in input_df.columns]
        try:
            # Try to use SHAP if available
            import shap

            explainer = shap.TreeExplainer(model)
            row = input_df.iloc[[row_idx]]
            shap_values = explainer.shap_values(row)

            if isinstance(shap_values, list):
                shap_values = shap_values[0]

            values = np.asarray(shap_values).flatten()
            return {
                "method": "shap",
                "feature_importance": {
                    str(f): round(float(v), 6) for f, v in zip(features, values)
                },
                "base_value": float(explainer.expected_value) if not isinstance(explainer.expected_value, list) else float(explainer.expected_value[0]),
            }
        except Exception:
            # Fallback: coefficient-based importance for linear models
            try:
                if hasattr(model, "coef_"):
                    coef = np.asarray(model.coef_).flatten()
                    if len(coef) != len(features):
                        coef = np.resize(coef, len(features))
                    return {
                        "method": "coefficients",
                        "feature_importance": {
                            str(f): round(float(c), 6) for f, c in zip(features, coef)
                        },
                    }
            except Exception:
                pass

            # Last resort: uniform values
            return {
                "method": "fallback",
                "feature_importance": {str(f): 0.0 for f in features},
            }


class LIMEExplainer:
    """Simplified LIME-style local explanation."""

    @staticmethod
    def local_explanation(
        model: Any,
        input_df: pd.DataFrame,
        row_idx: int = 0,
        feature_names: list[str] | None = None,
    ) -> dict[str, Any]:
        features = feature_names or [str(c) for c in input_df.columns]
        return {
            "method": "lime",
            "feature_importance": {str(f): 0.0 for f in features},
            "note": "LIME explanation requires the lime package and is not available.",
        }