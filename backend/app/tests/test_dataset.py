"""
Unit tests for dataset validators, type detection, and quality engine.
"""

from __future__ import annotations

import io

import pandas as pd
import pytest

from app.exceptions import ValidationError
from app.validators.column_validator import ColumnValidator
from app.validators.file_validator import FileValidator
from app.validators.quality_engine import QualityEngine
from app.validators.type_detector import TypeDetector


class TestFileValidator:
    """Tests for file validation logic."""

    def test_validate_extension_csv(self) -> None:
        assert FileValidator().validate_extension("data.csv") == ".csv"

    def test_validate_extension_xlsx(self) -> None:
        assert FileValidator().validate_extension("report.xlsx") == ".xlsx"

    def test_validate_extension_unsupported(self) -> None:
        with pytest.raises(ValidationError):
            FileValidator().validate_extension("file.txt")

    def test_validate_size_empty(self) -> None:
        with pytest.raises(ValidationError):
            FileValidator().validate_size(0)

    def test_validate_size_too_large(self) -> None:
        fv = FileValidator()
        fv.max_size = 100
        with pytest.raises(ValidationError):
            fv.validate_size(200)

    def test_validate_filename_path_traversal(self) -> None:
        with pytest.raises(ValidationError):
            FileValidator().validate_filename("../../etc/passwd")

    def test_compute_sha256(self) -> None:
        h = FileValidator.compute_sha256(b"hello")
        assert len(h) == 64
        assert h == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


class TestColumnValidator:
    """Tests for column header validation."""

    def test_valid_headers(self) -> None:
        result = ColumnValidator.validate_headers(["name", "email", "age"])
        assert result == ["name", "email", "age"]

    def test_duplicate_headers(self) -> None:
        with pytest.raises(ValidationError):
            ColumnValidator.validate_headers(["name", "name", "age"])

    def test_blank_header(self) -> None:
        with pytest.raises(ValidationError):
            ColumnValidator.validate_headers(["name", "", "age"])

    def test_empty_headers(self) -> None:
        with pytest.raises(ValidationError):
            ColumnValidator.validate_headers([])


class TestTypeDetector:
    """Tests for automatic data type detection."""

    def test_detect_integer(self) -> None:
        s = pd.Series([1, 2, 3, 4, 5])
        assert TypeDetector.detect_series_type(s) == "integer"

    def test_detect_float(self) -> None:
        s = pd.Series([1.1, 2.2, 3.3])
        assert TypeDetector.detect_series_type(s) == "float"

    def test_detect_boolean(self) -> None:
        s = pd.Series([True, False, True])
        assert TypeDetector.detect_series_type(s) == "boolean"

    def test_detect_email(self) -> None:
        s = pd.Series(["a@b.com", "c@d.org", "e@f.net"])
        assert TypeDetector.detect_series_type(s) == "email"

    def test_detect_uuid(self) -> None:
        s = pd.Series([
            "550e8400-e29b-41d4-a716-446655440000",
            "550e8400-e29b-41d4-a716-446655440001",
        ])
        assert TypeDetector.detect_series_type(s) == "uuid"

    def test_detect_string(self) -> None:
        s = pd.Series(["alpha", "beta", "gamma", "delta", "epsilon"])
        assert TypeDetector.detect_series_type(s) == "string"

    def test_detect_categorical(self) -> None:
        s = pd.Series(["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"] * 10)
        assert TypeDetector.detect_series_type(s) == "categorical"

    def test_detect_column_types(self) -> None:
        df = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
        types = TypeDetector.detect_column_types(df)
        assert types["id"] == "integer"
        assert types["name"] in ("string", "categorical")


class TestQualityEngine:
    """Tests for the data quality scoring engine."""

    def test_empty_dataset(self) -> None:
        result = QualityEngine.analyze(pd.DataFrame())
        assert result["quality_score"] == 0.0
        assert any(i["type"] == "empty_dataset" for i in result["issues"])

    def test_clean_dataset(self) -> None:
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        result = QualityEngine.analyze(df)
        assert result["quality_score"] > 50
        assert result["completeness"] == 100.0

    def test_missing_values(self) -> None:
        df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", None]})
        result = QualityEngine.analyze(df)
        assert result["completeness"] < 100.0

    def test_duplicate_rows(self) -> None:
        df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
        result = QualityEngine.analyze(df)
        assert result["uniqueness"] < 100.0

    def test_constant_column(self) -> None:
        df = pd.DataFrame({"a": [1, 1, 1], "b": ["x", "y", "z"]})
        result = QualityEngine.analyze(df)
        col_summary = result["column_summary"]
        assert any("Constant column" in issue for issue in col_summary["a"]["issues"])

    def test_outliers_iqr(self) -> None:
        s = pd.Series([1, 2, 3, 4, 5, 100])
        outliers = TypeDetector.detect_outliers_iqr(s)
        assert outliers >= 1

    def test_quality_score_range(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = QualityEngine.analyze(df)
        assert 0 <= result["quality_score"] <= 100