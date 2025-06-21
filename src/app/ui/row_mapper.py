"""
Utility module for formatting validation context into row dictionaries.

This is used by the NiceGUI table display. Given a context dictionary returned by
`AddressValidationFlow.validate()`, this module maps the relevant fields into a
flattened row dictionary with fixed keys matching the table's `field` definitions.
"""

from address_validator.constants import (
    BLOCK_NUMBER,
    PARSED_ADDRESS,
    POSTAL_CODE,
    PROPERTY_TYPE,
    RAW_ADDRESS,
    STREET_NAME,
    UNIT_NUMBER,
    VALIDATE_STATUS,
)
from address_validator.search import SearchResponseStatus
from address_validator.utils.common import extract_property_types
from address_validator.validation import ValidateStatus


def html_status_badge(status) -> str:
    """
    Return a coloured HTML badge for a validation status.
    Accepts either a ValidateStatus enum or a plain string.
    """
    if isinstance(status, ValidateStatus):
        status_str = status.value  # e.g. "Valid"
        is_good = status is ValidateStatus.VALID
    else:
        status_str = str(status)
        is_good = status_str.lower() == "valid"

    colour = "positive" if is_good else "negative"  # Quasar palette names
    return f'<span class="text-{colour} text-bold">{status_str}</span>'


def map_ctx_to_row(ctx: dict, raw_address: str) -> dict:
    """
    Convert a validation context into a NiceGUI-compatible row dictionary.

    Args:
        ctx (dict): The validation context returned by `AddressValidationFlow.validate()`.
        raw_address (str): The original address string submitted for validation.

    Returns:
        dict: A dictionary with fixed keys matching the `ui.table()` fields, containing
              extracted address components, validation status, and inferred property type.
    """
    # Always put the original raw address in the row
    row = {RAW_ADDRESS: raw_address}

    # Extract the validation status (either a ValidateStatus or a custom error string)
    status = ctx.get(VALIDATE_STATUS, "")
    row[VALIDATE_STATUS] = status

    parsed_addr = ctx.get(PARSED_ADDRESS, {})

    if status in [SearchResponseStatus.ERROR, SearchResponseStatus.TIMEOUT]:
        row[BLOCK_NUMBER] = ""
        row[STREET_NAME] = ""
        row[UNIT_NUMBER] = ""
        row[POSTAL_CODE] = ""
        row[PROPERTY_TYPE] = ""
    else:
        property_types = extract_property_types(ctx)
        property_type = property_types[0] if property_types else ""

        # Now pull out the parsed fields
        row[BLOCK_NUMBER] = parsed_addr.get(BLOCK_NUMBER, "")
        row[STREET_NAME] = parsed_addr.get(STREET_NAME, "")
        row[UNIT_NUMBER] = parsed_addr.get(UNIT_NUMBER, "")
        row[POSTAL_CODE] = parsed_addr.get(POSTAL_CODE, "")

        if status in [ValidateStatus.ADDRESS_AND_POSTCODE_MISMATCH, ValidateStatus.INVALID_POSTAL_CODE]:
            row[PROPERTY_TYPE] = "-"
        else:
            row[PROPERTY_TYPE] = property_type

    return row
