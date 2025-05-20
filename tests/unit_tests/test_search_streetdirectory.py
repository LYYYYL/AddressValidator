# tests/unit_tests/test_search_streetdirectory.py

from datetime import datetime

import pytest

from address_validator.onemap_client import ONEMAP_BLK_NO_KEY, ONEMAP_POSTCODE_KEY, ONEMAP_STREET_KEY
from address_validator.steps.search_streetdirectory import SearchStreetDirectoryStep
from address_validator.streetdirectory_client import (
    SearchResponseStatus,
    StreetDirectorySearchResult,
)
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    return SearchStreetDirectoryStep()


# 1) If onemap_data is empty or missing, __call__ should simply return ctx untouched.
def test_no_onemap_data(step):
    ctx = {}  # no "onemap_data" key
    returned = step(ctx.copy())
    assert "validate_status" not in returned
    assert "streetdirectory_results" not in returned

    ctx2 = {"onemap_data": []}
    returned2 = step(ctx2.copy())
    assert "validate_status" not in returned2
    assert "streetdirectory_results" not in returned2


# 2) If StreetDirectoryClient.search(...) returns a non‐OK status,
#    __call__ should set ctx["validate_status"] = status.value
def test_non_ok_status(monkeypatch, step):
    dummy_onemap = {
        ONEMAP_BLK_NO_KEY: "123",
        ONEMAP_STREET_KEY: "Orchard Road",
        ONEMAP_POSTCODE_KEY: "238826",
    }
    ctx = {"onemap_data": [dummy_onemap]}

    fake_status = SearchResponseStatus.NOT_FOUND
    fake_items = [("irrelevant", "data")]

    # Pass dummy raw_query="" and fetched_at=None to satisfy __init__
    fake_result = StreetDirectorySearchResult(
        status=fake_status,
        items=fake_items,
        raw_query="",
        fetched_at=None,
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
    assert updated["validate_status"] == fake_status.value
    assert "streetdirectory_results" not in updated


# 3) If status == OK but items == [], __call__ should set NO_STREETDIRECTORY_MATCH
def test_ok_status_but_empty_items(monkeypatch, step):
    dummy_onemap = {
        ONEMAP_BLK_NO_KEY: "45",
        ONEMAP_STREET_KEY: "Bukit Timah Road",
        ONEMAP_POSTCODE_KEY: "229875",
    }
    ctx = {"onemap_data": [dummy_onemap]}

    fake_status = SearchResponseStatus.OK
    fake_items = []

    fake_result = StreetDirectorySearchResult(
        status=fake_status,
        items=fake_items,
        raw_query="",
        fetched_at=None,
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
    assert updated["validate_status"] == ValidateStatus.NO_STREETDIRECTORY_MATCH
    assert "streetdirectory_results" not in updated


# 4) If status == OK and items != [], __call__ should set "streetdirectory_results" to the returned items
def test_ok_status_with_items(monkeypatch, step):
    dummy_onemap = {
        ONEMAP_BLK_NO_KEY: "88",
        ONEMAP_STREET_KEY: "Jalan Besar",
        ONEMAP_POSTCODE_KEY: "209005",
    }
    ctx = {"onemap_data": [dummy_onemap]}

    fake_status = SearchResponseStatus.OK
    fake_items = [
        ("88 Jalan Besar, #01-15", "Residential"),
        ("88 Jalan Besar, #02-22", "Commercial"),
    ]

    fake_result = StreetDirectorySearchResult(
        status=fake_status,
        items=fake_items,
        raw_query="",
        fetched_at=None,
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
    assert "validate_status" not in updated
    # streetdirectory_results should match fake_items
    assert updated["streetdirectory_results"] == fake_items

    # Verify the constructed query string is "<blk>, <street>, <postcode>"
    assert captured["address_arg"] == "88, Jalan Besar, 209005"
    # Verify the other fixed arguments
    assert captured["other_args"] == ("singapore", 0, None)


# 5) If ONEMAP_BLK_NO_KEY == "NIL", we should trim it to an empty string in the query
def test_nil_blk_becomes_empty(monkeypatch, step):
    dummy_onemap = {
        ONEMAP_BLK_NO_KEY: "NIL",  # Should be treated as ""
        ONEMAP_STREET_KEY: "Pasir Panjang Road",
        ONEMAP_POSTCODE_KEY: "117439",
    }
    ctx = {"onemap_data": [dummy_onemap]}

    fake_status = SearchResponseStatus.OK
    fake_items = []

    fake_result = StreetDirectorySearchResult(
        status=fake_status,
        items=fake_items,
        raw_query="",
        fetched_at=None,
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
    assert updated["validate_status"] == ValidateStatus.NO_STREETDIRECTORY_MATCH

    # Because blk was "NIL", the query string should be ", Pasir Panjang Road, 117439"
    assert captured["address_arg"] == ", Pasir Panjang Road, 117439"


# 6) If onemap_data[0] is missing some keys (e.g. missing ONEMAP_STREET_KEY),
#    __call__ will still build a query string with empty pieces.
def test_missing_keys_in_onemap_data(monkeypatch, step):
    # Omit ONEMAP_STREET_KEY entirely
    dummy_onemap = {
        ONEMAP_BLK_NO_KEY: "150",
        # no ONEMAP_STREET_KEY
        ONEMAP_POSTCODE_KEY: "530150",
    }
    ctx = {"onemap_data": [dummy_onemap]}

    fake_status = SearchResponseStatus.OK
    fake_items = []

    fake_result = StreetDirectorySearchResult(
        status=fake_status,
        items=fake_items,
        raw_query="",
        fetched_at=None,
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
    assert updated["validate_status"] == ValidateStatus.NO_STREETDIRECTORY_MATCH

    # Since ONEMAP_STREET_KEY was missing, `street` defaults to "",
    # so the expected query is "150, , 530150"
    assert captured["address_arg"] == "150, , 530150"
