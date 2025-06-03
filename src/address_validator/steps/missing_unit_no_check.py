"""
Validation step to check for missing unit numbers.

This step uses property type information (from StreetDirectory) to determine
if a unit number is required. If the property type indicates that a unit number
is needed and none is found in the parsed address, the context's `VALIDATE_STATUS`
is set to `UNIT_NUMBER_MISSING`.
"""

from address_validator.constants import (
    PARSED_ADDRESS,
    PROPERTY_TYPES_NOT_REQUIRING_UNIT,
    PROPERTY_TYPES_REQUIRING_UNIT,
    UNIT_NUMBER,
    USE_UNIT_REQUIREMENT_WHITELIST,
    VALIDATE_STATUS,
)
from address_validator.steps.base import ValidationStep
from address_validator.utils.common import extract_property_types
from address_validator.validation import ValidateStatus


class MissingUnitNoCheck(ValidationStep):
    """
    Checks if a unit number is missing when the property type requires it.

    This step looks at property type(s) extracted from StreetDirectory results,
    and depending on the configuration, determines whether the absence of a unit
    number should be flagged as a validation issue.
    """

    def __call__(self, ctx: dict) -> dict:
        """
        Determine if a unit number is required but missing.

        Uses whitelist or blacklist mode to decide which property types require a unit.
        If missing and required, sets `VALIDATE_STATUS` to `UNIT_NUMBER_MISSING`.

        Args:
            ctx (dict): Address validation context with parsed address and property type.

        Returns:
            dict: Updated context, with validation status set if applicable.
        """
        property_types = extract_property_types(ctx)

        if not property_types:
            return ctx  # No valid SD property types

        if USE_UNIT_REQUIREMENT_WHITELIST:
            needs_unit = any(pt in PROPERTY_TYPES_REQUIRING_UNIT for pt in property_types)
        else:
            needs_unit = any(pt not in PROPERTY_TYPES_NOT_REQUIRING_UNIT for pt in property_types)

        parsed_unit = ctx.get(PARSED_ADDRESS, {}).get(UNIT_NUMBER)

        # todo: for data collection purpose, remove this
        if parsed_unit:
            ctx.setdefault("proptypes_with_unit_no", set()).add(property_types[0])

        if needs_unit and not parsed_unit:
            ctx[VALIDATE_STATUS] = ValidateStatus.UNIT_NUMBER_MISSING

        return ctx


missing_unit_no_check_step = MissingUnitNoCheck()
