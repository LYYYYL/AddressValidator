"""
Wrapper utilities for libpostal address parsing and expansion.

This module provides static methods to normalize and parse freeform
addresses using libpostal's `expand_address` and `parse_address` functions.
"""

import os

os.environ["LIBPOSTAL_DATA_DIR"] = "/home/anonymous/libpostal-lib/libpostal/"

from postal.expand import expand_address
from postal.parser import parse_address


class CommonAddressUtils:
    """
    Utility methods for working with libpostal address parsing and expansion.

    Includes normalization (e.g., "Rd" → "Road") and component parsing into
    structured dictionaries (e.g., {'road': 'orchard', 'house_number': '1'}).
    """

    @staticmethod
    def expand_address(raw_address: str) -> list[str]:
        """
        Generate alternative normalized forms of an address using libpostal.

        Args:
            raw_address (str): The original raw address string.

        Returns:
            list[str]: A list of expanded address variants.
        """
        return expand_address(raw_address)

    @staticmethod
    def parse_address(address: str) -> dict:
        """
        Parse an address into labeled components using libpostal.

        Args:
            address (str): The address string to parse.

        Returns:
            dict: A dictionary mapping components (e.g., 'road', 'postcode') to their values.
        """
        return {label: value for value, label in parse_address(address)}
