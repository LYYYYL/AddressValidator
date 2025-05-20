"""
This class queries streetdirectory.com for an address and scrapes the result using BeautifulSoup.
streetdirectory.com does not have a working resultAPI at the time of this implementation, so scraping is
used. Returns the property type that is used to determine whether a unit number is required for an address:
E.g. HDB, condo.
"""

import datetime
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

from address_validator.search import SearchResponseStatus


@dataclass
class StreetDirectorySearchResult:
    raw_query: str
    items: list[tuple[str | None, str]]  # List of (address, category)
    status: SearchResponseStatus
    fetched_at: datetime.datetime

    @classmethod
    def from_parsed(
        cls, raw_query: str, parsed: list[tuple[Optional[str], str]] | None, status: SearchResponseStatus
    ) -> "StreetDirectorySearchResult":
        """
        Factory that normalizes parsed output into a consistent object.
        - If parsed is None or empty and status is OK, we treat it as NOT_FOUND.
        - If parsed is a nonempty list, status remains OK.
        - If status passed in is already NOT_FOUND / ERROR / RATE_LIMITED, we wrap accordingly.
        """
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if status == SearchResponseStatus.OK:
            # If the API said “OK” but parsing returned no items, treat as NOT_FOUND.
            if not parsed:
                return cls(raw_query, [], SearchResponseStatus.NOT_FOUND, now)
            return cls(raw_query, parsed, SearchResponseStatus.OK, now)

        # Any other status—just wrap an empty list.
        return cls(raw_query, [], status, now)


class StreetDirectoryApiClient:
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
        Retry whenever we get back a (None, RATE_LIMITED) or (None, ERROR).
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
        Perform the HTTP GET to StreetDirectory. If we hit a timeout/connection error/429/5xx,
        return (None, appropriate_status) so that tenacity can decide whether to retry.
        On success (status_code 200–299), return (html_text, OK).
        On 400–499 (excluding 429), treat as ERROR (no retry).
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
    # ─── Private class constants ─────────────────────────────────────────────
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
        Given raw StreetDirectory HTML, return up to `limit` (address, category) pairs.
        Using the “private” class constants above so they never escape this class.
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
        raw_html, status = self.api.fetch_html(address, country, state)

        if status != SearchResponseStatus.OK or raw_html is None:
            return StreetDirectorySearchResult.from_parsed(address, None, status)

        parsed_items = self._parse_html(raw_html, limit)
        return StreetDirectorySearchResult.from_parsed(address, parsed_items, SearchResponseStatus.OK)
