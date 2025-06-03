"""
Global constants and configuration flags for address validation.

Includes toggles for debug output, unit validation logic, category filters for
StreetDirectory, and key names used throughout the validation pipeline.
"""

###################################################################################################
# Toggle this flag to turn detailed debug prints on or off. Todo: Replace with Loguru
###################################################################################################
DEBUG_PRINT = False


###################################################################################################
# block_number_match.py
# #################################################################################################
BLOCK_NUMBER_STRIP_TRAILING_ALPHA = False

###################################################################################################
# Property types that do NOT require a unit (blacklist style)
###################################################################################################
PROPERTY_TYPES_NOT_REQUIRING_UNIT = {
    "Bungalow",
    "Semi Detached House",
    "International School",
    "Terrace House",
    "Hospital",
    "Primary School",
    "Methodist Church",
    "Church",
    "Kindergarten",
    "Preschool",
    "Shop Houses",
    "Bank Branches",
    "Supermarket",
    "Public Building",
}

###################################################################################################
# Property types that DO require a unit (whitelist style)
###################################################################################################
PROPERTY_TYPES_REQUIRING_UNIT = {
    "Apartments",
    "Commercial Building",
    "Condominium",
    "DBSS Blocks",
    "Dormitory",
    "HDB Blocks",
    "Industrial Building",
    "Industrial Estate",
    "Shopping Malls",
}

###################################################################################################
# Toggle: if True, use the whitelist above; if False, use the blacklist above
###################################################################################################
USE_UNIT_REQUIREMENT_WHITELIST = True


###################################################################################################
# StreetDirectory: exact category names to exclude
###################################################################################################
STREETDIR_EXACT_CATEGORY_EXCLUSIONS = {"SCDF Bomb Shelter", "Multi Storey Car Park (MSCP)", "Car Park", "Fire Post"}

###################################################################################################
# StreetDirectory: substrings in a category to exclude
###################################################################################################
STREETDIR_CATEGORY_SUBSTRING_EXCLUSIONS = {
    "Business dealing with",
}


###################################################################################################
# Dictionary keys used by libpostal that are adopted in this project
###################################################################################################

BLOCK_NUMBER = "house_number"
UNIT_NUMBER = "unit"
STREET_NAME = "road"
POSTAL_CODE = "postcode"
BUILDING_NAME = "building"

###################################################################################################
# Other context keys for the ValidationFlowBuilder pipeline
###########################additionalProp1#########################################################
PARSED_ADDRESS = "parsed_address"
RAW_ADDRESS = "raw_address"
VALIDATE_STATUS = "validate_status"
VALIDATED_AT = "validated_at"
PROPERTY_TYPE = "property_type"
ONEMAP_RESULTS_BY_POSTCODE = "onemap_results_by_postcode"
ONEMAP_RESULTS_BY_ADDRESS = "onemap_results_by_address"
STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS = "streetdirectory_results_by_full_address"

###################################################################################################
# Dictionary keys used by Onemap
###################################################################################################

ONEMAP_STREET_NAME = "ROAD_NAME"
ONEMAP_BLOCK_NUMBER = "BLK_NO"
ONEMAP_POSTAL_CODE = "POSTAL"

###################################################################################################
# COUNTRY CODES
###################################################################################################

COUNTRY_CODE_SINGAPORE = "SG"
