from address_validator.onemap_client import ONEMAP_BLK_NO_KEY
from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class BlockNumberMatchStep(ValidationStep):
    """
    If BLOCK_NUMBER_STRIP_TRAILING_ALPHA is True, strip any trailing letter from both the parsed block number
    (e.g. “113A” → “113”) and each source block number before comparing. Otherwise, compare
    them exactly (case‐insensitive).
    """

    # ─── CONFIGURATION FLAG ─────────────────────────────────────────
    # When True: ignore any trailing letter on block numbers for both parsed and source.
    BLOCK_NUMBER_STRIP_TRAILING_ALPHA = True
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _strip_trailing_alpha(s: str) -> str:
        """If the string ends in a letter, drop that letter; otherwise return unchanged."""
        return s[:-1] if s and s[-1].isalpha() else s

    def __call__(self, ctx: dict) -> dict:
        parsed = ctx.get("parsed", {})
        onemap_data = ctx.get("onemap_data", [])
        blk_no = parsed.get("house_number")

        # Normalize and uppercase the parsed block
        blk_no = "" if blk_no is None else str(blk_no).strip().upper()

        # Build the set of source block numbers, possibly stripping trailing letters
        source_blk_nos = set()
        for addr in onemap_data:
            raw_source = addr.get(ONEMAP_BLK_NO_KEY, "").strip().upper()
            if self.BLOCK_NUMBER_STRIP_TRAILING_ALPHA:
                raw_source = self._strip_trailing_alpha(raw_source)
            source_blk_nos.add(raw_source)

        # If configured, also strip trailing alpha from the parsed block
        if self.BLOCK_NUMBER_STRIP_TRAILING_ALPHA:
            blk_no = self._strip_trailing_alpha(blk_no)

        # Finally, check membership
        if blk_no not in source_blk_nos:
            ctx["validate_status"] = ValidateStatus.BLOCK_NUMBER_MISMATCH

        return ctx


block_number_match_step = BlockNumberMatchStep()
