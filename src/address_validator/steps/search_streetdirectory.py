"""
Validation step for querying and filtering StreetDirectory search results.

This module defines a `SearchStreetDirectoryStep` that uses the StreetDirectoryClient
to query address data based on OneMap-derived address parts (block, street, and postal code).
The results are filtered to exclude certain categories and substrings defined in constants.
Filtered results are stored in the context, or appropriate validation statuses are set if
the search fails or returns no acceptable matches.
"""

import address_validator.streetdirectory_client as sd_client_module
from address_validator.constants import (
    ONEMAP_RESULTS_BY_POSTCODE,
    STREETDIR_CATEGORY_SUBSTRING_EXCLUSIONS,
    STREETDIR_EXACT_CATEGORY_EXCLUSIONS,
    STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS,
    VALIDATE_STATUS,
)
from address_validator.steps.base import ValidationStep
from address_validator.streetdirectory_client import (
    SearchResponseStatus,
    StreetDirectorySearchResult,
)
from address_validator.utils.common import extract_address_query_parts


class SearchStreetDirectoryStep(ValidationStep):
    """
    A validation step that queries StreetDirectory using parsed address components.

    This step constructs a query string from OneMap-derived or parsed block, street, and postal code.
    It calls the `StreetDirectoryClient` to search for matching addresses. The returned results are:
    - Validated for API status.
    - Filtered to exclude certain categories defined by exact matches or substrings.
    - Stored in the context if valid results remain.

    If the query fails, returns no results, or all results are excluded, an appropriate `ValidateStatus`
    is set in the context to reflect the failure reason.

    This step helps enhance address validation by cross-referencing StreetDirectory's
    business and residential listings.
    """

    def __call__(self, ctx: dict) -> dict:
        """
        Executes the StreetDirectory search step in the validation pipeline.

        Args:
            ctx (dict): Validation context containing parsed or OneMap address components.

        Returns:
            dict: Updated context including:
                - Filtered StreetDirectory results (if any),
                - Or a validation status indicating failure or no matches.

        Behavior:
            - Extracts (blk, street, postcode) from context using OneMap or fallback parser.
            - Forms a query string and sends it to StreetDirectoryClient.
            - Filters results based on configured category exclusions.
            - Updates context with results or error status accordingly.
        """
        blk, street, pcode = extract_address_query_parts(
            ctx,
            prefer_onemap=True,
            onemap_key=ONEMAP_RESULTS_BY_POSTCODE,
            fallback_to_parsed=True,
        )

        if not any([blk, street, pcode]):
            return ctx

        # Build the query exactly as "<blk>, <street>, <postcode>"
        query = f"{blk}, {street}, {pcode}"

        sd_client = sd_client_module.StreetDirectoryClient()
        sd_result: StreetDirectorySearchResult = sd_client.search(
            address=query,
            country="singapore",
            state=0,
            limit=None,
        )

        # 1) If non‐OK status, propagate it
        if sd_result.status != SearchResponseStatus.OK:
            ctx[VALIDATE_STATUS] = sd_result.status.value
            return ctx

        # 2) If OK but no items at all, “no match”
        if not sd_result.items:
            return ctx

        # 3) Filter out any unwanted categories
        filtered_items = []
        for addr_text, category in sd_result.items:
            # Skip if exact match in the exclusion set
            if category in STREETDIR_EXACT_CATEGORY_EXCLUSIONS:
                continue

            # Skip if any of the substrings appear in the category string
            if any(substr in category for substr in STREETDIR_CATEGORY_SUBSTRING_EXCLUSIONS):
                continue

            filtered_items.append((addr_text, category))

        # 4) If nothing remains, treat as “no match”
        if not filtered_items:
            return ctx

        # 5) Otherwise save the filtered list
        ctx[STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS] = filtered_items
        return ctx


search_streetdirectory_step = SearchStreetDirectoryStep()
