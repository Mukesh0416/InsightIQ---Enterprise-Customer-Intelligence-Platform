"""
Analytics package for the InsightIQ Data Profiling and EDA Engine.

Provides automated statistical profiling, distribution analysis, outlier
detection, correlation analysis, data quality insights, and visualization
data generation for uploaded datasets.
"""

from app.analytics.profiling.engine import ProfilingEngine
from app.analytics.statistics.numerical import NumericalAnalyzer
from app.analytics.statistics.categorical import CategoricalAnalyzer
from app.analytics.outliers.detector import OutlierDetector
from app.analytics.correlation.engine import CorrelationEngine
from app.analytics.distribution.analyzer import DistributionAnalyzer
from app.analytics.quality.insights import QualityInsights
from app.analytics.visualization.generator import VisualizationGenerator

__all__ = [
    "ProfilingEngine",
    "NumericalAnalyzer",
    "CategoricalAnalyzer",
    "OutlierDetector",
    "CorrelationEngine",
    "DistributionAnalyzer",
    "QualityInsights",
    "VisualizationGenerator",
]