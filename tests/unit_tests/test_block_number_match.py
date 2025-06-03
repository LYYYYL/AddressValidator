"""
Unit tests for the BlockNumberMatchStep validation logic.

Covers:
- Exact match and mismatch behavior
- Case-insensitive and optional trailing alpha stripping
- Handling of missing or empty block numbers
- Behavior toggled by BLOCK_NUMBER_STRIP_TRAILING_ALPHA
"""

import pytest

import address_validator.constants
from address_validator.constants import (
    ONEMAP_BLOCK_NUMBER,
    ONEMAP_RESULTS_BY_POSTCODE,
    PARSED_ADDRESS,
    VALIDATE_STATUS,
)
from address_validator.steps.block_number_match import BlockNumberMatchStep
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    """BlockNumberMatchStep class instantiation for shared use."""
    return BlockNumberMatchStep()


def make_ctx(house_number, source_blks):
    """
    Helper to construct ctx.

    - house_number: value for parsed_addr[AddressKeys.BLOCK_NUMBER].
    - source_blks: list of strings, each is ONEMAP_BLOCK_NUMBER in onemap_search_with_postcode entries.
    """
    parsed_addr = {"house_number": house_number}
    onemap_search_with_postcode = [{ONEMAP_BLOCK_NUMBER: blk} for blk in source_blks]
    return {PARSED_ADDRESS: parsed_addr, ONEMAP_RESULTS_BY_POSTCODE: onemap_search_with_postcode}


def test_exact_match_no_mismatch(step):
    """If parsed_addr.house_number matches a source block exactly, no validate_status is set."""
    ctx = make_ctx("123", ["123"])
    updated = step(ctx.copy())
    assert VALIDATE_STATUS not in updated


def test_exact_mismatch(step):
    """If parsed_addr.house_number does not match any source block, validate_status == BLOCK_NUMBER_MISMATCH."""
    ctx = make_ctx("456", ["123", "789"])
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.BLOCK_NUMBER_MISMATCH


def test_strip_trailing_alpha_match(monkeypatch):
    """
    With BLOCK_NUMBER_STRIP_TRAILING_ALPHA=True, trailing letters are stripped before compare.
    '123A' (source) vs '123' (parsed_addr) should match.
    """
    monkeypatch.setattr(address_validator.constants, "BLOCK_NUMBER_STRIP_TRAILING_ALPHA", True)
    step = BlockNumberMatchStep()
    ctx = make_ctx("123", ["123A"])
    updated = step(ctx.copy())
    assert VALIDATE_STATUS not in updated


def test_strip_trailing_alpha_mismatch(step):
    """With BLOCK_NUMBER_STRIP_TRAILING_ALPHA=True, '123A' vs '124' still mismatches."""
    ctx = make_ctx("124", ["123A"])
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.BLOCK_NUMBER_MISMATCH


def test_case_insensitive_compare(step):
    """
    Upper/lower case differences should not matter (letters are stripped or compared uppercased).
    'abcA' and 'ABCa' become 'ABC' -> match.
    """
    ctx = make_ctx("ABCa", ["abcA"])
    updated = step(ctx.copy())
    assert VALIDATE_STATUS not in updated


def test_onemap_empty_list_causes_mismatch(step):
    """
    If onemap_search_with_postcode is empty, source set is empty;
    any non-empty parsed_addr.house_number causes mismatch.
    """
    ctx = {PARSED_ADDRESS: {"house_number": "123"}, ONEMAP_RESULTS_BY_POSTCODE: []}
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.BLOCK_NUMBER_MISMATCH


def test_missing_house_number_treated_as_empty_and_matched(step):
    """
    If parsed_addr.house_number is missing or None, blk_no -> ''.
    If onemap_search_with_postcode has an entry with empty blk,
    that yields raw_source '', so it matches and no validate_status is set.
    """
    # Case: house_number is None, onemap_search_with_postcode contains an entry with blank block
    ctx = {PARSED_ADDRESS: {"house_number": None}, ONEMAP_RESULTS_BY_POSTCODE: [{ONEMAP_BLOCK_NUMBER: ""}]}
    updated = step(ctx.copy())
    assert VALIDATE_STATUS not in updated

    # Case: house_number key is entirely missing
    ctx2 = {PARSED_ADDRESS: {}, ONEMAP_RESULTS_BY_POSTCODE: [{ONEMAP_BLOCK_NUMBER: ""}]}
    updated2 = step(ctx2.copy())
    assert VALIDATE_STATUS not in updated2


def test_strip_alpha_disabled(monkeypatch, step):
    """
    If BLOCK_NUMBER_STRIP_TRAILING_ALPHA=False, no stripping occurs.
    '123A' (source) vs '123' (parsed_addr) should mismatch.
    """
    # Temporarily disable stripping on the class
    monkeypatch.setattr(address_validator.constants, "BLOCK_NUMBER_STRIP_TRAILING_ALPHA", False)

    ctx = make_ctx("123", ["123A"])
    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.BLOCK_NUMBER_MISMATCH

    # And if they match exactly including trailing alpha, no mismatch
    ctx2 = make_ctx("123A", ["123A"])
    updated2 = step(ctx2.copy())
    assert VALIDATE_STATUS not in updated2
