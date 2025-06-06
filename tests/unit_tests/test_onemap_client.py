"""
Unit tests for OneMapClient and OneMapSearchResult behavior.

Covers:
- Search result classification (OK, NOT_FOUND, INVALID_API_RESPONSE, etc.)
- Client response handling from mocked API responses
"""

import pytest

from address_validator.onemap_client import OneMapApiClient, OneMapClient, OneMapSearchResult
from address_validator.search import SearchResponseStatus

###################################################################################################
# Helpers / Fixtures
####################################################################################################


@pytest.fixture
def sample_list_of_dicts():
    """Sample OneMap API response with one address result."""
    return [{"ROAD_NAME": "Main Street", "POSTAL": "123456"}]


# ────────────────────────────────────────────────────────────────────────────────
# Tests for OneMapSearchResult.from_results(...)
# ────────────────────────────────────────────────────────────────────────────────


def test_from_results_none_returns_not_found_and_empty_list():
    """Should return INVALID_API_RESPONSE if results is None."""
    raw = "S123456"
    result = OneMapSearchResult.from_results(raw_query=raw, results=None)

    assert isinstance(result, OneMapSearchResult)
    assert result.raw_query == raw
    assert result.result_addrs == []  # no addresses
    assert result.status == SearchResponseStatus.INVALID_API_RESPONSE


def test_from_results_empty_list_returns_not_found_and_empty_list():
    """Should return NOT_FOUND if results is an empty list."""
    raw = "S000000"
    result = OneMapSearchResult.from_results(raw_query=raw, results=[])

    assert result.raw_query == raw
    assert result.result_addrs == []  # still no addresses
    assert result.status == SearchResponseStatus.NOT_FOUND


def test_from_results_nonempty_list_returns_ok_and_preserves_list(sample_list_of_dicts):
    """Should return OK if results contains a valid non-empty list."""
    raw = "528513"
    results = sample_list_of_dicts.copy()
    result = OneMapSearchResult.from_results(raw_query=raw, results=results)

    assert result.raw_query == raw
    assert result.result_addrs == results  # exactly the same list
    assert result.status == SearchResponseStatus.OK


def test_from_results_unexpected_type_returns_invalid_api_response():
    """Should return INVALID_API_RESPONSE if results is not a list."""
    raw = "ABC123"
    bogus = {"unexpected_key": "unexpected_value"}  # not a list or None
    result = OneMapSearchResult.from_results(raw_query=raw, results=bogus)

    assert result.raw_query == raw
    assert result.result_addrs == []  # fallback to empty list
    assert result.status == SearchResponseStatus.INVALID_API_RESPONSE


###################################################################################################
# Tests for OneMapClient.search(...)
###################################################################################################


def test_search_when_fetch_returns_ok_and_nonempty_list(monkeypatch, sample_list_of_dicts):
    """Should return OK if fetch yields non-empty list with OK status."""

    def fake_fetch(self, postal_code: str):
        return (sample_list_of_dicts, SearchResponseStatus.OK)

    # Monkey‐patch OneMapApiClient.fetch to return our sample list
    monkeypatch.setattr(OneMapApiClient, "fetch", fake_fetch)

    client = OneMapClient()
    result = client.search("528513")

    assert isinstance(result, OneMapSearchResult)
    assert result.raw_query == "528513"
    assert result.result_addrs == sample_list_of_dicts
    assert result.status == SearchResponseStatus.OK


def test_search_when_fetch_returns_ok_and_empty_list(monkeypatch):
    """Should return NOT_FOUND if fetch yields empty list with OK status."""

    def fake_fetch(self, postal_code: str):
        return ([], SearchResponseStatus.OK)

    monkeypatch.setattr(OneMapApiClient, "fetch", fake_fetch)

    client = OneMapClient()
    result = client.search("000000")

    assert result.raw_query == "000000"
    assert result.result_addrs == []
    assert result.status == SearchResponseStatus.NOT_FOUND


@pytest.mark.parametrize(
    "fetch_results, fetch_status, expected_status",
    [
        # Case 1: fetch returns (None, TIMEOUT)
        (None, SearchResponseStatus.TIMEOUT, SearchResponseStatus.TIMEOUT),
        # Case 2: fetch returns (None, ERROR)
        (None, SearchResponseStatus.ERROR, SearchResponseStatus.ERROR),
        # Case 3: fetch returns (None, RATE_LIMITED)
        (None, SearchResponseStatus.RATE_LIMITED, SearchResponseStatus.RATE_LIMITED),
        # Case 4: fetch returns (None, INVALID_API_RESPONSE)
        (None, SearchResponseStatus.INVALID_API_RESPONSE, SearchResponseStatus.INVALID_API_RESPONSE),
    ],
)
def test_search_when_fetch_returns_non_ok(fetch_results, fetch_status, expected_status, monkeypatch):
    """Should return matching non-OK status if fetch fails or is invalid."""

    def fake_fetch(self, postal_code: str):
        return (fetch_results, fetch_status)

    monkeypatch.setattr(OneMapApiClient, "fetch", fake_fetch)

    client = OneMapClient()
    result = client.search("any-postal")

    assert result.raw_query == "any-postal"
    assert result.result_addrs == []
    assert result.status == expected_status


def test_search_when_fetch_returns_none_and_ok(monkeypatch):
    """Should treat None + OK from fetch as INVALID_API_RESPONSE."""

    def fake_fetch(self, postal_code: str):
        return (None, SearchResponseStatus.OK)

    monkeypatch.setattr(OneMapApiClient, "fetch", fake_fetch)

    client = OneMapClient()
    result = client.search("ANY")

    assert result.raw_query == "ANY"
    assert result.result_addrs == []
    assert result.status == SearchResponseStatus.INVALID_API_RESPONSE  # <- updated!
