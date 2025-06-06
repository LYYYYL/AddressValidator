"""pytest configuration file."""

import os
import sys
from pathlib import Path

TESTS_DIR_PARENT = Path(__file__).parent.parent.resolve()

sys.path.insert(0, str(TESTS_DIR_PARENT / "src"))
sys.path.insert(0, str(TESTS_DIR_PARENT / "app"))

pytest_plugins = ["tests.fixtures.example_fixture"]


# MUST be set before any `postal` import happens
os.environ["LIBPOSTAL_DATA_DIR"] = "/home/anonymous/libpostal-lib/libpostal/"
