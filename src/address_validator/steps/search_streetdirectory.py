# src/address_validator/steps/search_streetdirectory.py

import address_validator.streetdirectory_client as sd_client_module
from address_validator.constants import (
    STREETDIR_CATEGORY_SUBSTRING_EXCLUSIONS,
    STREETDIR_EXACT_CATEGORY_EXCLUSIONS,
)
from address_validator.onemap_client import (
    ONEMAP_BLK_NO_KEY,
    ONEMAP_POSTCODE_KEY,
    ONEMAP_STREET_KEY,
)
from address_validator.steps.base import ValidationStep
from address_validator.streetdirectory_client import (
    SearchResponseStatus,
    StreetDirectorySearchResult,
)
from address_validator.validation import ValidateStatus


class SearchStreetDirectoryStep(ValidationStep):
    """
    Query StreetDirectory using the first element of onemap_data and save all results,
    handling fetch errors via the new StreetDirectoryClient.search(...) facade.
    Excludes any result whose category is exactly one of STREETDIR_EXACT_CATEGORY_EXCLUSIONS
    or contains any substring from STREETDIR_CATEGORY_SUBSTRING_EXCLUSIONS.
    """

    def __call__(self, ctx: dict) -> dict:
        onemap_data = ctx.get("onemap_data") or []
        if not onemap_data:
            return ctx

        first = onemap_data[0]
        blk = first.get(ONEMAP_BLK_NO_KEY, "")
        if blk == "NIL":
            blk = ""
        street = first.get(ONEMAP_STREET_KEY, "")
        pcode = first.get(ONEMAP_POSTCODE_KEY, "")

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
            ctx["validate_status"] = sd_result.status.value
            return ctx

        # 2) If OK but no items at all, “no match”
        if not sd_result.items:
            ctx["validate_status"] = ValidateStatus.NO_STREETDIRECTORY_MATCH
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
            ctx["validate_status"] = ValidateStatus.NO_STREETDIRECTORY_MATCH
            return ctx

        # 5) Otherwise save the filtered list
        ctx["streetdirectory_results"] = filtered_items
        return ctx


search_streetdirectory_step = SearchStreetDirectoryStep()
