from address_validator.steps.base import ValidationStep
from address_validator.utils.libpostal import CommonAddressUtils


class LibPostalParseStep(ValidationStep):
    def __call__(self, ctx: dict) -> dict:
        raw = ctx.get("preprocessed_address") or ctx.get("raw_address", "")
        ctx["parsed"] = CommonAddressUtils.parse_address(raw)
        return ctx


libpostal_parse_step = LibPostalParseStep()
