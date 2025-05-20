from enum import Enum


class SearchResponseStatus(Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    ERROR = "error"
    TIMEOUT = "timeout"
    INVALID_API_RESPONSE = "invalid_api_response"
    RATE_LIMITED = "rate_limited"


class SearchSrc(str, Enum):
    CACHE = "cache"
    ONEMAP = "onemap"
    STDIR = "streetdirectory"
    ONEMAP_STDIR = "onemap_streetdirectory"


# @dataclass
# class SearchResult:
