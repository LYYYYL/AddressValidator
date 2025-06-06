"""
Unit tests for MissingUnitNoCheck step.

This step sets VALIDATE_STATUS to UNIT_NUMBER_MISSING if a unit number is required
(based on property type) but not present in the parsed address.
"""

import pytest

from address_validator.constants import (
    PARSED_ADDRESS,
    UNIT_NUMBER,
    VALIDATE_STATUS,
)
from address_validator.steps.missing_unit_no_check import MissingUnitNoCheck
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    """Returns a shared MissingUnitNoCheck instance."""
    return MissingUnitNoCheck()


def test_property_requires_unit_but_none_given_whitelist(monkeypatch, step):
    """Should set VALIDATE_STATUS if property type needs unit and no unit is present (whitelist mode)."""
    monkeypatch.setattr("address_validator.steps.missing_unit_no_check.USE_UNIT_REQUIREMENT_WHITELIST", True)
    monkeypatch.setattr(
        "address_validator.steps.missing_unit_no_check.extract_property_types", lambda ctx: ["Condominium"]
    )

    ctx = {PARSED_ADDRESS: {}}
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.UNIT_NUMBER_MISSING


def test_property_does_not_require_unit_whitelist(monkeypatch, step):
    """Should not set VALIDATE_STATUS if unit is missing but property does not require it (whitelist mode)."""
    monkeypatch.setattr("address_validator.steps.missing_unit_no_check.USE_UNIT_REQUIREMENT_WHITELIST", True)
    monkeypatch.setattr("address_validator.steps.missing_unit_no_check.extract_property_types", lambda ctx: ["Landed"])

    ctx = {PARSED_ADDRESS: {}}
    updated = step(ctx.copy())
    assert VALIDATE_STATUS not in updated


def test_property_requires_unit_but_none_given_blacklist(monkeypatch, step):
    """Should set VALIDATE_STATUS if property is not in safe list and unit is missing (blacklist mode)."""
    monkeypatch.setattr("address_validator.steps.missing_unit_no_check.USE_UNIT_REQUIREMENT_WHITELIST", False)
    monkeypatch.setattr(
        "address_validator.steps.missing_unit_no_check.extract_property_types", lambda ctx: ["Shophouse"]
    )

    ctx = {PARSED_ADDRESS: {}}
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.UNIT_NUMBER_MISSING


def test_property_in_blacklist_exempt_list(monkeypatch, step):
    """Should not set VALIDATE_STATUS if property is in NOT_REQUIRING_UNIT list (blacklist mode)."""
    monkeypatch.setattr("address_validator.steps.missing_unit_no_check.USE_UNIT_REQUIREMENT_WHITELIST", False)
    monkeypatch.setattr("address_validator.steps.missing_unit_no_check.extract_property_types", lambda ctx: ["Landed"])
    monkeypatch.setattr("address_validator.steps.missing_unit_no_check.PROPERTY_TYPES_NOT_REQUIRING_UNIT", ["Landed"])

    ctx = {PARSED_ADDRESS: {}}
    updated = step(ctx.copy())
    assert VALIDATE_STATUS not in updated


def test_property_type_missing(monkeypatch, step):
    """Should skip check if no valid property types are found."""
    monkeypatch.setattr("address_validator.steps.missing_unit_no_check.extract_property_types", lambda ctx: [])

    ctx = {PARSED_ADDRESS: {}}
    updated = step(ctx.copy())
    assert VALIDATE_STATUS not in updated


def test_unit_present_even_if_required(monkeypatch, step):
    """Should not set VALIDATE_STATUS if unit is present, even if property type needs it."""
    monkeypatch.setattr("address_validator.steps.missing_unit_no_check.USE_UNIT_REQUIREMENT_WHITELIST", True)
    monkeypatch.setattr(
        "address_validator.steps.missing_unit_no_check.extract_property_types", lambda ctx: ["Condominium"]
    )

    ctx = {PARSED_ADDRESS: {UNIT_NUMBER: "#01-23"}}
    updated = step(ctx.copy())
    assert VALIDATE_STATUS not in updated
