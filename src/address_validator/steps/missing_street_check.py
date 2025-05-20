from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class MissingStreetCheckStep(ValidationStep):
    def __call__(self, ctx: dict) -> dict:
        street = ctx.get("parsed", {}).get("road")
        if not street:  # covers None or empty string
            ctx["validate_status"] = ValidateStatus.STREET_NAME_MISSING
        return ctx


missing_street_check_step = MissingStreetCheckStep()
