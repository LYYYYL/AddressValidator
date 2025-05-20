from address_validator.onemap_client import ONEMAP_POSTCODE_KEY, OneMapClient
from address_validator.steps.base import ValidationStep
from address_validator.validation import ValidateStatus


class OneMapValidatePostalWithStreetStep(ValidationStep):
    def __call__(self, ctx: dict) -> dict:
        parsed = ctx.get("parsed")
        blk = parsed.get("house_number")
        street = parsed.get("road")
        building = parsed.get("building")
        postcode = parsed.get("postcode")
        if building is None:
            building = ""
        search_field = f"{blk} {street} {building}"

        result = OneMapClient().search(search_field)
        ctx["onemap_search_with_street"] = result.result_addrs
        if result.status != result.status.OK:
            ctx["validate_status"] = result.status
            return ctx
        elif not result.result_addrs:
            ctx["validate_status"] = ValidateStatus.NO_ONEMAP_MATCH
            return ctx

        search_with_street_postcodes = [addr.get(ONEMAP_POSTCODE_KEY) for addr in result.result_addrs]
        if postcode not in search_with_street_postcodes:
            ctx["validate_status"] = ValidateStatus.BLK_STREET_AND_POSTCODE_MISMATCH
            return ctx
        return ctx


onemap_validate_postal_with_street_step = OneMapValidatePostalWithStreetStep()
