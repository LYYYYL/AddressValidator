"""
Validation step to verify postal code validity using OneMap.

This step queries OneMap with the parsed postal code. If the response indicates
an error or yields no results, the appropriate `VALIDATE_STATUS` is set in the context.
"""

from address_validator.constants import ONEMAP_RESULTS_BY_POSTCODE, PARSED_ADDRESS, POSTAL_CODE, VALIDATE_STATUS
from address_validator.onemap_client import OneMapClient
from address_validator.search import SearchResponseStatus
from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class OneMapValidatePostalStep(ValidationStep):
    """
    Uses OneMap to validate the parsed postal code.

    If the postal code is invalid, missing from OneMap results, or results in an error,
    this step will update the context with an appropriate `VALIDATE_STATUS`.
    """

    def __call__(self, ctx: dict) -> dict:
        """
        Perform postal code lookup using OneMap and validate the response.

        Args:
            ctx (dict): The address validation context containing a parsed postal code.

        Returns:
            dict: Updated context including OneMap results or validation status.
        """
        parsed_addr = ctx.get(PARSED_ADDRESS, {})
        postcode = parsed_addr.get(POSTAL_CODE)

        # query OneMap using postal code
        result = OneMapClient().search(postcode)
        ctx[ONEMAP_RESULTS_BY_POSTCODE] = result.result_addrs

        if result.status != result.status.OK:
            if result.status == SearchResponseStatus.NOT_FOUND:
                ctx[VALIDATE_STATUS] = ValidateStatus.INVALID_POSTAL_CODE
                return ctx
            else:
                ctx[VALIDATE_STATUS] = result.status
                return ctx
        elif not result.result_addrs:
            ctx[VALIDATE_STATUS] = ValidateStatus.NO_ONEMAP_MATCH
            return ctx
        return ctx


onemap_validate_postal_step = OneMapValidatePostalStep()
