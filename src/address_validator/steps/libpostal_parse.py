"""
Validation step to parse raw addresses using libpostal.

This step uses libpostal to convert a raw address string into a structured
dictionary of components (e.g., house number, road, postcode). The parsed
result is stored in the context under the `PARSED_ADDRESS` key.
"""

from address_validator.constants import PARSED_ADDRESS, RAW_ADDRESS
from address_validator.steps.base import ValidationStep
from address_validator.utils.libpostal import CommonAddressUtils


class LibPostalParseStep(ValidationStep):
    """
    Parses raw address strings using libpostal.

    This step is intended to be used at the beginning of the pipeline to
    convert freeform address strings into structured data suitable for
    downstream validation steps.
    """

    def __call__(self, ctx: dict) -> dict:
        """
        Parse the raw address string using libpostal.

        The result is stored under the `PARSED_ADDRESS` key in the context.

        Args:
            ctx (dict): Address validation context containing the raw address.

        Returns:
            dict: Updated context with `PARSED_ADDRESS` added.
        """
        raw = ctx.get(RAW_ADDRESS, "")
        ctx[PARSED_ADDRESS] = CommonAddressUtils.parse_address(raw)
        return ctx


libpostal_parse_step = LibPostalParseStep()
