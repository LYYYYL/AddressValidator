import datetime
import textwrap

import pytest
import requests

from address_validator.search import SearchResponseStatus
from address_validator.streetdirectory_client import (
    StreetDirectoryApiClient,
    StreetDirectoryClient,
    StreetDirectorySearchResult,
)

# -----------------------------------------------------------------------------
# Fixtures: Sample HTML snippets (same as before but now used by the new parser)
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_html_minimal():
    """Minimal snippet with two results for parsing‐and‐factory tests."""
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
    """A real-world snippet with exactly one HDB block (bold tag around the address)."""
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
    """A real-page snippet with ten entries—five HDB blocks, one MSCP, and four business listings."""
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
    client = StreetDirectoryClient()
    # Bypass HTTP entirely by calling the parser directly:
    results = client._parse_html(sample_html_minimal, limit=None)

    assert results == [
        ("A1 Road", "CatA"),
        ("B2 Avenue", "CatB"),
    ]


def test_parse_one(sample_html_one):
    client = StreetDirectoryClient()
    results = client._parse_html(sample_html_one, limit=None)

    # Exactly one result:
    assert results == [("288E Jurong East Street 21 (S) 605288", "HDB Blocks")]


def test_parse_many(sample_html_many):
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


# -----------------------------------------------------------------------------
# 2. Result‐factory tests: ensure from_parsed(...) behaves correctly
# -----------------------------------------------------------------------------


def test_from_parsed_with_none_or_empty():
    """If parsed is None or [] but status is OK, it should become NOT_FOUND."""
    now_before = datetime.datetime.now(tz=datetime.timezone.utc)
    res_none = StreetDirectorySearchResult.from_parsed("any", None, SearchResponseStatus.OK)
    assert res_none.raw_query == "any"
    assert res_none.items == []
    assert res_none.status == SearchResponseStatus.NOT_FOUND
    assert isinstance(res_none.fetched_at, datetime.datetime)
    assert res_none.fetched_at >= now_before

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
    """If parsed list is nonempty and status is OK, status remains OK."""
    # Reuse the minimal HTML fixture to generate a parsed list
    client = StreetDirectoryClient()
    parsed = client._parse_html(sample_html_minimal, limit=None)
    assert parsed  # should be nonempty

    res = StreetDirectorySearchResult.from_parsed("ignored", parsed, SearchResponseStatus.OK)
    assert res.raw_query == "ignored"
    assert res.items == parsed
    assert res.status == SearchResponseStatus.OK
    assert isinstance(res.fetched_at, datetime.datetime)


# -----------------------------------------------------------------------------
# 3. “Factory” tests (HTTP calls) with monkeypatching
# -----------------------------------------------------------------------------


class DummyResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_search_factory_minimal(monkeypatch, sample_html_minimal):
    """
    If fetch_html(...) returns (minimal HTML, OK), then
    client.search(...) should wrap that into a StreetDirectorySearchResult
    with exactly two items.
    """

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
    assert isinstance(result.fetched_at, datetime.datetime)


def test_search_factory_no_matches(monkeypatch):
    """
    If fetch_html returns ("<empty page>", OK), parsed is [], so status → NOT_FOUND.
    """

    def fake_fetch(self, address, country, state):
        # Minimal wrapper that returns HTML with no <div class="category_row">
        return ("<html><body>No results found</body></html>", SearchResponseStatus.OK)

    monkeypatch.setattr(StreetDirectoryApiClient, "fetch_html", fake_fetch)

    client = StreetDirectoryClient()
    result = client.search("anything", country="singapore", state=0, limit=None)

    assert result.raw_query == "anything"
    assert result.items == []  # no items parsed
    assert result.status == SearchResponseStatus.NOT_FOUND
    assert isinstance(result.fetched_at, datetime.datetime)


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
    """
    If fetch_html(...) returns (None, some_non_OK_status), then search → that status, empty items.
    """

    def fake_fetch(self, address, country, state):
        return fetch_return

    monkeypatch.setattr(StreetDirectoryApiClient, "fetch_html", fake_fetch)

    client = StreetDirectoryClient()
    result = client.search("whatever", country="singapore", state=0, limit=None)

    assert result.raw_query == "whatever"
    assert result.items == []  # no parse step at all
    assert result.status == expected_status
    assert isinstance(result.fetched_at, datetime.datetime)


# -----------------------------------------------------------------------------
# 4. “Real‐request” tests (live HTTP) marked as slow
# -----------------------------------------------------------------------------


@pytest.mark.slow
def test_real_search_one():
    """
    Live‐site check: “288E Jurong East Street 21” should return exactly one HDB block.
    """
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
    """
    Live‐site check: “288 Jurong East Street 21” should return exactly the full set of 10 entries.
    We assert against the complete expected list below.
    """
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
            "Business dealing with Building Construction , Building Construction Contractor , Kitchen Remodeling , etc",
        ),
        (
            "HDB Jurong East, 288A Jurong East Street 21 (S) 601288",
            "Business dealing with Piano Course , Piano Lesson , Piano Teacher",
        ),
    ]

    assert result.items == expected
