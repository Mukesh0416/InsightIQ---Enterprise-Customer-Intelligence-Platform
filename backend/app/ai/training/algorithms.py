"""
Algorithm Registry.

Maps algorithm names to sklearn-compatible estimator instances
for classification, regression, and clustering.
"""

from __future__ import annotations

from typing import Any

from sklearn.base import BaseEstimator
from sklearn.ensemble import (
    AdaBoostClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import (
    ElasticNet,
    Lasso,
    LinearRegression,
    LogisticRegression,
    Ridge,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans

from app.exceptions import ValidationError


def _xgb_classifier(**kw: Any) -> BaseEstimator:
    from xgboost import XGBClassifier
    return XGBClassifier(eval_metric="logloss", random_state=42, **kw)


def _xgb_regressor(**kw: Any) -> BaseEstimator:
    from xgboost import XGBRegressor
    return XGBRegressor(random_state=42, **kw)


def _lgbm_classifier(**kw: Any) -> BaseEstimator:
    from lightgbm import LGBMClassifier
    return LGBMClassifier(random_state=42, verbose=-1, **kw)


def _lgbm_regressor(**kw: Any) -> BaseEstimator:
    from lightgbm import LGBMRegressor
    return LGBMRegressor(random_state=42, verbose=-1, **kw)


def _catboost_classifier(**kw: Any) -> BaseEstimator:
    from catboost import CatBoostClassifier
    return CatBoostClassifier(random_state=42, verbose=0, **kw)


def _catboost_regressor(**kw: Any) -> BaseEstimator:
    from catboost import CatBoostRegressor
    return CatBoostRegressor(random_state=42, verbose=0, **kw)


CLASSIFICATION_REGISTRY: dict[str, Any] = {
    "logistic_regression": lambda **kw: LogisticRegression(max_iter=1000, random_state=42, **kw),
    "decision_tree": lambda **kw: DecisionTreeClassifier(random_state=42, **kw),
    "random_forest": lambda **kw: RandomForestClassifier(
        n_estimators=kw.pop("n_estimators", 100),
        random_state=42,
        **kw,
    ),
    "extra_trees": lambda **kw: ExtraTreesClassifier(
        n_estimators=kw.pop("n_estimators", 100),
        random_state=42,
        **kw,
    ),
    "xgboost": _xgb_classifier,
    "lightgbm": _lgbm_classifier,
    "catboost": _catboost_classifier,
    "gradient_boosting": lambda **kw: GradientBoostingClassifier(random_state=42, **kw),
    "adaboost": lambda **kw: AdaBoostClassifier(random_state=42, **kw),
    "naive_bayes": lambda **kw: GaussianNB(**kw),
    "svm": lambda **kw: SVC(probability=True, random_state=42, **kw),
    "knn": lambda **kw: KNeighborsClassifier(**kw),
}

REGRESSION_REGISTRY: dict[str, Any] = {
    "linear_regression": lambda **kw: LinearRegression(**kw),
    "ridge": lambda **kw: Ridge(random_state=42, **kw),
    "lasso": lambda **kw: Lasso(random_state=42, **kw),
    "elasticnet": lambda **kw: ElasticNet(random_state=42, **kw),
    "random_forest_regressor": lambda **kw: RandomForestRegressor(
        n_estimators=kw.pop("n_estimators", 100),
        random_state=42,
        **kw,
    ),
    "xgboost_regressor": _xgb_regressor,
    "catboost_regressor": _catboost_regressor,
    "lightgbm_regressor": _lgbm_regressor,
}

CLUSTERING_REGISTRY: dict[str, Any] = {
    "kmeans": lambda **kw: KMeans(n_clusters=kw.pop("n_clusters", 5), random_state=42, **kw),
    "dbscan": lambda **kw: DBSCAN(**kw),
    "agglomerative": lambda **kw: AgglomerativeClustering(**kw),
}

ALL_REGISTRIES = {
    "classification": CLASSIFICATION_REGISTRY,
    "regression": REGRESSION_REGISTRY,
    "clustering": CLUSTERING_REGISTRY,
}


def get_estimator(model_type: str, algorithm: str, hyperparameters: dict[str, Any] | None = None) -> BaseEstimator:
    """Instantiate an estimator by model type and algorithm name."""
    registry = ALL_REGISTRIES.get(model_type)
    if registry is None:
        raise ValidationError(f"Unknown model type: {model_type}")
    factory = registry.get(algorithm)
    if factory is None:
        raise ValidationError(f"Unknown algorithm '{algorithm}' for type '{model_type}'")
    return factory(**(hyperparameters or {}))


def default_algorithms(model_type: str) -> list[str]:
    """Return the default algorithm list for a model type."""
    registry = ALL_REGISTRIES.get(model_type, {})
    return list(registry.keys())
