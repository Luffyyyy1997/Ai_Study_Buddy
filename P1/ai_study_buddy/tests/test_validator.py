"""Tests for validator.py."""

import pytest
from validator import (
    validate_material,
    validate_topic,
    validate_doubt,
    validate_study_time,
)


# ---------------------------------------------------------------------------
# validate_material
# ---------------------------------------------------------------------------

class TestValidateMaterial:
    def test_empty_string(self):
        assert validate_material("") is not None

    def test_whitespace_only(self):
        assert validate_material("   \n\t  ") is not None

    def test_too_short(self):
        assert validate_material("Short text") is not None

    def test_exactly_49_chars(self):
        assert validate_material("x" * 49) is not None

    def test_exactly_50_chars_passes(self):
        assert validate_material("x" * 50) is None

    def test_long_text_passes(self):
        assert validate_material("A" * 200) is None

    def test_returns_string_on_failure(self):
        result = validate_material("")
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# validate_topic
# ---------------------------------------------------------------------------

class TestValidateTopic:
    def test_empty_string(self):
        assert validate_topic("") is not None

    def test_whitespace_only(self):
        assert validate_topic("   ") is not None

    def test_valid_topic(self):
        assert validate_topic("Recursion") is None

    def test_single_char(self):
        assert validate_topic("A") is None


# ---------------------------------------------------------------------------
# validate_doubt
# ---------------------------------------------------------------------------

class TestValidateDoubt:
    def test_empty_string(self):
        assert validate_doubt("") is not None

    def test_whitespace_only(self):
        assert validate_doubt("  ") is not None

    def test_valid_doubt(self):
        assert validate_doubt("What is a variable?") is None


# ---------------------------------------------------------------------------
# validate_study_time
# ---------------------------------------------------------------------------

class TestValidateStudyTime:
    def test_none(self):
        assert validate_study_time(None) is not None

    def test_zero(self):
        assert validate_study_time(0) is not None

    def test_negative(self):
        assert validate_study_time(-1) is not None

    def test_valid_integer(self):
        assert validate_study_time(2) is None

    def test_valid_float(self):
        assert validate_study_time(1.5) is None

    def test_non_numeric_string(self):
        assert validate_study_time("abc") is not None
