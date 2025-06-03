"""
Validation step to check if the postal code format is valid.

This step verifies that the postal code is a 6-digit numeric string.
If invalid or missing, it sets the validation status accordingly.
"""

from address_validator.constants import PARSED_ADDRESS, POSTAL_CODE, VALIDATE_STATUS
from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class SGCheckPostalFormatStep(ValidationStep):
    """
    Check whether the parsed postal code is in a valid Singapore format.

    Singapore postal codes must be exactly 6 digits and numeric.
    """

    def __call__(self, ctx: dict) -> dict:
        """
        Validate the format of the parsed postal code.

        Args:
            ctx (dict): Address validation context containing PARSED_ADDRESS.

        Returns:
            dict: Updated context, with VALIDATE_STATUS set if postal code is invalid.
        """
        parsed_addr = ctx.get(PARSED_ADDRESS, {})
        postal = parsed_addr.get(POSTAL_CODE)
        if not postal:
            ctx[VALIDATE_STATUS] = ValidateStatus.INVALID_POSTAL_CODE
            return ctx
        elif not postal.isdigit() or len(postal) != 6:
            ctx[VALIDATE_STATUS] = ValidateStatus.INVALID_POSTAL_CODE
            return ctx
        return ctx


check_postal_format_step = SGCheckPostalFormatStep()
