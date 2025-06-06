"""
StreetDirectory scraping client for property-type classification.

Since streetdirectory.com does not offer a working address result API, this module
uses HTML scraping via BeautifulSoup to extract the category (e.g., HDB, Condo, School)
for a given address. Categories are used to infer whether unit numbers are required.
"""

from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

from address_validator.search import SearchResponseStatus, SearchResult
from address_validator.utils.common import current_utc_isoformat


@dataclass
class StreetDirectorySearchResult(SearchResult):
    """
    A search result returned by the StreetDirectory scraping client.

    Attributes:
        items (list): A list of (address, category) tuples.
    """

    items: list[tuple[str | None, str]]  # List of (address, category)

    @classmethod
    def from_parsed(
        cls, raw_query: str, parsed_addr: list[tuple[str | None, str]] | None, status: SearchResponseStatus
    ) -> "StreetDirectorySearchResult":
        """
        Build a result object from parsed items and a given status.

        Args:
            raw_query (str): The original query string.
            parsed_addr (list | None): Parsed (address, category) pairs.
            status (SearchResponseStatus): The status of the fetch.

        Returns:
            StreetDirectorySearchResult: A structured result object.
        """
        now = current_utc_isoformat()
        if status == SearchResponseStatus.OK and parsed_addr:
            return cls(
                raw_query=raw_query,
                status=SearchResponseStatus.OK,
                timestamp=now,
                items=parsed_addr,
            )
        return cls(
            raw_query=raw_query,
            status=SearchResponseStatus.NOT_FOUND if status == SearchResponseStatus.OK else status,
            timestamp=now,
            items=[],
        )


class StreetDirectoryApiClient:
    """Handles low-level HTTP requests to streetdirectory.com with retry logic."""

    BASE_URL = "https://www.streetdirectory.com/asia_travel/search/"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    }
    TIMEOUT = 10.0  # seconds

    @staticmethod
    def _should_retry(result: tuple[Optional[str], SearchResponseStatus]) -> bool:
        """
        Decide whether to retry based on the result status.

        Args:
            result (tuple): A (response_text, status) tuple.

        Returns:
            bool: True if retry should occur, else False.
        """
        _, status = result
        return status in {SearchResponseStatus.RATE_LIMITED, SearchResponseStatus.ERROR}

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=(
            retry_if_exception_type(requests.exceptions.Timeout)
            | retry_if_exception_type(requests.exceptions.ConnectionError)
            | retry_if_result(_should_retry)
        ),
        reraise=True,
    )
    def fetch_html(self, address: str, country: str, state: int) -> tuple[str | None, SearchResponseStatus]:
        """
        Send a GET request to StreetDirectory and return raw HTML on success.

        Args:
            address (str): The address to search.
            country (str): Country name (e.g., 'singapore').
            state (int): State ID (usually 0).

        Returns:
            tuple: (HTML string or None, SearchResponseStatus)
        """
        params = {"q": address, "country": country, "state": state}
        try:
            response = requests.get(
                StreetDirectoryApiClient.BASE_URL,
                params=params,
                headers=StreetDirectoryApiClient.HEADERS,
                timeout=StreetDirectoryApiClient.TIMEOUT,
            )
        except requests.exceptions.Timeout:
            return None, SearchResponseStatus.TIMEOUT
        except requests.exceptions.ConnectionError:
            return None, SearchResponseStatus.ERROR
        except requests.exceptions.RequestException:
            return None, SearchResponseStatus.ERROR

        code = response.status_code
        if code == 429:
            return None, SearchResponseStatus.RATE_LIMITED
        if 500 <= code < 600:
            return None, SearchResponseStatus.ERROR
        if 400 <= code < 500:
            return None, SearchResponseStatus.ERROR

        try:
            return response.text, SearchResponseStatus.OK
        except Exception:
            return None, SearchResponseStatus.INVALID_API_RESPONSE


class StreetDirectoryClient:
    """High-level client to scrape and extract property categories from StreetDirectory."""

    _CATEGORY_SELECTOR = "div.main_view_result div.category_row"
    _ADDRESS_CONTAINER_CLASS = "search_list"
    _FIELD_LABEL_CLASS = "search_label"
    _ADDRESS_FIELD_LABEL = "Address"

    def __init__(self):
        self.api = StreetDirectoryApiClient()

    def _extract_after_colon(self, elem) -> str:
        text = elem.get_text(" ", strip=True)
        _, sep, after = text.partition(":")
        return after.strip() if sep else text

    def _parse_html(self, html: str, limit: int | None = 1) -> list[tuple[str | None, str]]:
        """
        Parse raw HTML and extract (address, category) results.

        Args:
            html (str): Raw HTML returned from StreetDirectory.
            limit (int | None): Max number of results to return.

        Returns:
            list: List of (address, category) pairs.
        """
        soup = BeautifulSoup(html, "html.parser")
        results: list[tuple[Optional[str], str]] = []

        # Notice we reference the class attributes via `self._CATEGORY_SELECTOR`
        for cat_div in soup.select(self._CATEGORY_SELECTOR):
            category = self._extract_after_colon(cat_div)

            search_list_div = cat_div.find_parent("div", class_=self._ADDRESS_CONTAINER_CLASS)
            address: Optional[str] = None
            if search_list_div:
                for child in search_list_div.find_all("div", recursive=False):
                    label = child.find("div", class_=self._FIELD_LABEL_CLASS)
                    if label and self._ADDRESS_FIELD_LABEL in label.get_text():
                        address = self._extract_after_colon(child)
                        break

            results.append((address, category))
            if limit is not None and len(results) >= limit:
                break

        return results

    def search(
        self,
        address: str,
        country: str = "singapore",
        state: int = 0,
        limit: int | None = 1,
    ) -> StreetDirectorySearchResult:
        """
        Perform a search query and return structured result with property category.

        Args:
            address (str): The full address string to search.
            country (str): Country to include in the query.
            state (int): Optional state ID.
            limit (int | None): Max number of result pairs to return.

        Returns:
            StreetDirectorySearchResult: Structured result with categories.
        """
        raw_html, status = self.api.fetch_html(address, country, state)

        if status != SearchResponseStatus.OK or raw_html is None:
            return StreetDirectorySearchResult.from_parsed(address, None, status)

        parsed_items = self._parse_html(raw_html, limit)
        return StreetDirectorySearchResult.from_parsed(address, parsed_items, SearchResponseStatus.OK)
