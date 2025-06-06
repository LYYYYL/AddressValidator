"""
Validation step to check if the parsed block number matches any of the block numbers
returned from OneMap's search-by-postal-code results.

This step optionally strips trailing alphabetic characters from both the parsed
block number and the OneMap result before comparison, depending on the global
configuration flag `BLOCK_NUMBER_STRIP_TRAILING_ALPHA`.

If the parsed block number does not match any from OneMap, it sets
`VALIDATE_STATUS` to `BLOCK_NUMBER_MISMATCH`.
"""

from address_validator import constants
from address_validator.constants import (
    BLOCK_NUMBER,
    ONEMAP_BLOCK_NUMBER,
    ONEMAP_RESULTS_BY_POSTCODE,
    PARSED_ADDRESS,
    VALIDATE_STATUS,
)
from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class BlockNumberMatchStep(ValidationStep):
    """
    Validation step to compare the parsed block number against OneMap search results.

    This step fetches the block number from the parsed address and compares it with
    those found in the OneMap search results (based on postal code). It supports
    normalization such as stripping trailing letters for better tolerance to formatting
    differences (e.g., "113A" vs "113").

    If no match is found, the context's `VALIDATE_STATUS` is set to `BLOCK_NUMBER_MISMATCH`.
    """

    @staticmethod
    def _strip_trailing_alpha(s: str) -> str:
        """
        Strip trailing letter from a block number string, if present.

        Args:
            s (str): Block number string to normalize.

        Returns:
            str: The block number without any trailing alphabetic character.
        """
        return s[:-1] if s and s[-1].isalpha() else s

    def __call__(self, ctx: dict) -> dict:
        """
        Perform block number match validation using OneMap results.

        Args:
            ctx (dict): Address validation context containing parsed address and OneMap results.

        Returns:
            dict: Updated context. If a mismatch is detected, sets `VALIDATE_STATUS`.
        """
        parsed_addr = ctx.get(PARSED_ADDRESS, {})
        onemap_search_with_postcode = ctx.get(ONEMAP_RESULTS_BY_POSTCODE, [])

        blk_no = parsed_addr.get(BLOCK_NUMBER)
        # Normalize and uppercase the parsed_addr block
        blk_no = "" if blk_no is None else str(blk_no).strip().upper()
        # If configured, also strip trailing alpha from the parsed_addr block
        if constants.BLOCK_NUMBER_STRIP_TRAILING_ALPHA:
            blk_no = self._strip_trailing_alpha(blk_no)

        # Build the set of source block numbers from OneMap results, possibly stripping trailing letters
        source_blk_nos = set()
        for addr in onemap_search_with_postcode:
            raw_source = addr.get(ONEMAP_BLOCK_NUMBER, "").strip().upper()
            if constants.BLOCK_NUMBER_STRIP_TRAILING_ALPHA:
                raw_source = self._strip_trailing_alpha(raw_source)
            source_blk_nos.add(raw_source)

        # Finally, check membership
        if blk_no not in source_blk_nos:
            ctx[VALIDATE_STATUS] = ValidateStatus.BLOCK_NUMBER_MISMATCH

        return ctx


block_number_match_step = BlockNumberMatchStep()
