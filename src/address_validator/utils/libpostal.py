import os

os.environ["LIBPOSTAL_DATA_DIR"] = "/home/anonymous/libpostal-lib/libpostal/"

from postal.expand import expand_address
from postal.parser import parse_address


class CommonAddressUtils:
    @staticmethod
    def expand_address(raw_address: str) -> list[str]:
        return expand_address(raw_address)

    @staticmethod
    def parse_address(address: str) -> dict:
        return {label: value for value, label in parse_address(address)}
