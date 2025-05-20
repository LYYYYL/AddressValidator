from address_validator.registry.loader import register_steps_for_country
from address_validator.steps.block_number_match import block_number_match_step
from address_validator.steps.missing_street_check import missing_street_check_step
from address_validator.steps.missing_unit_no_check import missing_unit_no_check_step
from address_validator.steps.onemap_validate_postal import onemap_validate_postal_step
from address_validator.steps.onemap_validate_postal_with_street import onemap_validate_postal_with_street_step
from address_validator.steps.search_streetdirectory import search_streetdirectory_step
from address_validator.steps.sg_parse import sg_parse_step
from address_validator.steps.sg_postcode_check import check_postal_format_step


@register_steps_for_country("SG")
def get_sg_steps() -> list:
    return [
        sg_parse_step,
        check_postal_format_step,
        onemap_validate_postal_step,
        search_streetdirectory_step,
        missing_street_check_step,
        block_number_match_step,
        onemap_validate_postal_with_street_step,
        missing_unit_no_check_step,
    ]
