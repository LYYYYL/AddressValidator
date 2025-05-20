# tests/unit_tests/test_onemap_client.py

import datetime

import pytest

from address_validator.onemap_client import OneMapApiClient, OneMapClient, OneMapSearchResult
from address_validator.search import SearchResponseStatus

# ────────────────────────────────────────────────────────────────────────────────
# Helpers / Fixtures
# ────────────────────────────────────────────────────────────────────────────────


class DummyFetchResult:
    """
    A fake container for (results, status) pairs. Not strictly necessary,
    but keeps our intent clear when we patch OneMapApiClient.fetch.
    """

    def __init__(self, results, status):
        self.results = results
        self.status = status

    def as_tuple(self):
        return (self.results, self.status)


@pytest.fixture
def sample_list_of_dicts():
    """
    A “normal” case: OneMap API returns a non‐empty list of address‐dicts.
    Each dict uses the ONEMAP_* keys (e.g. ROAD_NAME, POSTAL).
    """
    return [{"ROAD_NAME": "Main Street", "POSTAL": "123456"}]


# ────────────────────────────────────────────────────────────────────────────────
# Tests for OneMapSearchResult.from_results(...)
# ────────────────────────────────────────────────────────────────────────────────


def test_from_results_none_returns_not_found_and_empty_list():
    raw = "S123456"
    result = OneMapSearchResult.from_results(raw_addr=raw, results=None)

    assert isinstance(result, OneMapSearchResult)
    assert result.raw_addr == raw
    assert result.result_addrs == []  # no addresses
    assert result.status == SearchResponseStatus.NOT_FOUND
    assert isinstance(result.validated_at, datetime.datetime)


def test_from_results_empty_list_returns_not_found_and_empty_list():
    raw = "S000000"
    result = OneMapSearchResult.from_results(raw_addr=raw, results=[])

    assert result.raw_addr == raw
    assert result.result_addrs == []  # still no addresses
    assert result.status == SearchResponseStatus.NOT_FOUND
    assert isinstance(result.validated_at, datetime.datetime)


def test_from_results_nonempty_list_returns_ok_and_preserves_list(sample_list_of_dicts):
    raw = "528513"
    results = sample_list_of_dicts.copy()
    result = OneMapSearchResult.from_results(raw_addr=raw, results=results)

    assert result.raw_addr == raw
    assert result.result_addrs == results  # exactly the same list
    assert result.status == SearchResponseStatus.OK
    assert isinstance(result.validated_at, datetime.datetime)


def test_from_results_unexpected_type_returns_invalid_api_response():
    raw = "ABC123"
    bogus = {"unexpected_key": "unexpected_value"}  # not a list or None
    result = OneMapSearchResult.from_results(raw_addr=raw, results=bogus)

    assert result.raw_addr == raw
    assert result.result_addrs == []  # fallback to empty list
    assert result.status == SearchResponseStatus.INVALID_API_RESPONSE
    assert isinstance(result.validated_at, datetime.datetime)


# ────────────────────────────────────────────────────────────────────────────────
# Tests for OneMapClient.search(...)
# ────────────────────────────────────────────────────────────────────────────────


def test_search_when_fetch_returns_ok_and_nonempty_list(monkeypatch, sample_list_of_dicts):
    """
    If OneMapApiClient.fetch(...) yields (list_of_dicts, OK),
    then OneMapClient.search(...) should wrap that in a OneMapSearchResult with status OK.
    """

    def fake_fetch(self, postal_code: str):
        return (sample_list_of_dicts, SearchResponseStatus.OK)

    # Monkey‐patch OneMapApiClient.fetch to return our sample list
    monkeypatch.setattr(OneMapApiClient, "fetch", fake_fetch)

    client = OneMapClient()
    result = client.search("528513")

    assert isinstance(result, OneMapSearchResult)
    assert result.raw_addr == "528513"
    assert result.result_addrs == sample_list_of_dicts
    assert result.status == SearchResponseStatus.OK
    assert isinstance(result.validated_at, datetime.datetime)


def test_search_when_fetch_returns_ok_and_empty_list(monkeypatch):
    """
    If OneMapApiClient.fetch(...) yields ([], OK),
    then OneMapClient.search(...) should treat that as NOT_FOUND.
    """

    def fake_fetch(self, postal_code: str):
        return ([], SearchResponseStatus.OK)

    monkeypatch.setattr(OneMapApiClient, "fetch", fake_fetch)

    client = OneMapClient()
    result = client.search("000000")

    assert result.raw_addr == "000000"
    assert result.result_addrs == []
    assert result.status == SearchResponseStatus.NOT_FOUND
    assert isinstance(result.validated_at, datetime.datetime)


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
    """
    If OneMapApiClient.fetch(...) yields (None, some_non_OK_status), then
    OneMapClient.search(...) should return a OneMapSearchResult where:
      - raw_addr is the same
      - result_addrs = []
      - status = that same non‐OK status
      - validated_at is a datetime
    """

    def fake_fetch(self, postal_code: str):
        return (fetch_results, fetch_status)

    monkeypatch.setattr(OneMapApiClient, "fetch", fake_fetch)

    client = OneMapClient()
    result = client.search("any-postal")

    assert result.raw_addr == "any-postal"
    assert result.result_addrs == []
    assert result.status == expected_status
    assert isinstance(result.validated_at, datetime.datetime)


def test_search_when_fetch_returns_none_and_ok(monkeypatch):
    """
    If OneMapApiClient.fetch(...) yields (None, OK),
    then OneMapClient.search(...) should ask OneMapSearchResult.from_results(None) → NOT_FOUND.
    """

    def fake_fetch(self, postal_code: str):
        return (None, SearchResponseStatus.OK)

    monkeypatch.setattr(OneMapApiClient, "fetch", fake_fetch)

    client = OneMapClient()
    result = client.search("ANY")

    assert result.raw_addr == "ANY"
    # OneMapSearchResult.from_results(None, OK) → status NOT_FOUND, empty list
    assert result.result_addrs == []
    assert result.status == SearchResponseStatus.NOT_FOUND
    assert isinstance(result.validated_at, datetime.datetime)
