"""
Tests for StreetDirectoryClient, parser, and search result behavior.

Covers HTML parsing, result factory logic, and optional real-time HTTP search.
"""

import textwrap

import pytest
import requests

from address_validator.search import SearchResponseStatus
from address_validator.streetdirectory_client import (
    StreetDirectoryApiClient,
    StreetDirectoryClient,
    StreetDirectorySearchResult,
)
from address_validator.utils.common import current_utc_isoformat

###################################################################################################
# Fixtures: Sample HTML snippets
###################################################################################################


@pytest.fixture
def sample_html_minimal():
    """Minimal HTML with two results for parsing tests."""
    return textwrap.dedent(
        """
    <div class="main_view_result arial">
      <div class="search_list">
        <div>
          <div class="search_label">Address</div> : A1 Road
        </div>
        <div class="category_row">
          <div class="search_label">Category</div> : CatA
        </div>
      </div>
    </div>

    <div class="main_view_result arial">
      <div class="search_list">
        <div>
          <div class="search_label">Address</div> : B2 Avenue
        </div>
        <div class="category_row">
          <div class="search_label">Category</div> : CatB
        </div>
      </div>
    </div>
    """
    )


@pytest.fixture
def sample_html_one():
    """One-entry HDB listing (real-world)."""
    return """
<div class="main_view_result arial" align="left">
  <div style="display: inline-block; margin: 10px 0 10px 0;">
    … <!-- ad code omitted -->
  </div>
  <div style="width:99%;margin:5px 1px 20px 1px;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr><td align="left">
        <a href="…/110247_111429.html" class="item_title_search">HDB Jurong East</a>
        <div>
          <div class="TextDarkGray ver_13">
            <div style="float:left; width:98%;" class="search_list">
              <div>
                <div class="search_label">Address </div>
                : <b>288E Jurong East Street 21</b> (S) 605288
              </div>
              <div></div>
              <div class="category_row">
                <div class="search_label">Category</div>
                : HDB Blocks
              </div>
            </div>
          </div>
        </div>
      </td></tr>
    </table>
  </div>
</div>
"""


@pytest.fixture
def sample_html_many():
    """Ten-entry mixed HDB, MSCP, and business listings."""
    return """
<div class="main_view_result arial" align="left">
    <div style="display: inline-block; margin: 10px 0 10px 0;">
        … <!-- Ad snippet omitted for brevity -->
    </div>

    <div style="width:99%;margin:5px 1px 20px 1px;">
        <table>…</table>
        <div style="float:left; width:70%;" class="search_list">
            <div><div class="search_label">Address </div> : 288A Jurong East Street 21 (S) 601288</div>
            <div class="category_row"><div class="search_label">Category</div> : HDB Blocks</div>
        </div>
    </div>

    <div style="width:99%;margin:5px 1px 20px 1px;">
        <table>…</table>
        <div class="search_list">
            <div><div class="search_label">Address </div> : 288B Jurong East Street 21 (S) 602288</div>
            <div class="category_row"><div class="search_label">Category</div> : HDB Blocks</div>
        </div>
    </div>

    <div style="width:99%;margin:5px 1px 20px 1px;">
        <table>…</table>
        <div class="search_list">
            <div><div class="search_label">Address </div> : 288C Jurong East Street 21 (S) 603288</div>
            <div class="category_row"><div class="search_label">Category</div> : HDB Blocks</div>
        </div>
    </div>

    <div style="width:99%;margin:5px 1px 20px 1px;">
        <table>…</table>
        <div class="search_list">
            <div><div class="search_label">Address </div> : 288D Jurong East Street 21 (S) 604288</div>
            <div class="category_row"><div class="search_label">Category</div> : HDB Blocks</div>
        </div>
    </div>

    <div style="width:99%;margin:5px 1px 20px 1px;">
        <table>…</table>
        <div class="search_list">
            <div><div class="search_label">Address </div> : 288E Jurong East Street 21 (S) 605288</div>
            <div class="category_row"><div class="search_label">Category</div> : HDB Blocks</div>
        </div>
    </div>

    <div style="width:99%;margin:5px 1px 20px 1px;">
        <table>…</table>
        <div class="search_list">
            <div><div class="search_label">Address </div> : 288F Jurong East Street 21 (S) 606288</div>
            <div class="category_row"><div class="search_label">Category</div> : Multi Storey Car Park (MSCP)</div>
        </div>
    </div>

    <div style="width:99%;margin:5px 1px 20px 1px;">
        <table>…</table>
        <div class="search_list">
            <div><div class="search_label">Address </div> : HDB Jurong East, 288B Jurong East Street 21 (S) 602288</div>
            <div class="category_row">Business dealing with Child Care Centre, Child Education, Daycare, etc</div>
        </div>
    </div>

    <div style="width:99%;margin:5px 1px 20px 1px;">
        <table>…</table>
        <div class="search_list">
            <div><div class="search_label">Address </div> : HDB Jurong East, 288C Jurong East Street 21 (S) 603288</div>
            <div class="category_row">Business dealing with Control Accessories, Electric, Electric Relay</div>
        </div>
    </div>

    <div style="width:99%;margin:5px 1px 20px 1px;">
        <table>…</table>
        <div class="search_list">
            <div><div class="search_label">Address </div> : HDB Jurong East, 288C Jurong East Street 21 (S) 603288</div>
            <div class="category_row">Business dealing with Building Construction, Building Construction Contractor, Kitchen Remodeling, etc</div>
        </div>
    </div>

    <div style="width:99%;margin:5px 1px 20px 1px;">
        <table>…</table>
        <div class="search_list">
            <div><div class="search_label">Address </div> : HDB Jurong East, 288A Jurong East Street 21 (S) 601288</div>
            <div class="category_row">Business dealing with Piano Course, Piano Lesson, Piano Teacher </div>
        </div>
    </div>
</div>
"""


# -----------------------------------------------------------------------------
# 1. Parsing tests: ensure the private `_parse_html` returns correct tuples
# -----------------------------------------------------------------------------


def test_parse_minimal(sample_html_minimal):
    """Parses two minimal entries correctly."""
    client = StreetDirectoryClient()
    # Bypass HTTP entirely by calling the parser directly:
    results = client._parse_html(sample_html_minimal, limit=None)

    assert results == [
        ("A1 Road", "CatA"),
        ("B2 Avenue", "CatB"),
    ]


def test_parse_one(sample_html_one):
    """Parses exactly one HDB listing from single block."""
    client = StreetDirectoryClient()
    results = client._parse_html(sample_html_one, limit=None)

    # Exactly one result:
    assert results == [("288E Jurong East Street 21 (S) 605288", "HDB Blocks")]


def test_parse_many(sample_html_many):
    """Parses 10 expected entries from full sample HTML."""
    client = StreetDirectoryClient()
    results = client._parse_html(sample_html_many, limit=None)

    # We expect 10 entries in the order given above:
    expected = [
        ("288A Jurong East Street 21 (S) 601288", "HDB Blocks"),
        ("288B Jurong East Street 21 (S) 602288", "HDB Blocks"),
        ("288C Jurong East Street 21 (S) 603288", "HDB Blocks"),
        ("288D Jurong East Street 21 (S) 604288", "HDB Blocks"),
        ("288E Jurong East Street 21 (S) 605288", "HDB Blocks"),
        ("288F Jurong East Street 21 (S) 606288", "Multi Storey Car Park (MSCP)"),
        (
            "HDB Jurong East, 288B Jurong East Street 21 (S) 602288",
            "Business dealing with Child Care Centre, Child Education, Daycare, etc",
        ),
        (
            "HDB Jurong East, 288C Jurong East Street 21 (S) 603288",
            "Business dealing with Control Accessories, Electric, Electric Relay",
        ),
        (
            "HDB Jurong East, 288C Jurong East Street 21 (S) 603288",
            "Business dealing with Building Construction, Building Construction Contractor, Kitchen Remodeling, etc",
        ),
        (
            "HDB Jurong East, 288A Jurong East Street 21 (S) 601288",
            "Business dealing with Piano Course, Piano Lesson, Piano Teacher",
        ),
    ]
    assert results == expected


###################################################################################################
# 2. Result‐factory tests: ensure from_parsed(...) behaves correctly
###################################################################################################


def test_from_parsed_with_none_or_empty():
    """Wraps OK + empty into NOT_FOUND; retains non-OK status."""
    now_before = current_utc_isoformat()
    res_none = StreetDirectorySearchResult.from_parsed("any", None, SearchResponseStatus.OK)
    assert res_none.raw_query == "any"
    assert res_none.items == []
    assert res_none.status == SearchResponseStatus.NOT_FOUND
    assert res_none.timestamp >= now_before

    res_empty = StreetDirectorySearchResult.from_parsed("any", [], SearchResponseStatus.OK)
    assert res_empty.raw_query == "any"
    assert res_empty.items == []
    assert res_empty.status == SearchResponseStatus.NOT_FOUND

    # If status is already ERROR/RATE_LIMITED, we wrap into that status (empty items)
    res_error = StreetDirectorySearchResult.from_parsed("q", [], SearchResponseStatus.ERROR)
    assert res_error.raw_query == "q"
    assert res_error.items == []
    assert res_error.status == SearchResponseStatus.ERROR


def test_from_parsed_with_nonempty_list(sample_html_minimal):
    """Wraps parsed list into OK result."""
    # Reuse the minimal HTML fixture to generate a parsed_addr list
    client = StreetDirectoryClient()
    parsed_addr = client._parse_html(sample_html_minimal, limit=None)
    assert parsed_addr  # should be nonempty

    res = StreetDirectorySearchResult.from_parsed("ignored", parsed_addr, SearchResponseStatus.OK)
    assert res.raw_query == "ignored"
    assert res.items == parsed_addr
    assert res.status == SearchResponseStatus.OK


###################################################################################################
# 3. “Factory” tests (HTTP calls) with monkeypatching
###################################################################################################


class DummyResponse:
    """A mock HTTP response object for testing StreetDirectoryApiClient."""

    def __init__(self, text, status_code=200):
        """Initialize the mock response with text content and a status code."""
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        """Raise HTTPError if status code is 400 or higher."""
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_search_factory_minimal(monkeypatch, sample_html_minimal):
    """Mocks HTTP and parses two entries."""

    def fake_fetch(self, address, country, state):
        return (sample_html_minimal, SearchResponseStatus.OK)

    monkeypatch.setattr(StreetDirectoryApiClient, "fetch_html", fake_fetch)

    client = StreetDirectoryClient()
    result = client.search("ignored", country="singapore", state=0, limit=None)

    # The client should parse the two entries and status should be OK
    assert isinstance(result, StreetDirectorySearchResult)
    assert result.raw_query == "ignored"
    assert result.items == [("A1 Road", "CatA"), ("B2 Avenue", "CatB")]
    assert result.status == SearchResponseStatus.OK


def test_search_factory_no_matches(monkeypatch):
    """Empty HTML returns NOT_FOUND."""

    def fake_fetch(self, address, country, state):
        # Minimal wrapper that returns HTML with no <div class="category_row">
        return ("<html><body>No results found</body></html>", SearchResponseStatus.OK)

    monkeypatch.setattr(StreetDirectoryApiClient, "fetch_html", fake_fetch)

    client = StreetDirectoryClient()
    result = client.search("anything", country="singapore", state=0, limit=None)

    assert result.raw_query == "anything"
    assert result.items == []  # no items parsed
    assert result.status == SearchResponseStatus.NOT_FOUND


@pytest.mark.parametrize(
    "fetch_return, expected_status",
    [
        ((None, SearchResponseStatus.TIMEOUT), SearchResponseStatus.TIMEOUT),
        ((None, SearchResponseStatus.ERROR), SearchResponseStatus.ERROR),
        ((None, SearchResponseStatus.RATE_LIMITED), SearchResponseStatus.RATE_LIMITED),
        ((None, SearchResponseStatus.INVALID_API_RESPONSE), SearchResponseStatus.INVALID_API_RESPONSE),
    ],
)
def test_search_factory_non_ok(fetch_return, expected_status, monkeypatch):
    """Client wraps non-OK status with empty items."""

    def fake_fetch(self, address, country, state):
        return fetch_return

    monkeypatch.setattr(StreetDirectoryApiClient, "fetch_html", fake_fetch)

    client = StreetDirectoryClient()
    result = client.search("whatever", country="singapore", state=0, limit=None)

    assert result.raw_query == "whatever"
    assert result.items == []  # no parse step at all
    assert result.status == expected_status


###################################################################################################
# 4. “Real‐request” tests (live HTTP) marked as slow
###################################################################################################


@pytest.mark.slow
def test_real_search_one():
    """Live test for known HDB block — should return one match."""
    client = StreetDirectoryClient()
    result = client.search(address="288E Jurong East Street 21", country="singapore", state=0, limit=None)
    # Verify the search operation was successful
    assert result.status == SearchResponseStatus.OK
    # Ensure exactly one result is returned
    assert isinstance(result.items, list)
    assert len(result.items) == 1
    # Verify the address and category of the result match the live site
    address, category = result.items[0]
    assert address == "288E Jurong East Street 21 (S) 605288"
    assert category == "HDB Blocks"


@pytest.mark.slow
def test_real_search_many():
    """Live test for full result set with 10 known matches."""
    client = StreetDirectoryClient()
    result = client.search("288 Jurong East Street 21", country="singapore", state=0, limit=None)

    assert result.status == SearchResponseStatus.OK

    expected = [
        ("288A Jurong East Street 21 (S) 601288", "HDB Blocks"),
        ("288B Jurong East Street 21 (S) 602288", "HDB Blocks"),
        ("288C Jurong East Street 21 (S) 603288", "HDB Blocks"),
        ("288D Jurong East Street 21 (S) 604288", "HDB Blocks"),
        ("288E Jurong East Street 21 (S) 605288", "HDB Blocks"),
        ("288F Jurong East Street 21 (S) 606288", "Multi Storey Car Park (MSCP)"),
        (
            "HDB Jurong East, 288B Jurong East Street 21 (S) 602288",
            "Business dealing with Child Care Centre , Child Education , Daycare , etc",
        ),
        (
            "HDB Jurong East, 288C Jurong East Street 21 (S) 603288",
            "Business dealing with Control Accessories , Electric , Electric Relay",
        ),
        (
            "HDB Jurong East, 288C Jurong East Street 21 (S) 603288",
            (
                "Business dealing with Building Construction , Building Construction Contractor , "
                "Kitchen Remodeling , etc"
            ),
        ),
        (
            "HDB Jurong East, 288A Jurong East Street 21 (S) 601288",
            "Business dealing with Piano Course , Piano Lesson , Piano Teacher",
        ),
    ]

    assert result.items == expected
