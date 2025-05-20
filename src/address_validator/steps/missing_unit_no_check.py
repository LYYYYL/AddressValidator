# src/address_validator/steps/missing_unit_no_check_step.py

from address_validator.constants import (
    PROPERTY_TYPES_NOT_REQUIRING_UNIT,
    PROPERTY_TYPES_REQUIRING_UNIT,
    USE_UNIT_REQUIREMENT_WHITELIST,
)
from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class MissingUnitNoCheck(ValidationStep):
    """
    Verify that if property types from streetdirectory_results require a unit number,
    that the parsed unit exists.

    - If USE_UNIT_REQUIREMENT_WHITELIST is True:
        Only types in PROPERTY_TYPES_REQUIRING_UNIT will require a unit.
    - If False:
        Any type NOT in PROPERTY_TYPES_NOT_REQUIRING_UNIT will require a unit.

    (We assume any “Business dealing with …” substrings were already removed upstream.)
    """

    def __call__(self, ctx: dict) -> dict:
        sd_results = ctx.get("streetdirectory_results") or []
        if not sd_results:
            return ctx  # No StreetDirectory data; nothing to check

        # Extract raw property types (already filtered)
        property_types_raw = [ptype for _, ptype in sd_results]

        # Remove duplicates while preserving insertion order
        property_types = list(dict.fromkeys(property_types_raw))

        # Decide if a unit is needed
        if USE_UNIT_REQUIREMENT_WHITELIST:
            # Only those in the whitelist require a unit
            needs_unit = any(pt in PROPERTY_TYPES_REQUIRING_UNIT for pt in property_types)
        else:
            # Any type not in the blacklist requires a unit
            needs_unit = any(pt not in PROPERTY_TYPES_NOT_REQUIRING_UNIT for pt in property_types)

        parsed_unit = ctx.get("parsed", {}).get("unit")

        # If a unit was provided, record the property type that needed it
        if parsed_unit and property_types:
            if "proptypes_with_unit_no" not in ctx:
                ctx["proptypes_with_unit_no"] = set()
            ctx["proptypes_with_unit_no"].add(property_types[0])

        # If a unit is required but missing, set failure
        if needs_unit and not parsed_unit:
            ctx["validate_status"] = ValidateStatus.UNIT_NUMBER_MISSING

        return ctx


missing_unit_no_check_step = MissingUnitNoCheck()
