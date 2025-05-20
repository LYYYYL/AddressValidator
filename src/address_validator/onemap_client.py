import datetime
from dataclasses import dataclass

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

from address_validator.search import SearchResponseStatus

ONEMAP_STREET_KEY = "ROAD_NAME"
ONEMAP_BLK_NO_KEY = "BLK_NO"
ONEMAP_POSTCODE_KEY = "POSTAL"


@dataclass
class OneMapSearchResult:
    raw_addr: str
    result_addrs: list[dict[str, str]]
    status: SearchResponseStatus
    validated_at: datetime.datetime

    @classmethod
    def from_results(cls, raw_addr: str, results: dict | None) -> "OneMapSearchResult":
        now = datetime.datetime.now(datetime.UTC)
        if results is None:
            return cls(raw_addr, [], SearchResponseStatus.NOT_FOUND, now)
        if isinstance(results, list):
            if not results:
                return cls(raw_addr, [], SearchResponseStatus.NOT_FOUND, now)
            return cls(raw_addr, results, SearchResponseStatus.OK, now)
        return cls(raw_addr, [], SearchResponseStatus.INVALID_API_RESPONSE, now)


class OneMapApiClient:
    BASE_URL = "https://www.onemap.gov.sg/api/common/elastic/search"
    headers = {"Authorization": "Bearer **********************"}

    def __init__(self):
        pass

    @staticmethod
    def _should_retry_response(result: tuple[dict | None, SearchResponseStatus]) -> bool:
        """
        Return True if the returned status is one we want to retry on:
        RATE_LIMITED or ERROR (5xx).
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
        Contact OneMap’s search API. If we hit a timeout, connection error, 429, or 5xx,
        tenacity will retry automatically up to 5 times with exponential backoff.
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
    def __init__(self):
        self.api = OneMapApiClient()

    def search(self, address: str) -> OneMapSearchResult:
        results, status = self.api.fetch(address)
        if status == SearchResponseStatus.OK:
            return OneMapSearchResult.from_results(address, results)
        return OneMapSearchResult(address, [], status, datetime.datetime.now(datetime.UTC))
