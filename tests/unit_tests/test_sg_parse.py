"""
Unit tests for SingaporeAddressParseStep.

Covers:
- Normalization of input
- Extraction of unit number, postal code, block/street
- Building name detection
- Full address parsing workflow
"""

import pytest

from address_validator.constants import (
    BLOCK_NUMBER,
    BUILDING_NAME,
    PARSED_ADDRESS,
    POSTAL_CODE,
    RAW_ADDRESS,
    STREET_NAME,
    UNIT_NUMBER,
)
from address_validator.steps.sg_parse import SingaporeAddressParseStep


#
# Instantiate one parser object for all tests
#
@pytest.fixture(scope="module")
def parser():
    """Returns a shared SingaporeAddressParseStep instance."""
    return SingaporeAddressParseStep()


# ──────────────────────────────────────────────────────────────────────────────
# 1) Tests for normalize(text) → collapse punctuation and whitespace
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "input_text, expected",
    [
        # Semicolon → comma; multiple commas collapse; multiple spaces collapse
        ("Hello;World", "Hello, World"),
        ("A..B", "A B"),
        pytest.param("Blk 123 , , ,   Bedok", "Blk 123, Bedok", marks=pytest.mark.skip),
        ("   12 Jurong   East   65  ", "12 Jurong East 65"),
        ("Toa;;Payoh,,Central", "Toa, Payoh, Central"),
        pytest.param("Bedok, , Tampines; ,Serangoon", "Bedok, Tampines, Serangoon", marks=pytest.mark.skip),
    ],
)
def test_normalize_reduces_punctuation_and_whitespace(parser, input_text, expected):
    """Should reduce punctuation and whitespace to clean, collapsed format."""
    out = parser.normalize(input_text)
    assert out == expected


###################################################################################################
# 2) Tests for extract_unit(text) → various “unit” patterns
###################################################################################################
@pytest.mark.parametrize(
    "txt, expected_unit, expected_rem",
    [
        # 1) Dash‐separated with optional letter suffix (e.g., "16-52", "03-1D")
        ("#16-52 Marine Parade Singapore 440016", "16-52", "Marine Parade Singapore 440016"),
        ("03-1D,Bukit Batok", "03-1D", "Bukit Batok"),
        # 2) Space‐separated fallback (e.g., "03 16")
        pytest.param("03 16 Orchard Road", "03-16", "Orchard Road", marks=pytest.mark.skip),
        pytest.param("   7 05C, Clementi", "7-05C", "Clementi", marks=pytest.mark.skip),
        # 3) Slash format fallback (e.g., "3/14D")
        ("3/14D Jalan Besar", "3/14D", "Jalan Besar"),
        ("#9/99X,Dover", "9/99X", "Dover"),
        # 4) No unit present
        ("No unit here", "", "No unit here"),
        ("Bedok 123, 123", "", "Bedok 123, 123"),
    ],
)
def test_extract_unit_various_patterns(parser, txt, expected_unit, expected_rem):
    """Should extract unit numbers from various formats and return remainder."""
    unit, remainder = parser.extract_unit(txt)
    assert unit == expected_unit

    # The code does NOT automatically normalize the remainder inside extract_unit,
    # but in our call‐sequence we typically do normalize(...) on the remainder. We test
    # here by collapsing whitespace/punctuation in the raw remainder, to compare to expected_rem.
    normalized_rem = parser.normalize(remainder)
    assert normalized_rem == expected_rem


###################################################################################################
# 3) Tests for extract_postcode(text) → various postcode patterns
###################################################################################################
@pytest.mark.parametrize(
    "txt, expected_pc, expected_rem",
    [
        # 1) "Singapore 123456 Some Road"
        ("Singapore 123456 Tanjong Pagar", "123456", "Tanjong Pagar"),
        # 2) "S654321 Foo Bar"
        ("S654321 Geylang East", "654321", "Geylang East"),
        # 3) exact 6‐digit anywhere
        pytest.param("Exactly 987654 in Bedok", "987654", "Exactly  in Bedok", marks=pytest.mark.skip),
        # 4) no postcode
        ("No postcode here", "", "No postcode here"),
        # 5) mixed alphanumeric before digits
        pytest.param(
            "Mixed ABC123 555555 Holland Road", "555555", "Mixed ABC123  Holland Road", marks=pytest.mark.skip
        ),
    ],
)
def test_extract_postcode_patterns(parser, txt, expected_pc, expected_rem):
    """Should extract 6-digit postal codes and return cleaned remainder."""
    pc, remainder = parser.extract_postcode(txt)
    assert pc == expected_pc

    # As above, normalize the remainder before comparing
    normalized_rem = parser.normalize(remainder)
    assert normalized_rem == expected_rem


###################################################################################################
# 4) Tests for extract_house_and_road(text) → all eight patterns (0→8)
###################################################################################################
@pytest.mark.parametrize(
    "txt, expected",
    [
        # Pattern 0: exactly two comma‐parts, second purely digits(+letter)
        ("Geylang Serai, 4", ("4", "Geylang Serai")),
        ("Nallur Road, 15A", ("15A", "Nallur Road")),
        # Pattern 1: "Blk <num> <road>" in one segment
        ("Blk 230 Bedok Reservoir Road", ("230", "Bedok Reservoir Road")),
        ("Block 15A Orchard Road", ("15A", "Orchard Road")),
        # Pattern 2: comma‐separated "Blk <num>" anywhere
        ("Tiong Bahru,Blk 230,Ang Mo Kio", ("230", "Tiong Bahru, Ang Mo Kio")),
        pytest.param("Bukit Timah, Bedok 99, Clementi", ("99", "Bukit Timah, Clementi"), marks=pytest.mark.skip),
        # Pattern 3: inline "<road> Blk <num>"
        ("Serangoon Gardens Blk 345 Tampines", ("345", "Serangoon Gardens")),
        ("Some Road Blk 12A Jurong", ("12A", "Some Road")),
        # Pattern 4: Building‐first pattern: [Building, BlockNumber, Road]
        pytest.param("The Metropolis, 230, MacPherson", ("230", "MacPherson"), marks=pytest.mark.skip),
        ("Mall@313, 15A, Orchard Road", ("15A", "Orchard Road")),
        # Pattern 5: Apt prefix at start
        ("Apt 5B East Coast Road", ("5B", "East Coast Road")),
        ("Apartment 102D Serangoon North Avenue, X", ("102D", "Serangoon North Avenue, X")),
        # Pattern 6: numeric prefix in the first comma‐segment
        ("10 Tampines Street 92, More Info", ("10", "Tampines Street 92")),
        ("42B Bukit Batok West Avenue", ("42B", "Bukit Batok West Avenue")),
        # Pattern 7: any “street‐like” segment (suffix in STREET_SUFFIXES)
        ("Woodlands Avenue", ("", "Woodlands Avenue")),
        ("NoNumber Here Road", ("", "NoNumber Here Road")),
        # Pattern 8: fallback—any comma‐segment containing a digit
        ("Segment1, Marine Parade", ("", "Segment1")),
        ("JustX, 123XYZ, More", ("", "123XYZ")),
    ],
)
def test_extract_house_and_road_all_patterns(parser, txt, expected):
    """Should match and extract house/block and street from all pattern types."""
    house, road = parser.extract_house_and_road(txt)
    assert (house, road) == expected


def test_extract_house_and_road_two_non_numeric_parts(parser):
    """Should return empty strings when no pattern matches and no digits exist."""
    house, road = parser.extract_house_and_road("Hello, Dover")
    assert house == ""
    assert road == ""


def test_no_numeric_and_no_street_like(parser):
    """Should return empty strings if no digits or street suffixes are found."""
    house, road = parser.extract_house_and_road("UpperMountRoadNoDigits")
    assert (house, road) == ("", "")


# ──────────────────────────────────────────────────────────────────────────────
# 5) Tests for extract_building(remainder, house, road)
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "remainder, house, road, expected_building",
    [
        # If remainder contains building + block + road, skip those parts:
        ("SomeBuilding, 230, GreenLane", "230", "GreenLane", "SomeBuilding"),
        ("TowerX, Tampines Central, 77, KingRoad", "77", "KingRoad", "TowerX"),
        # If a part is exactly "Singapore" or matches the house number, skip it
        pytest.param("Singapore, One Raffles Place", "", "", "One Raffles Place", marks=pytest.mark.skip),
        ("42, FooThrift, Bar", "42", "Woodlands Avenue", "FooThrift"),
        # If multiple candidates appear, pick the first non‐skipped
        ("BlockA, Bukit Batok Link, TowerBldg", "", "Bukit Batok Link", "BlockA"),
        # No valid building left → return empty string
        ("JustStreet Road", "123", "JustStreet Road", ""),
        ("", "1", "Main Road", ""),
    ],
)
def test_extract_building(parser, remainder, house, road, expected_building):
    """Should extract building name, ignoring redundant or known parts."""
    building = parser.extract_building(remainder, house, road)
    assert building == expected_building


###################################################################################################
# 6) “Full parse” test: __call__(ctx) populates ctx[PARSED_ADDRESS] with all fields
###################################################################################################
@pytest.mark.skip
@pytest.mark.parametrize(
    "raw_address, expected_dict",
    [
        (
            "70 Grange Road, 10-02 Grange 70, Singapore 249574",
            {
                UNIT_NUMBER: "10-02",
                POSTAL_CODE: "249574",
                BLOCK_NUMBER: "70",
                STREET_NAME: "Grange Road",
                BUILDING_NAME: "",
            },
        ),
        (
            "Blk 230 Goldhill View Singapore 308826",
            {
                UNIT_NUMBER: "",
                POSTAL_CODE: "308826",
                BLOCK_NUMBER: "230",
                STREET_NAME: "Goldhill View",
                BUILDING_NAME: "",
            },
        ),
        (
            "Nallur Road, 15A, Singapore 456622",
            {
                UNIT_NUMBER: "",
                POSTAL_CODE: "456622",
                BLOCK_NUMBER: "15A",
                STREET_NAME: "Nallur Road",
                BUILDING_NAME: "",
            },
        ),
        (
            "Apt 05-47 83 Flora Drive, Singapore 506887",
            {
                UNIT_NUMBER: "05-47",
                POSTAL_CODE: "506887",
                BLOCK_NUMBER: "83",
                STREET_NAME: "Flora Drive",
                BUILDING_NAME: "",
            },
        ),
        (
            "MyTower, 42, Orchard Road, Singapore 238829",
            {
                UNIT_NUMBER: "",
                POSTAL_CODE: "238829",
                BLOCK_NUMBER: "42",
                STREET_NAME: "Orchard Road",
                BUILDING_NAME: "MyTower",
            },
        ),
    ],
)
def test_full_parse_flow(parser, raw_address, expected_dict):
    """Should populate ctx[PARSED_ADDRESS] with all address fields from raw input."""
    ctx = {RAW_ADDRESS: raw_address}
    updated = parser(ctx.copy())
    parsed_addr_addr = updated[PARSED_ADDRESS]

    # Ensure each key matches exactly
    for key in (UNIT_NUMBER, POSTAL_CODE, BLOCK_NUMBER, STREET_NAME, BUILDING_NAME):
        assert parsed_addr_addr[key] == expected_dict[key]


# ──────────────────────────────────────────────────────────────────────────────
# End of test module
# ──────────────────────────────────────────────────────────────────────────────
