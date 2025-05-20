from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class SGCheckPostalFormatStep(ValidationStep):
    def __call__(self, ctx: dict) -> dict:
        parsed = ctx.get("parsed", {})
        postal = parsed.get("postcode")
        if not postal:
            ctx["validate_status"] = ValidateStatus.POSTAL_CODE_MISSING
            return ctx
        elif not postal.isdigit() or len(postal) != 6:
            ctx["validate_status"] = ValidateStatus.INVALID_POSTAL_CODE
            return ctx
        return ctx


check_postal_format_step = SGCheckPostalFormatStep()
