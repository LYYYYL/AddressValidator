# tests/unit_tests/test_missing_street_check_step.py

import pytest

from address_validator.steps.missing_street_check import MissingStreetCheckStep
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    return MissingStreetCheckStep()


def test_no_parsed_key(step):
    """
    If ctx has no "parsed" key, then 'street' is None and validate_status should be set.
    """
    ctx = {}
    updated = step(ctx.copy())
    assert updated["validate_status"] == ValidateStatus.STREET_NAME_MISSING


def test_empty_road(step):
    """
    If ctx["parsed"]["road"] is an empty string, validate_status should be set.
    """
    ctx = {"parsed": {"road": ""}}
    updated = step(ctx.copy())
    assert updated["validate_status"] == ValidateStatus.STREET_NAME_MISSING


def test_none_road(step):
    """
    If ctx["parsed"]["road"] is None, validate_status should be set.
    """
    ctx = {"parsed": {"road": None}}
    updated = step(ctx.copy())
    assert updated["validate_status"] == ValidateStatus.STREET_NAME_MISSING


def test_valid_road(step):
    """
    If ctx["parsed"]["road"] is a non-empty string, validate_status should not be set.
    """
    ctx = {"parsed": {"road": "Orchard Road"}}
    updated = step(ctx.copy())
    assert "validate_status" not in updated
