from address_validator.onemap_client import OneMapClient
from address_validator.search import SearchResponseStatus
from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class OneMapValidatePostalStep(ValidationStep):
    def __call__(self, ctx: dict) -> dict:
        parsed = ctx.get("parsed")
        postcode = parsed.get("postcode")
        result = OneMapClient().search(postcode)
        ctx["onemap_data"] = result.result_addrs
        if result.status != result.status.OK:
            if result.status == SearchResponseStatus.NOT_FOUND:
                ctx["validate_status"] = ValidateStatus.INVALID_POSTAL_CODE
                return ctx
            else:
                ctx["validate_status"] = result.status
                return ctx
        elif not result.result_addrs:
            ctx["validate_status"] = ValidateStatus.NO_ONEMAP_MATCH
            return ctx
        return ctx


onemap_validate_postal_step = OneMapValidatePostalStep()
