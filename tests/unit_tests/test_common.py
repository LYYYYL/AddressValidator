"""
Unit tests for utility functions in address_validator.utils.common.

Includes tests for:
- extract_property_types: Extracts unique, non-empty property types from StreetDirectory results.
- extract_address_query_parts: Extracts (block, street, postal code) from context.
- current_utc_isoformat: Returns the current UTC time in ISO 8601 format with timezone.
"""

from datetime import datetime

from address_validator.constants import (
    BLOCK_NUMBER,
    ONEMAP_BLOCK_NUMBER,
    ONEMAP_POSTAL_CODE,
    ONEMAP_RESULTS_BY_POSTCODE,
    ONEMAP_STREET_NAME,
    PARSED_ADDRESS,
    POSTAL_CODE,
    STREET_NAME,
    STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS,
)
from address_validator.utils.common import (
    current_utc_isoformat,
    extract_address_query_parts,
    extract_property_types,
)

# --- extract_property_types ---


def test_extract_property_types_multiple():
    """Should return a list of unique property types when duplicates exist."""
    ctx = {
        STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS: [
            ("288E Jurong East Street 21, #12-34, 605288", "HDB Blocks"),
            ("26 Ridout Road, Singapore 248420", "Bungalow"),
            ("712 Yishun Ave 5, #01-23, 760712", "HDB Blocks"),
        ]
    }
    result = extract_property_types(ctx)
    assert result == ["HDB Blocks", "Bungalow"]


def test_extract_property_types_single():
    """Should return a single property type in a list."""
    ctx = {STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS: [("288E Jurong East Street 21", "Condominium")]}
    result = extract_property_types(ctx)
    assert result == ["Condominium"]


def test_extract_property_types_empty_context():
    """Should return an empty list when context is empty."""
    ctx = {}
    result = extract_property_types(ctx)
    assert result == []


def test_extract_property_types_empty_items():
    """Should return an empty list when StreetDirectory results are empty."""
    ctx = {STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS: []}
    result = extract_property_types(ctx)
    assert result == []


def test_extract_property_types_skips_none():
    """Should skip None and empty strings in category values."""
    ctx = {
        STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS: [
            ("some address", None),
            ("some address", ""),
            ("some address", "Industrial Building"),
        ]
    }
    result = extract_property_types(ctx)
    assert result == ["Industrial Building"]


# --- extract_address_query_parts ---


def test_extract_address_from_onemap():
    """Should extract address parts from OneMap results when available."""
    ctx = {
        ONEMAP_RESULTS_BY_POSTCODE: [
            {
                ONEMAP_BLOCK_NUMBER: "288E",
                ONEMAP_STREET_NAME: "Jurong East Street 21",
                ONEMAP_POSTAL_CODE: "605288",
            }
        ]
    }
    blk, street, postal = extract_address_query_parts(ctx)
    assert (blk, street, postal) == ("288E", "Jurong East Street 21", "605288")


def test_extract_address_onemap_nil_blk():
    """Should treat 'NIL' block numbers as empty strings."""
    ctx = {
        ONEMAP_RESULTS_BY_POSTCODE: [
            {
                ONEMAP_BLOCK_NUMBER: "NIL",
                ONEMAP_STREET_NAME: "Ang Mo Kio Avenue 3",
                ONEMAP_POSTAL_CODE: "560123",
            }
        ]
    }
    blk, street, postal = extract_address_query_parts(ctx)
    assert (blk, street, postal) == ("", "Ang Mo Kio Avenue 3", "560123")


def test_extract_address_from_parsed_fallback():
    """Should extract address parts from parsed address if prefer_onemap is False."""
    ctx = {
        PARSED_ADDRESS: {
            BLOCK_NUMBER: "712",
            STREET_NAME: "Yishun Avenue 5",
            POSTAL_CODE: "760712",
        }
    }
    blk, street, postal = extract_address_query_parts(ctx, prefer_onemap=False)
    assert (blk, street, postal) == ("712", "Yishun Avenue 5", "760712")


def test_extract_address_missing_all():
    """Should return empty strings when no address data is found."""
    ctx = {}
    blk, street, postal = extract_address_query_parts(ctx)
    assert (blk, street, postal) == ("", "", "")


# --- current_utc_isoformat ---


def test_current_utc_isoformat():
    """Should return a valid ISO 8601 UTC timestamp with timezone info."""
    ts = current_utc_isoformat()
    dt = datetime.fromisoformat(ts)
    assert dt.tzinfo is not None
    assert dt.utcoffset().total_seconds() == 0  # Should be UTC
