"""
Unit tests for SearchStreetDirectoryStep.

Covers behavior for various OneMap inputs and StreetDirectoryClient responses,
including OK, error, empty, NIL block, and missing keys.
"""

import pytest

from address_validator.constants import (
    ONEMAP_BLOCK_NUMBER,
    ONEMAP_POSTAL_CODE,
    ONEMAP_RESULTS_BY_POSTCODE,
    ONEMAP_STREET_NAME,
    STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS,
    VALIDATE_STATUS,
)
from address_validator.steps.search_streetdirectory import SearchStreetDirectoryStep
from address_validator.streetdirectory_client import (
    SearchResponseStatus,
    StreetDirectorySearchResult,
)
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    """Returns a shared instance of SearchStreetDirectoryStep."""
    return SearchStreetDirectoryStep()


# 1) If onemap_search_with_postcode is empty or missing, __call__ should simply return ctx untouched.
def test_no_onemap_data(step):
    """Returns a shared instance of SearchStreetDirectoryStep."""
    ctx = {}
    returned = step(ctx.copy())
    assert VALIDATE_STATUS not in returned
    assert STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS not in returned

    ctx2 = {ONEMAP_RESULTS_BY_POSTCODE: []}
    returned2 = step(ctx2.copy())
    assert VALIDATE_STATUS not in returned2
    assert STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS not in returned2


def test_non_ok_status(monkeypatch, step):
    """Should set VALIDATE_STATUS to non-OK status if StreetDirectory search fails."""
    dummy_onemap = {
        ONEMAP_BLOCK_NUMBER: "123",
        ONEMAP_STREET_NAME: "Orchard Road",
        ONEMAP_POSTAL_CODE: "238826",
    }
    ctx = {ONEMAP_RESULTS_BY_POSTCODE: [dummy_onemap]}

    fake_status = SearchResponseStatus.NOT_FOUND
    fake_items = [("irrelevant", "data")]

    # Pass dummy raw_query="" and timestamp=None to satisfy __init__
    fake_result = StreetDirectorySearchResult(
        status=fake_status,
        items=fake_items,
        raw_query="",
        timestamp=None,
    )

    class DummyClient:
        def __init__(self):
            pass

        def search(self, address, country, state, limit):
            return fake_result

    # Monkey‐patch the StreetDirectoryClient constructor
    monkeypatch.setattr(
        "address_validator.streetdirectory_client.StreetDirectoryClient",
        DummyClient,
    )

    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == fake_status.value
    assert STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS not in updated


# 3) If status == OK but items == [], __call__ should set NO_STREETDIRECTORY_MATCH
def test_ok_status_but_empty_items(monkeypatch, step):
    """Should set NO_STREETDIRECTORY_MATCH if status is OK but items is empty."""
    dummy_onemap = {
        ONEMAP_BLOCK_NUMBER: "45",
        ONEMAP_STREET_NAME: "Bukit Timah Road",
        ONEMAP_POSTAL_CODE: "229875",
    }
    ctx = {ONEMAP_RESULTS_BY_POSTCODE: [dummy_onemap]}

    fake_status = SearchResponseStatus.OK
    fake_items = []

    fake_result = StreetDirectorySearchResult(
        status=fake_status,
        items=fake_items,
        raw_query="",
        timestamp=None,
    )

    class DummyClient:
        def __init__(self):
            pass

        def search(self, address, country, state, limit):
            return fake_result

    monkeypatch.setattr(
        "address_validator.streetdirectory_client.StreetDirectoryClient",
        DummyClient,
    )

    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.NO_STREETDIRECTORY_MATCH
    assert STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS not in updated


# 4) If status == OK and items != [], __call__ should set STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS to the returned items
def test_ok_status_with_items(monkeypatch, step):
    """Should set STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS if status is OK and items are returned."""
    dummy_onemap = {
        ONEMAP_BLOCK_NUMBER: "88",
        ONEMAP_STREET_NAME: "Jalan Besar",
        ONEMAP_POSTAL_CODE: "209005",
    }
    ctx = {ONEMAP_RESULTS_BY_POSTCODE: [dummy_onemap]}

    fake_status = SearchResponseStatus.OK
    fake_items = [
        ("88 Jalan Besar, #01-15", "Residential"),
        ("88 Jalan Besar, #02-22", "Commercial"),
    ]

    fake_result = StreetDirectorySearchResult(
        status=fake_status,
        items=fake_items,
        raw_query="",
        timestamp=None,
    )

    captured = {}

    class DummyClient:
        def __init__(self):
            pass

        def search(self, address, country, state, limit):
            captured["address_arg"] = address
            captured["other_args"] = (country, state, limit)
            return fake_result

    monkeypatch.setattr(
        "address_validator.streetdirectory_client.StreetDirectoryClient",
        DummyClient,
    )

    updated = step(ctx.copy())
    # No validate_status should be set here
    assert VALIDATE_STATUS not in updated
    # streetdirectory_results should match fake_items
    assert updated[STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS] == fake_items

    # Verify the constructed query string is "<blk>, <street>, <postcode>"
    assert captured["address_arg"] == "88, Jalan Besar, 209005"
    # Verify the other fixed arguments
    assert captured["other_args"] == ("singapore", 0, None)


# 5) If ONEMAP_BLOCK_NUMBER == "NIL", we should trim it to an empty string in the query
def test_nil_blk_becomes_empty(monkeypatch, step):
    """Should treat 'NIL' block number as an empty string in the query."""
    dummy_onemap = {
        ONEMAP_BLOCK_NUMBER: "NIL",  # Should be treated as ""
        ONEMAP_STREET_NAME: "Pasir Panjang Road",
        ONEMAP_POSTAL_CODE: "117439",
    }
    ctx = {ONEMAP_RESULTS_BY_POSTCODE: [dummy_onemap]}

    fake_status = SearchResponseStatus.OK
    fake_items = []

    fake_result = StreetDirectorySearchResult(
        status=fake_status,
        items=fake_items,
        raw_query="",
        timestamp=None,
    )

    captured = {}

    class DummyClient:
        def __init__(self):
            pass

        def search(self, address, country, state, limit):
            captured["address_arg"] = address
            return fake_result

    monkeypatch.setattr(
        "address_validator.streetdirectory_client.StreetDirectoryClient",
        DummyClient,
    )

    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.NO_STREETDIRECTORY_MATCH

    # Because blk was "NIL", the query string should be ", Pasir Panjang Road, 117439"
    assert captured["address_arg"] == ", Pasir Panjang Road, 117439"


# 6) If onemap_search_with_postcode[0] is missing some keys (e.g. missing ONEMAP_STREET_NAME),
#    __call__ will still build a query string with empty pieces.
def test_missing_keys_in_onemap_data(monkeypatch, step):
    """Should still run if ONEMAP_STREET_NAME is missing from the input."""
    # Omit ONEMAP_STREET_NAME entirely
    dummy_onemap = {
        ONEMAP_BLOCK_NUMBER: "150",
        # no ONEMAP_STREET_NAME
        ONEMAP_POSTAL_CODE: "530150",
    }
    ctx = {ONEMAP_RESULTS_BY_POSTCODE: [dummy_onemap]}

    fake_status = SearchResponseStatus.OK
    fake_items = []

    fake_result = StreetDirectorySearchResult(
        status=fake_status,
        items=fake_items,
        raw_query="",
        timestamp=None,
    )

    captured = {}

    class DummyClient:
        def __init__(self):
            pass

        def search(self, address, country, state, limit):
            captured["address_arg"] = address
            return fake_result

    monkeypatch.setattr(
        "address_validator.streetdirectory_client.StreetDirectoryClient",
        DummyClient,
    )

    updated = step(ctx.copy())
    assert updated[VALIDATE_STATUS] == ValidateStatus.NO_STREETDIRECTORY_MATCH

    # Since ONEMAP_STREET_NAME was missing, `street` defaults to "",
    # so the expected query is "150, , 530150"
    assert captured["address_arg"] == "150, , 530150"
