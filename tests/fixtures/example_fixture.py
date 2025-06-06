"""Defines fixtures that can be used in the tests."""

from uuid import uuid4

import pytest

from tests.consts import PROJECT_DIR


@pytest.fixture(scope="session")
def generate_test_session_id() -> str:
    """Return a unique test session ID."""
    test_session_id = str(PROJECT_DIR.name) + str(uuid4())[:6]
    return test_session_id
