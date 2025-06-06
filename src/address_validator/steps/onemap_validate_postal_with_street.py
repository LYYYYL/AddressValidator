"""
Validation step to cross-check postal code using block, street, and building name.

This step sends a query to OneMap using the parsed block number, street name,
and building name. It compares the returned postal codes against the parsed one.
If there is a mismatch or no match, an appropriate `VALIDATE_STATUS` is set.
"""

from address_validator.constants import (
    BLOCK_NUMBER,
    BUILDING_NAME,
    ONEMAP_POSTAL_CODE,
    ONEMAP_RESULTS_BY_ADDRESS,
    PARSED_ADDRESS,
    POSTAL_CODE,
    STREET_NAME,
    VALIDATE_STATUS,
)
from address_validator.onemap_client import OneMapClient
from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class OneMapValidatePostalWithStreetStep(ValidationStep):
    """
    Validates postal code by cross-checking OneMap results from full address input.

    This step builds a search string using block number, street name, and building name,
    queries OneMap for matches, and ensures the parsed postal code is present in the results.
    """

    def __call__(self, ctx: dict) -> dict:
        """
        Validate that the parsed postal code matches the OneMap result based on street search.

        The step:
        1. Constructs a search string from block, street, and building.
        2. Queries OneMap.
        3. Checks whether the returned postal codes include the parsed one.
        4. Sets `VALIDATE_STATUS` if no match is found or if the API fails.

        Args:
            ctx (dict): The current address validation context.

        Returns:
            dict: Updated context with OneMap results and possibly a validation status.
        """
        # obtain individual address fields using user's input
        parsed_addr = ctx.get(PARSED_ADDRESS, {})
        blk = parsed_addr.get(BLOCK_NUMBER)
        street = parsed_addr.get(STREET_NAME)
        building = parsed_addr.get(BUILDING_NAME)
        postcode = parsed_addr.get(POSTAL_CODE)

        # form a query using only block number, street name and building, but no postal code
        if building is None:
            building = ""
        search_field = f"{blk} {street} {building}"

        # query OneMap
        result = OneMapClient().search(search_field)
        ctx[ONEMAP_RESULTS_BY_ADDRESS] = result.result_addrs
        if result.status != result.status.OK:
            ctx[VALIDATE_STATUS] = result.status
            return ctx
        elif not result.result_addrs:
            ctx[VALIDATE_STATUS] = ValidateStatus.NO_ONEMAP_MATCH
            return ctx

        # check membership of user input postal code against postal codes found with query
        search_with_street_postcodes = [addr.get(ONEMAP_POSTAL_CODE) for addr in result.result_addrs]
        if postcode not in search_with_street_postcodes:
            ctx[VALIDATE_STATUS] = ValidateStatus.ADDRESS_AND_POSTCODE_MISMATCH
            return ctx
        return ctx


onemap_validate_postal_with_street_step = OneMapValidatePostalWithStreetStep()
