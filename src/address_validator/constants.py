# Toggle this flag to turn detailed debug prints on or off
DEBUG_PRINT = True


# ─── General configuration flags/numbers ────────────────────────────
BLOCK_NUMBER_STRIP_TRAILING_ALPHA = True

# ─── Property types that do NOT require a unit (blacklist style) ──────────────────
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
    "Commercial Building",
    "Dormitory",
    "Shop Houses",
    "Bank Branches",
    "Supermarket",
    "Public Building",
}

# ─── Property types that DO require a unit (whitelist style) ─────────────────────
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

# ─── Toggle: if True, use the whitelist above; if False, use the blacklist above. ─
USE_UNIT_REQUIREMENT_WHITELIST = True


# ─── StreetDirectory: exact category names to exclude ────────────────────
STREETDIR_EXACT_CATEGORY_EXCLUSIONS = {"SCDF Bomb Shelter", "Multi Storey Car Park (MSCP)", "Car Park", "Fire Post"}

# ─── StreetDirectory: substrings in a category to exclude ─────────────────
STREETDIR_CATEGORY_SUBSTRING_EXCLUSIONS = {
    "Business dealing with",
}
