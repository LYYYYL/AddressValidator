"""
Unit tests for SGCheckPostalFormatStep.

This step checks if the parsed postal code is present and correctly formatted
as a six-digit number. If not, it sets VALIDATE_STATUS to INVALID_POSTAL_CODE.
"""

import pytest

from address_validator.constants import PARSED_ADDRESS, POSTAL_CODE, VALIDATE_STATUS
from address_validator.steps.sg_postcode_check import SGCheckPostalFormatStep
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    """Returns a shared SGCheckPostalFormatStep instance."""
    return SGCheckPostalFormatStep()


def test_missing_postcode(step):
    """Should flag INVALID_POSTAL_CODE if postcode key is missing or None."""
    ctx = {PARSED_ADDRESS: {}}
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.INVALID_POSTAL_CODE


def test_empty_postcode(step):
    """Should flag INVALID_POSTAL_CODE if postcode is an empty string."""
    ctx = {PARSED_ADDRESS: {POSTAL_CODE: ""}}
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.INVALID_POSTAL_CODE


@pytest.mark.parametrize(
    "bad_postal",
    [
        "12345",  # too short
        "1234567",  # too long
        "ABC123",  # non‐digit characters
        "12A456",  # mixed letters and digits
    ],
)
def test_invalid_postcode_format(step, bad_postal):
    """Should flag INVALID_POSTAL_CODE for non-6-digit or non-numeric values."""
    ctx = {PARSED_ADDRESS: {POSTAL_CODE: bad_postal}}
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.INVALID_POSTAL_CODE


def test_valid_postcode(step):
    """Should not set validate_status for valid six-digit postcode."""
    ctx = {PARSED_ADDRESS: {POSTAL_CODE: "123456"}}
    updated = step(ctx.copy())
    # For a valid postcode, the step returns the ctx unchanged (no validate_status key)
    assert VALIDATE_STATUS not in updated
