"""
Unit tests for the map_ctx_to_row function in app.ui.row_mapper.

Covers:
- Normal case with valid address
- Various error and timeout statuses
- Property type overrides for specific validation errors
"""

from address_validator.constants import (
    BLOCK_NUMBER,
    PARSED_ADDRESS,
    POSTAL_CODE,
    PROPERTY_TYPE,
    RAW_ADDRESS,
    STREET_NAME,
    STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS,
    UNIT_NUMBER,
    VALIDATE_STATUS,
)
from address_validator.search import SearchResponseStatus
from address_validator.validation import ValidateStatus
from app.ui.row_mapper import map_ctx_to_row

EXAMPLE_PARSED_ADDRESS = {
    BLOCK_NUMBER: "288E",
    STREET_NAME: "Jurong East Street 21",
    UNIT_NUMBER: "06-408",
    POSTAL_CODE: "605288",
}

RAW_INPUT = "288E Jurong East Street 21, #06-408, 605288"


def test_valid_address_mapping():
    """Should map a valid address context to a populated row dict."""
    ctx = {
        VALIDATE_STATUS: ValidateStatus.VALID,
        PARSED_ADDRESS: EXAMPLE_PARSED_ADDRESS,
        STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS: [(RAW_INPUT, "HDB Blocks")],
    }

    row = map_ctx_to_row(ctx, RAW_INPUT)
    assert row[RAW_ADDRESS] == RAW_INPUT
    assert row[VALIDATE_STATUS] == ValidateStatus.VALID
    assert row[BLOCK_NUMBER] == "288E"
    assert row[STREET_NAME] == "Jurong East Street 21"
    assert row[UNIT_NUMBER] == "06-408"
    assert row[POSTAL_CODE] == "605288"
    assert row[PROPERTY_TYPE] == "HDB Blocks"


def test_error_response():
    """Should return empty fields when validation status is ERROR."""
    ctx = {
        VALIDATE_STATUS: SearchResponseStatus.ERROR,
    }

    row = map_ctx_to_row(ctx, RAW_INPUT)
    assert row[BLOCK_NUMBER] == ""
    assert row[STREET_NAME] == ""
    assert row[UNIT_NUMBER] == ""
    assert row[POSTAL_CODE] == ""
    assert row[PROPERTY_TYPE] == ""


def test_timeout_response():
    """Should return empty fields when validation status is TIMEOUT."""
    ctx = {
        VALIDATE_STATUS: SearchResponseStatus.TIMEOUT,
    }

    row = map_ctx_to_row(ctx, RAW_INPUT)
    assert row[BLOCK_NUMBER] == ""
    assert row[STREET_NAME] == ""
    assert row[UNIT_NUMBER] == ""
    assert row[POSTAL_CODE] == ""
    assert row[PROPERTY_TYPE] == ""


def test_address_and_postcode_mismatch():
    """Should override property type with '-' for ADDRESS_AND_POSTCODE_MISMATCH."""
    ctx = {
        VALIDATE_STATUS: ValidateStatus.ADDRESS_AND_POSTCODE_MISMATCH,
        PARSED_ADDRESS: EXAMPLE_PARSED_ADDRESS,
        STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS: [(RAW_INPUT, "Condominium")],
    }

    row = map_ctx_to_row(ctx, RAW_INPUT)
    assert row[PROPERTY_TYPE] == "-"  # override


def test_invalid_postal_code():
    """Should override property type with '-' for INVALID_POSTAL_CODE."""
    ctx = {
        VALIDATE_STATUS: ValidateStatus.INVALID_POSTAL_CODE,
        PARSED_ADDRESS: EXAMPLE_PARSED_ADDRESS,
        STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS: [(RAW_INPUT, "HDB Blocks")],
    }

    row = map_ctx_to_row(ctx, RAW_INPUT)
    assert row[PROPERTY_TYPE] == "-"  # override


def test_other_error_keeps_property_type():
    """Should retain property type for non-override validation errors."""
    ctx = {
        VALIDATE_STATUS: ValidateStatus.UNIT_NUMBER_MISSING,
        PARSED_ADDRESS: EXAMPLE_PARSED_ADDRESS,
        STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS: [(RAW_INPUT, "HDB Blocks")],
    }

    row = map_ctx_to_row(ctx, RAW_INPUT)
    assert row[PROPERTY_TYPE] == "HDB Blocks"
