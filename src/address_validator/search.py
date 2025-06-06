"""
Base enums and abstract interfaces for address search clients and results.

Defines standard response statuses, result sources, and the base `SearchResult`
and `AddressSearchClient` interfaces for API implementations (e.g. OneMap, StreetDirectory).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class SearchResponseStatus(Enum):
    """
    Enum representing the status of a search query.

    Indicates whether the request was successful, failed, or hit API-specific issues.
    """

    OK = "ok"
    NOT_FOUND = "not_found"
    ERROR = "error"
    TIMEOUT = "timeout"
    INVALID_API_RESPONSE = "invalid_api_response"
    RATE_LIMITED = "rate_limited"


class SearchSrc(str, Enum):
    """
    Enum indicating which source the search result came from.

    Supports primary and hybrid sources (e.g. OneMap, StreetDirectory).
    """

    CACHE = "cache"
    ONEMAP = "onemap"
    STDIR = "streetdirectory"
    ONEMAP_STDIR = "onemap_streetdirectory"


@dataclass
class SearchResult(ABC):
    """
    Base class for structured search results returned from address providers.

    Attributes:
        raw_query (str): The original search query string.
        status (SearchResponseStatus): Status of the search result.
        timestamp (str): ISO 8601-formatted timestamp when the result was retrieved.
    """

    raw_query: str
    status: SearchResponseStatus
    timestamp: str  # e.g. ISO string from current_utc_isoformat()


class AddressSearchClient(ABC):
    """
    Abstract base class for address search clients.

    Concrete subclasses should implement provider-specific logic
    (e.g. OneMap, StreetDirectory) and return `SearchResult` subclasses.
    """

    @abstractmethod
    def search(self, address: str, **kwargs) -> SearchResult:
        """Search for the given address and return a subclass of SearchResult."""
        raise NotImplementedError
