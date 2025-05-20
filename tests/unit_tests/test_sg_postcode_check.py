# tests/unit_tests/test_sg_check_postal_format.py

import pytest

from address_validator.steps.sg_postcode_check import SGCheckPostalFormatStep
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    return SGCheckPostalFormatStep()


def test_missing_postcode(step):
    """
    If 'parsed' has no 'postcode' key (or it's None), we should get POSTAL_CODE_MISSING.
    """
    ctx = {"parsed": {}}
    updated = step(ctx.copy())
    assert updated["validate_status"] == ValidateStatus.POSTAL_CODE_MISSING


def test_empty_postcode(step):
    """
    If 'parsed' contains an empty string for 'postcode', that also counts as missing.
    """
    ctx = {"parsed": {"postcode": ""}}
    updated = step(ctx.copy())
    assert updated["validate_status"] == ValidateStatus.POSTAL_CODE_MISSING


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
    """
    Any postcode that is not exactly 6 digits should yield INVALID_POSTAL_CODE.
    """
    ctx = {"parsed": {"postcode": bad_postal}}
    updated = step(ctx.copy())
    assert updated["validate_status"] == ValidateStatus.INVALID_POSTAL_CODE


def test_valid_postcode(step):
    """
    A well‐formed, six‐digit numeric postcode should NOT set any validate_status.
    """
    ctx = {"parsed": {"postcode": "123456"}}
    updated = step(ctx.copy())
    # For a valid postcode, the step returns the ctx unchanged (no validate_status key)
    assert "validate_status" not in updated
