"""
Validation step to check for a missing street name.

This step verifies that the parsed address includes a non-empty street name.
If the street name is missing or empty, it sets the context's `VALIDATE_STATUS`
to `STREET_NAME_MISSING`.
"""

from address_validator.constants import PARSED_ADDRESS, STREET_NAME, VALIDATE_STATUS
from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class MissingStreetCheckStep(ValidationStep):
    """
    Checks if the street name is missing in the parsed address.

    This step should be run after address parsing, and is used to catch
    incomplete or poorly formatted addresses early in the validation pipeline.
    """

    def __call__(self, ctx: dict) -> dict:
        """
        Check if the parsed street name is missing or empty.

        If missing, sets the `VALIDATE_STATUS` to `STREET_NAME_MISSING`.

        Args:
            ctx (dict): Address validation context.

        Returns:
            dict: Updated context with possible validation status change.
        """
        street = ctx.get(PARSED_ADDRESS, {}).get(STREET_NAME)
        if not street:
            ctx[VALIDATE_STATUS] = ValidateStatus.STREET_NAME_MISSING
        return ctx


missing_street_check_step = MissingStreetCheckStep()
