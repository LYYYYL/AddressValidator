"""
Command-line tool to validate addresses from a CSV file.

Reads shipping addresses from a CSV, applies country-specific validation logic,
and outputs results including parsed fields, validation status, and inferred property type.
"""

import sys
from pathlib import Path

import pandas as pd

from address_validator.constants import (
    BLOCK_NUMBER,
    BUILDING_NAME,
    COUNTRY_CODE_SINGAPORE,
    PARSED_ADDRESS,
    POSTAL_CODE,
    STREET_NAME,
    STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS,
    UNIT_NUMBER,
    VALIDATE_STATUS,
)
from address_validator.validation import AddressValidationFlow, ValidateStatus

# Configuration flags
PRINT_ALL = False  # Set True to output all rows
SHOW_NO_ROAD = False  # Set True to output only rows missing a road
SKIP_EMPTY = True  # Set True to skip rows with neither Shipping Street nor Shipping Zip


class AddressCSVTester:
    """
    A utility class to validate addresses from a CSV file.

    It reads address rows, processes each through the validation pipeline,
    collects results, and writes the annotated output to a new CSV file.
    """

    def __init__(self, input_csv: Path, country: str = COUNTRY_CODE_SINGAPORE):
        """
        Initialize the tester with input CSV path and country.

        Args:
            input_csv (Path): Path to the input CSV file.
            country (str): Country code to determine validation rules.
        """
        self.input_csv = input_csv
        self.output_csv = input_csv.with_stem(input_csv.stem + "_validated")
        self.country = country
        self.df = None

    def load_addresses(self):
        """
        Load and clean shipping addresses from the input CSV file.

        Sets `self.df` with parsed DataFrame and ensures ZIPs are string-typed.
        """
        self.df = pd.read_csv(self.input_csv, dtype={"Shipping Zip": str})
        self.df["Shipping Zip"] = self.df["Shipping Zip"].str.lstrip("'")

    def validate_addresses(self):
        """
        Run address validation logic on each row in the CSV.

        Updates the DataFrame with parsed address parts, validation statuses,
        and inferred property types. Also prints up to five examples per property type
        where a unit number was provided.
        """
        statuses = []
        prop_types = []
        house_nums = []
        roads = []
        units = []
        postcodes = []
        buildings = []
        multiple_match_addrs = []  # UNUSED but left for structure

        # ───────────────────────────────────────────────────────────────────────
        # MASTER‐EXAMPLES: map property type → up to five example addresses
        master_examples = {}  # type: dict[str, list[str]]
        # ───────────────────────────────────────────────────────────────────────

        for _, row in self.df.iterrows():
            street = str(row["Shipping Street"]).strip()
            city = str(row["Shipping City"]).strip()
            shipping_zip = str(row["Shipping Zip"]).strip()

            # Skip blank rows entirely
            if street == "nan" and shipping_zip == "nan":
                statuses.append(None)
                prop_types.append(None)
                house_nums.append(None)
                roads.append(None)
                units.append(None)
                postcodes.append(None)
                buildings.append(None)
                multiple_match_addrs.append(None)
                continue

            # Build the “raw address” string used for both validation and example
            raw_address = f"{street}, {city} {shipping_zip}"

            ctx = {"street": street, "city": city, "postal": shipping_zip}
            result = AddressValidationFlow.validate(raw_address, country=self.country, ctx=ctx)

            parsed_addr = result.get(PARSED_ADDRESS, {})
            house_nums.append(parsed_addr.get(BLOCK_NUMBER))
            roads.append(parsed_addr.get(STREET_NAME))
            units.append(parsed_addr.get(UNIT_NUMBER))
            postcodes.append(parsed_addr.get(POSTAL_CODE))
            buildings.append(parsed_addr.get(BUILDING_NAME))

            status = result.get(VALIDATE_STATUS)
            statuses.append(status)
            streetdirectory_result = result.get(STREETDIRECTORY_RESULTS_BY_FULL_ADDRESS)
            this_prop = "UNKNOWN" if streetdirectory_result is None else streetdirectory_result[0][1]
            prop_types.append(this_prop)

            # ─────────────────────────────────────────────────────────────────────
            # If a unit was provided, store up to 5 examples for this_prop
            if parsed_addr.get(UNIT_NUMBER):
                if this_prop not in master_examples:
                    master_examples[this_prop] = []
                if len(master_examples[this_prop]) < 5:
                    master_examples[this_prop].append(raw_address)
            # ─────────────────────────────────────────────────────────────────────

        # Append new columns (unchanged)
        self.df["House Number"] = house_nums
        self.df["Road"] = roads
        self.df["Unit"] = units
        self.df["Postcode"] = postcodes
        self.df["Building"] = buildings
        self.df["Validation"] = statuses
        self.df["Property Type"] = prop_types

        # ─────────────────────────────────────────────────────────────────────
        # PRINT each property type along with up to five example addresses:
        print("\n" + "=" * 60)
        print("=== ALL PROPERTY TYPES WHERE USER SUPPLIED A UNIT ===")
        if master_examples:
            for prop_type in sorted(master_examples):
                print(f"\n  • {prop_type}")
                for addr in master_examples[prop_type]:
                    print(f"      – {addr}")
        else:
            print("  (none)")
        print("=" * 60 + "\n")
        # ─────────────────────────────────────────────────────────────────────

    def save_output(self):
        """
        Save the annotated DataFrame to a new CSV file.

        Respects filtering flags to exclude blank rows or only include invalid ones.
        """
        # Skip rows where both Shipping Street and Shipping Zip are empty
        if SKIP_EMPTY:
            self.df = self.df[
                ~(
                    (self.df["Shipping Street"].isna() | (self.df["Shipping Street"] == ""))
                    & (self.df["Shipping Zip"].isna() | (self.df["Shipping Zip"] == ""))
                )
            ]

        cols = [
            "Shipping Street",
            "Shipping City",
            "Shipping Zip",
            "House Number",
            "Road",
            "Unit",
            "Postcode",
            "Building",
            "Validation",
            "Property Type",
            # "Multiple Matches",  # include the new column here if needed
        ]
        output = self.df[cols]

        # Determine rows to save based on flags
        if SHOW_NO_ROAD:
            to_save = output[output["Road"].isna() | (output["Road"] == "")]
        elif PRINT_ALL:
            to_save = output
        else:
            to_save = output[output["Validation"] != ValidateStatus.VALID]

        to_save.to_csv(self.output_csv, index=False)
        print(f"\n✅ Output saved to: {self.output_csv} ({len(to_save)} rows)")


def main():
    """
    CLI entry point for running the CSV address validator.

    Usage:
        python read_from_file.py <input_csv_path>
    """
    if len(sys.argv) != 2:
        print("❌ Usage: python read_from_file.py <path/to/input.csv>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        sys.exit(1)

    tester = AddressCSVTester(input_path)
    tester.load_addresses()
    tester.validate_addresses()
    tester.save_output()


if __name__ == "__main__":
    main()
