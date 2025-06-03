"""
Singapore-specific address validation step registration.

This module defines the validation steps used specifically for addresses
in Singapore. It registers a sequence of functions implementing checks such as:
- postal code format validation
- OneMap and StreetDirectory lookups
- detection of missing street names or unit numbers
- block number matching

Steps are registered under the `COUNTRY_CODE_SINGAPORE` using the
`@register_steps_for_country` decorator, allowing the validation engine
to dynamically retrieve the correct processing pipeline based on country.
"""

from address_validator.constants import COUNTRY_CODE_SINGAPORE
from address_validator.registry.loader import register_steps_for_country
from address_validator.steps.block_number_match import block_number_match_step
from address_validator.steps.missing_street_check import missing_street_check_step
from address_validator.steps.missing_unit_no_check import missing_unit_no_check_step
from address_validator.steps.onemap_validate_postal import onemap_validate_postal_step
from address_validator.steps.onemap_validate_postal_with_street import onemap_validate_postal_with_street_step
from address_validator.steps.search_streetdirectory import search_streetdirectory_step
from address_validator.steps.sg_parse import sg_parse_step
from address_validator.steps.sg_postcode_check import check_postal_format_step


@register_steps_for_country(COUNTRY_CODE_SINGAPORE)
def get_sg_steps() -> list:
    """
    Return the ordered list of address validation steps for Singapore.

    These steps define the Singapore-specific validation logic used in the
    address validation pipeline. The steps include parsing, postal code checks,
    external API lookups (OneMap, StreetDirectory), and various heuristic checks.

    Returns:
        list: A list of callable validation steps to apply in order.
    """
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
