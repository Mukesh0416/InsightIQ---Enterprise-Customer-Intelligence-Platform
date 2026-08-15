"""Data drift detection module."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class DriftDetector:
    """Detects data drift between reference and current datasets."""

    @staticmethod
    def detect_data_drift(
        reference_df: pd.DataFrame,
        current_df: pd.DataFrame,
        threshold: float = 0.1,
    ) -> dict[str, Any]:
        """Compare reference and current feature distributions."""
        feature_drift: dict[str, Any] = {}

        common_cols = [c for c in reference_df.columns if c in current_df.columns]

        for col in common_cols:
            ref = pd.to_numeric(reference_df[col], errors="coerce").dropna()
            cur = pd.to_numeric(current_df[col], errors="coerce").dropna()
            if len(ref) == 0 or len(cur) == 0:
                continue

            # KS test for numeric features
            from scipy import stats

            try:
                ks_stat, ks_p = stats.ks_2samp(ref, cur)
            except Exception:
                ks_stat, ks_p = 0.0, 1.0

            ref_mean = float(ref.mean()) if len(ref) else 0.0
            cur_mean = float(cur.mean()) if len(cur) else 0.0
            magnitude = abs(cur_mean - ref_mean) / max(abs(ref_mean), 1.0)

            feature_drift[str(col)] = {
                "ks_test": {"statistic": round(float(ks_stat), 4), "p_value": round(float(ks_p), 4)},
                "mean_drift": round(magnitude, 4),
                "drift_score": round(max(magnitude, 1.0 - ks_p), 4),
            }

        # Overall drift score
        scores = [v.get("drift_score", 0.0) for v in feature_drift.values()]
        drift_score = float(np.mean(scores)) if scores else 0.0
        drift_detected = drift_score > threshold

        recommendations = []
        if drift_detected:
            drifted_cols = [k for k, v in feature_drift.items() if v.get("drift_score", 0) > threshold]
            recommendations.append(f"Retrain model: {len(drifted_cols)} features show drift: {drifted_cols[:5]}")

        return {
            "drift_detected": drift_detected,
            "drift_score": round(drift_score, 4),
            "feature_drift": feature_drift,
            "recommendations": recommendations,
        }