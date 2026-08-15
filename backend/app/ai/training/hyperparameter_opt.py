"""
Hyperparameter Optimization.

Supports Grid Search, Random Search, and Optuna-based Bayesian optimization
with configurable search spaces per algorithm.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.base import BaseEstimator
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, StratifiedKFold, KFold

from app.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Default search spaces per algorithm
DEFAULT_SEARCH_SPACES: dict[str, dict[str, Any]] = {
    "random_forest": {"n_estimators": [50, 100, 200], "max_depth": [None, 5, 10, 20], "min_samples_split": [2, 5, 10]},
    "random_forest_regressor": {"n_estimators": [50, 100, 200], "max_depth": [None, 5, 10, 20]},
    "xgboost": {"n_estimators": [50, 100, 200], "max_depth": [3, 5, 7], "learning_rate": [0.01, 0.1, 0.3]},
    "xgboost_regressor": {"n_estimators": [50, 100, 200], "max_depth": [3, 5, 7], "learning_rate": [0.01, 0.1, 0.3]},
    "lightgbm": {"n_estimators": [50, 100, 200], "num_leaves": [31, 63, 127], "learning_rate": [0.01, 0.1, 0.3]},
    "lightgbm_regressor": {"n_estimators": [50, 100, 200], "num_leaves": [31, 63, 127]},
    "logistic_regression": {"C": [0.01, 0.1, 1.0, 10.0], "solver": ["lbfgs", "saga"]},
    "ridge": {"alpha": [0.01, 0.1, 1.0, 10.0, 100.0]},
    "lasso": {"alpha": [0.001, 0.01, 0.1, 1.0]},
    "elasticnet": {"alpha": [0.01, 0.1, 1.0], "l1_ratio": [0.2, 0.5, 0.8]},
    "svm": {"C": [0.1, 1.0, 10.0], "kernel": ["rbf", "linear"]},
    "knn": {"n_neighbors": [3, 5, 7, 11], "weights": ["uniform", "distance"]},
    "decision_tree": {"max_depth": [None, 5, 10, 20], "min_samples_split": [2, 5, 10]},
    "gradient_boosting": {"n_estimators": [50, 100], "learning_rate": [0.05, 0.1, 0.2], "max_depth": [3, 5]},
}

OPTUNA_SEARCH_SPACES: dict[str, Any] = {
    "random_forest": lambda t: {
        "n_estimators": t.suggest_int("n_estimators", 50, 300),
        "max_depth": t.suggest_int("max_depth", 3, 20),
        "min_samples_split": t.suggest_int("min_samples_split", 2, 10),
    },
    "xgboost": lambda t: {
        "n_estimators": t.suggest_int("n_estimators", 50, 300),
        "max_depth": t.suggest_int("max_depth", 3, 10),
        "learning_rate": t.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": t.suggest_float("subsample", 0.6, 1.0),
    },
    "lightgbm": lambda t: {
        "n_estimators": t.suggest_int("n_estimators", 50, 300),
        "num_leaves": t.suggest_int("num_leaves", 20, 150),
        "learning_rate": t.suggest_float("learning_rate", 0.01, 0.3, log=True),
    },
    "logistic_regression": lambda t: {
        "C": t.suggest_float("C", 0.001, 100.0, log=True),
    },
    "ridge": lambda t: {"alpha": t.suggest_float("alpha", 0.001, 100.0, log=True)},
    "lasso": lambda t: {"alpha": t.suggest_float("alpha", 0.001, 10.0, log=True)},
}


class HyperparameterOptimizer:
    """Unified hyperparameter optimization interface."""

    @staticmethod
    def grid_search(
        estimator: BaseEstimator,
        X: Any,
        y: Any,
        algorithm: str,
        search_space: dict[str, Any] | None = None,
        cv: int = 5,
        scoring: str | None = None,
        model_type: str = "classification",
    ) -> tuple[BaseEstimator, dict[str, Any]]:
        """Run exhaustive grid search."""
        param_grid = search_space or DEFAULT_SEARCH_SPACES.get(algorithm, {})
        if not param_grid:
            logger.warning("No search space for %s; skipping grid search.", algorithm)
            estimator.fit(X, y)
            return estimator, {}

        cv_splitter = StratifiedKFold(n_splits=cv) if model_type == "classification" else KFold(n_splits=cv)
        gs = GridSearchCV(estimator, param_grid, cv=cv_splitter, scoring=scoring, n_jobs=-1, refit=True)
        gs.fit(X, y)
        logger.info("Grid search best params for %s: %s", algorithm, gs.best_params_)
        return gs.best_estimator_, {"best_params": gs.best_params_, "best_score": gs.best_score_}

    @staticmethod
    def random_search(
        estimator: BaseEstimator,
        X: Any,
        y: Any,
        algorithm: str,
        search_space: dict[str, Any] | None = None,
        n_iter: int = 20,
        cv: int = 5,
        scoring: str | None = None,
        model_type: str = "classification",
    ) -> tuple[BaseEstimator, dict[str, Any]]:
        """Run randomized search."""
        param_dist = search_space or DEFAULT_SEARCH_SPACES.get(algorithm, {})
        if not param_dist:
            estimator.fit(X, y)
            return estimator, {}

        cv_splitter = StratifiedKFold(n_splits=cv) if model_type == "classification" else KFold(n_splits=cv)
        rs = RandomizedSearchCV(
            estimator, param_dist, n_iter=n_iter, cv=cv_splitter,
            scoring=scoring, n_jobs=-1, refit=True, random_state=42,
        )
        rs.fit(X, y)
        logger.info("Random search best params for %s: %s", algorithm, rs.best_params_)
        return rs.best_estimator_, {"best_params": rs.best_params_, "best_score": rs.best_score_}

    @staticmethod
    def optuna_search(
        estimator_factory: Any,
        X: Any,
        y: Any,
        algorithm: str,
        n_trials: int = 50,
        cv: int = 5,
        scoring: str | None = None,
        model_type: str = "classification",
        timeout: int | None = 300,
    ) -> tuple[BaseEstimator, dict[str, Any]]:
        """Run Optuna Bayesian optimization."""
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)
        except ImportError as exc:
            raise ValidationError("optuna is not installed.") from exc

        from sklearn.model_selection import cross_val_score

        space_fn = OPTUNA_SEARCH_SPACES.get(algorithm)
        if space_fn is None:
            logger.warning("No Optuna space for %s; fitting with defaults.", algorithm)
            est = estimator_factory()
            est.fit(X, y)
            return est, {}

        cv_splitter = StratifiedKFold(n_splits=cv) if model_type == "classification" else KFold(n_splits=cv)
        default_scoring = "roc_auc" if model_type == "classification" else "r2"
        score_fn = scoring or default_scoring

        def objective(trial: Any) -> float:
            params = space_fn(trial)
            est = estimator_factory(**params)
            scores = cross_val_score(est, X, y, cv=cv_splitter, scoring=score_fn, n_jobs=-1)
            return float(np.mean(scores))

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials, timeout=timeout, show_progress_bar=False)

        best_params = study.best_params
        best_estimator = estimator_factory(**best_params)
        best_estimator.fit(X, y)
        logger.info("Optuna best params for %s: %s (score=%.4f)", algorithm, best_params, study.best_value)
        return best_estimator, {"best_params": best_params, "best_score": study.best_value, "n_trials": len(study.trials)}

    @classmethod
    def optimize(
        cls,
        estimator_factory: Any,
        X: Any,
        y: Any,
        algorithm: str,
        method: str = "optuna",
        model_type: str = "classification",
        **kwargs: Any,
    ) -> tuple[BaseEstimator, dict[str, Any]]:
        """Dispatch to the configured optimization method."""
        if method == "grid":
            return cls.grid_search(estimator_factory(), X, y, algorithm, model_type=model_type, **kwargs)
        if method == "random":
            return cls.random_search(estimator_factory(), X, y, algorithm, model_type=model_type, **kwargs)
        if method == "optuna":
            return cls.optuna_search(estimator_factory, X, y, algorithm, model_type=model_type, **kwargs)
        raise ValidationError(f"Unknown optimization method: {method}")
