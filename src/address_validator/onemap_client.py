"""
OneMap API client and result handler for postal code-based address lookup.

This module provides a retryable API client (`OneMapApiClient`) for calling
Singapore's OneMap address search API, and a wrapper (`OneMapClient`) that
returns a `OneMapSearchResult` used by the validation system.
"""

from dataclasses import dataclass

import requests
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
class OneMapSearchResult(SearchResult):
    """
    Wrapper for OneMap search results.

    Attributes:
        result_addrs (list[dict[str, str]]): List of matched address dictionaries.
    """

    result_addrs: list[dict[str, str]]

    @classmethod
    def from_results(cls, raw_query: str, results: dict | None) -> "OneMapSearchResult":
        """
        Convert raw API response to a structured `OneMapSearchResult`.

        Args:
            raw_query (str): The address or postal code that was queried.
            results (dict | None): Raw results returned from OneMap.

        Returns:
            OneMapSearchResult: Structured and timestamped result object.
        """
        now = current_utc_isoformat()
        if results is None or not isinstance(results, list):
            return cls(
                raw_query=raw_query,
                result_addrs=[],
                status=SearchResponseStatus.INVALID_API_RESPONSE,
                timestamp=now,
            )
        if not results:
            return cls(
                raw_query=raw_query,
                result_addrs=[],
                status=SearchResponseStatus.NOT_FOUND,
                timestamp=now,
            )
        return cls(
            raw_query=raw_query,
            result_addrs=results,
            status=SearchResponseStatus.OK,
            timestamp=now,
        )


class OneMapApiClient:
    """
    Low-level API client for OneMap's postal code and address search endpoint.

    Automatically retries requests on transient failures (e.g., timeout, rate limit, 5xx errors)
    using exponential backoff.
    """

    BASE_URL = "https://www.onemap.gov.sg/api/common/elastic/search"
    headers = {"Authorization": "Bearer **********************"}

    def __init__(self):
        pass

    @staticmethod
    def _should_retry_response(result: tuple[dict | None, SearchResponseStatus]) -> bool:
        """
        Determine whether a response status code should trigger a retry.

        Args:
            result (tuple): A (response, status) tuple.

        Returns:
            bool: True if the response should be retried, False otherwise.
        """
        _, status = result
        return status in {SearchResponseStatus.RATE_LIMITED, SearchResponseStatus.ERROR}

    @retry(
        # Stop retrying after 5 attempts
        stop=stop_after_attempt(5),
        # Exponential backoff: wait 1s, 2s, 4s, 8s, up to 10s
        wait=wait_exponential(multiplier=1, min=1, max=10),
        # Retry if a Timeout or ConnectionError exception is raised,
        # or if our function returns (None, RATE_LIMITED/ERROR)
        retry=(
            retry_if_exception_type(requests.exceptions.Timeout)
            | retry_if_exception_type(requests.exceptions.ConnectionError)
            | retry_if_result(_should_retry_response)
        ),
        reraise=True,
    )
    def fetch(self, postal_code: str) -> tuple[dict | None, SearchResponseStatus]:
        """
        Query OneMap's address search API with a postal code.

        Applies automatic retries for known transient errors using Tenacity.

        Args:
            postal_code (str): The postal code to search.

        Returns:
            tuple: (results list or None, status code)
        """
        params = {
            "searchVal": postal_code,
            "returnGeom": "Y",
            "getAddrDetails": "Y",
            "pageNum": 1,
        }

        try:
            response = requests.get(self.BASE_URL, headers=self.headers, params=params, timeout=5.0)
        except requests.exceptions.Timeout:
            # This exception is caught by tenacity and retried
            return None, SearchResponseStatus.TIMEOUT
        except requests.exceptions.ConnectionError:
            # Similarly retried by tenacity
            return None, SearchResponseStatus.ERROR
        except requests.exceptions.RequestException:
            # Any other transport‐level error → treat as generic ERROR
            return None, SearchResponseStatus.ERROR

        status_code = response.status_code

        # Rate‐limited → retry
        if status_code == 429:
            return None, SearchResponseStatus.RATE_LIMITED
        # Server error (5xx) → retry
        if 500 <= status_code < 600:
            return None, SearchResponseStatus.ERROR
        # Client error (4xx, excluding 429) → do not retry
        if 400 <= status_code < 500:
            return None, SearchResponseStatus.ERROR

        # Otherwise, parse JSON
        try:
            results = response.json().get("results")
        except ValueError:
            # Invalid JSON → do not retry (invalid API response)
            return None, SearchResponseStatus.INVALID_API_RESPONSE

        return results, SearchResponseStatus.OK


class OneMapClient:
    """High-level client for OneMap that returns `OneMapSearchResult` objects."""

    def __init__(self):
        self.api = OneMapApiClient()

    def search(self, address: str) -> OneMapSearchResult:
        """
        Run a OneMap search query and return a structured result object.

        Args:
            address (str): Address string or postal code to search.

        Returns:
            OneMapSearchResult: Result object with addresses and status.
        """
        results, status = self.api.fetch(address)
        if status == SearchResponseStatus.OK:
            return OneMapSearchResult.from_results(raw_query=address, results=results)

        return OneMapSearchResult(
            raw_query=address,
            result_addrs=[],
            status=status,
            timestamp=current_utc_isoformat(),
        )
