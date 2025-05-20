# tests/unit_tests/test_block_number_match_step.py

import pytest

from address_validator.onemap_client import ONEMAP_BLK_NO_KEY
from address_validator.steps.block_number_match import BlockNumberMatchStep
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    return BlockNumberMatchStep()


def make_ctx(house_number, source_blks):
    """
    Helper to construct ctx:
    - house_number: value for parsed["house_number"]
    - source_blks: list of strings, each is ONEMAP_BLK_NO_KEY in onemap_data entries
    """
    parsed = {"house_number": house_number}
    onemap_data = [{ONEMAP_BLK_NO_KEY: blk} for blk in source_blks]
    return {"parsed": parsed, "onemap_data": onemap_data}


def test_exact_match_no_mismatch(step):
    """
    If parsed.house_number matches a source block exactly, no validate_status is set.
    """
    ctx = make_ctx("123", ["123"])
    updated = step(ctx.copy())
    assert "validate_status" not in updated


def test_exact_mismatch(step):
    """
    If parsed.house_number does not match any source block, validate_status == BLOCK_NUMBER_MISMATCH.
    """
    ctx = make_ctx("456", ["123", "789"])
    updated = step(ctx.copy())
    assert updated["validate_status"] == ValidateStatus.BLOCK_NUMBER_MISMATCH


def test_strip_trailing_alpha_match(step):
    """
    With BLOCK_NUMBER_STRIP_TRAILING_ALPHA=True, trailing letters are stripped before compare.
    '123A' (source) vs '123' (parsed) should match.
    """
    ctx = make_ctx("123", ["123A"])
    updated = step(ctx.copy())
    assert "validate_status" not in updated


def test_strip_trailing_alpha_mismatch(step):
    """
    With BLOCK_NUMBER_STRIP_TRAILING_ALPHA=True, '123A' (source)->'123' vs '124' (parsed) still mismatch.
    """
    ctx = make_ctx("124", ["123A"])
    updated = step(ctx.copy())
    assert updated["validate_status"] == ValidateStatus.BLOCK_NUMBER_MISMATCH


def test_case_insensitive_compare(step):
    """
    Upper/lower case differences should not matter (letters are stripped or compared uppercased).
    'abcA' and 'ABCa' become 'ABC' -> match.
    """
    ctx = make_ctx("ABCa", ["abcA"])
    updated = step(ctx.copy())
    assert "validate_status" not in updated


def test_onemap_empty_list_causes_mismatch(step):
    """
    If onemap_data is empty, source set is empty; any non-empty parsed.house_number causes mismatch.
    """
    ctx = {"parsed": {"house_number": "123"}, "onemap_data": []}
    updated = step(ctx.copy())
    assert updated["validate_status"] == ValidateStatus.BLOCK_NUMBER_MISMATCH


def test_missing_house_number_treated_as_empty_and_matched(step):
    """
    If parsed.house_number is missing or None, blk_no -> ''. If onemap_data has an entry with empty blk,
    that yields raw_source '', so it matches and no validate_status is set.
    """
    # Case: house_number is None, onemap_data contains an entry with blank block
    ctx = {"parsed": {"house_number": None}, "onemap_data": [{ONEMAP_BLK_NO_KEY: ""}]}
    updated = step(ctx.copy())
    assert "validate_status" not in updated

    # Case: house_number key is entirely missing
    ctx2 = {"parsed": {}, "onemap_data": [{ONEMAP_BLK_NO_KEY: ""}]}
    updated2 = step(ctx2.copy())
    assert "validate_status" not in updated2


def test_strip_alpha_disabled(monkeypatch, step):
    """
    If BLOCK_NUMBER_STRIP_TRAILING_ALPHA=False, no stripping occurs.
    '123A' (source) vs '123' (parsed) should mismatch.
    """
    # Temporarily disable stripping on the class
    monkeypatch.setattr(BlockNumberMatchStep, "BLOCK_NUMBER_STRIP_TRAILING_ALPHA", False)

    ctx = make_ctx("123", ["123A"])
    updated = step(ctx.copy())
    assert updated["validate_status"] == ValidateStatus.BLOCK_NUMBER_MISMATCH

    # And if they match exactly including trailing alpha, no mismatch
    ctx2 = make_ctx("123A", ["123A"])
    updated2 = step(ctx2.copy())
    assert "validate_status" not in updated2
