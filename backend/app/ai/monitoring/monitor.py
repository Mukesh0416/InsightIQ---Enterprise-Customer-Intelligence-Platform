"""Model monitoring and operational metrics."""

from __future__ import annotations

from typing import Any


class ModelMonitor:
    """Computes operational monitoring metrics for deployed models."""

    @staticmethod
    def compute_operational_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
        """Compute latency, error rate, and throughput metrics from prediction records."""
        total = len(records)
        if total == 0:
            return {
                "total_predictions": 0,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "error_rate": 0.0,
                "failure_count": 0,
                "throughput_per_minute": 0.0,
            }

        latencies = [r.get("latency_ms", 0.0) or 0.0 for r in records]
        failures = [r for r in records if r.get("status") == "failed"]
        failure_count = len(failures)
        error_rate = failure_count / total if total else 0.0

        sorted_lat = sorted(latencies)
        p95_idx = min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)

        return {
            "total_predictions": total,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
            "p95_latency_ms": round(sorted_lat[p95_idx], 2) if sorted_lat else 0.0,
            "max_latency_ms": round(max(latencies), 2) if latencies else 0.0,
            "error_rate": round(error_rate, 4),
            "failure_count": failure_count,
            "throughput_per_minute": round(total / 60.0, 2),
        }

    @staticmethod
    def retraining_recommendation(
        drift_score: float,
        failure_rate: float,
        accuracy_degradation: float,
        days_since_training: int,
    ) -> dict[str, Any]:
        """Generate a retraining recommendation based on monitoring signals."""
        score = 0.0
        reasons: list[str] = []

        if drift_score > 0.1:
            score += 0.4
            reasons.append(f"Data drift detected (score={drift_score:.2f})")
        if failure_rate > 0.05:
            score += 0.3
            reasons.append(f"High failure rate ({failure_rate:.1%})")
        if accuracy_degradation > 0.05:
            score += 0.2
            reasons.append(f"Accuracy degradation ({accuracy_degradation:.1%})")
        if days_since_training > 30:
            score += 0.1
            reasons.append(f"Model is {days_since_training} days old")

        return {
            "needs_retraining": score >= 0.4,
            "retraining_score": round(min(score, 1.0), 4),
            "reasons": reasons,
            "recommendation": "Retrain model" if score >= 0.4 else "Model is healthy",
        }