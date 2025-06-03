"""
Common utilities used across the address validation pipeline.

Includes helpers for extracting property types, building address query parts,
and generating timestamp strings.
"""

from datetime import datetime, timezone

from address_validator.constants import (
    BLOCK_NUMBER,
    ONEMAP_BLOCK_NUMBER,
    ONEMAP_POSTAL_CODE,
    ONEMAP_RESULTS_BY_POSTCODE,
    ONEMAP_STREET_NAME,
    PARSED_ADDRESS,
    POSTAL_CODE,
    STREET_NAME,
    STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS,
)


def extract_property_types(ctx: dict) -> list[str]:
    """
    Extract property type(s) from streetdirectory_results in the context.

    Args:
        ctx (dict): Context dict from the validator pipeline.
        first_only (bool): If True, return the first property type (or None).
                           If False, return a list of unique types (or [None]).

    Returns:
        str | None | list[str | None]
    """
    results = ctx.get(STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS, [])
    if not results:
        return []

    types = [category for _, category in results if category]
    return list(dict.fromkeys(types))  # remove duplicates


def extract_address_query_parts(
    ctx: dict,
    prefer_onemap: bool = True,
    onemap_key: str = ONEMAP_RESULTS_BY_POSTCODE,
    fallback_to_parsed: bool = True,
) -> tuple[str, str, str]:
    """
    Extract (block number, street name, postal code) from context.

    Prefers OneMap results if available, and optionally falls back to the
    parsed address if allowed.

    Args:
        ctx (dict): Context dictionary containing OneMap and/or parsed address.
        prefer_onemap (bool): Whether to prioritize OneMap result first.
        onemap_key (str): Key in the context where OneMap results are stored.
        fallback_to_parsed (bool): Whether to use parsed address as a fallback.

    Returns:
        tuple[str, str, str]: A tuple of (block, street, postal code).
    """
    source = None
    from_onemap = False

    if prefer_onemap and ctx.get(onemap_key):
        onemap_results = ctx[onemap_key]
        if isinstance(onemap_results, list) and onemap_results:
            source = onemap_results[0]
            from_onemap = True

    if not source and fallback_to_parsed and ctx.get(PARSED_ADDRESS):
        source = ctx[PARSED_ADDRESS]

    if not source:
        return "", "", ""

    if from_onemap:
        blk = source.get(ONEMAP_BLOCK_NUMBER, "")
        if blk == "NIL":
            blk = ""
        street = source.get(ONEMAP_STREET_NAME, "")
        postcode = source.get(ONEMAP_POSTAL_CODE, "")
    else:
        blk = source.get(BLOCK_NUMBER, "")
        street = source.get(STREET_NAME, "")
        postcode = source.get(POSTAL_CODE, "")

    return blk.strip(), street.strip(), postcode.strip()


def current_utc_isoformat() -> str:
    """
    Return the current UTC time as an ISO 8601 string.

    Includes timezone info (e.g., `Z` or `+00:00`) to ensure full datetime accuracy.

    Returns:
        str: The current UTC datetime in ISO format.
    """
    return datetime.now(timezone.utc).isoformat()
