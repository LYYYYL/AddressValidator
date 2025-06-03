"""
Unit tests for the MissingStreetCheckStep validation logic.

This step ensures that the parsed address contains a non-empty street name.
Sets the validation status to STREET_NAME_MISSING if the street is missing or invalid.
"""

import pytest

from address_validator.constants import PARSED_ADDRESS, STREET_NAME, VALIDATE_STATUS
from address_validator.steps.missing_street_check import MissingStreetCheckStep
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    """Returns a shared MissingStreetCheckStep instance."""
    return MissingStreetCheckStep()


def test_no_parsed_key(step):
    """Should set validate_status if PARSED_ADDRESS is missing."""
    ctx = {}
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.STREET_NAME_MISSING


def test_empty_road(step):
    """Should set validate_status if street is an empty string."""
    ctx = {PARSED_ADDRESS: {STREET_NAME: ""}}
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.STREET_NAME_MISSING


def test_none_road(step):
    """Should set validate_status if street is None."""
    ctx = {PARSED_ADDRESS: {STREET_NAME: None}}
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.STREET_NAME_MISSING


def test_valid_road(step):
    """Should not set validate_status if street is a valid non-empty string."""
    ctx = {PARSED_ADDRESS: {STREET_NAME: "Orchard Road"}}
    updated = step(ctx.copy())
    assert VALIDATE_STATUS not in updated
