"""Business analytics package for enterprise KPI and reporting."""

import importlib

from app.analytics.business.customer import CustomerAnalytics

try:
    _sales = importlib.import_module(".sales", __package__)
except ModuleNotFoundError:
    _sales = None

SalesAnalytics = getattr(_sales, "SalesAnalytics", None)

from app.analytics.business.revenue import RevenueAnalytics
from app.analytics.business.retention import RetentionAnalytics, RFMAnalyzer, CohortAnalyzer
from app.analytics.business.kpi import KPIEngine, TrendAnalyzer
from app.analytics.business.recommendations import RecommendationEngine, ExecutiveSummaryEngine

__all__ = [
    "CustomerAnalytics",
    "SalesAnalytics",
    "RevenueAnalytics",
    "RetentionAnalytics",
    "RFMAnalyzer",
    "CohortAnalyzer",
    "KPIEngine",
    "TrendAnalyzer",
    "RecommendationEngine",
    "ExecutiveSummaryEngine",
]