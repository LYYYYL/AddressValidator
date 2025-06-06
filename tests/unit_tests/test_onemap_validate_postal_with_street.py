"""
Unit tests for OneMapValidatePostalWithStreetStep.

This step ensures that the returned postal code(s) from OneMap match the parsed one.
Handles cases like:
- Empty or error responses
- Mismatched postal codes
- Correct match and search field formatting
"""

from enum import Enum

import pytest

from address_validator.constants import (
    BLOCK_NUMBER,
    BUILDING_NAME,
    ONEMAP_POSTAL_CODE,
    ONEMAP_RESULTS_BY_ADDRESS,
    PARSED_ADDRESS,
    POSTAL_CODE,
    STREET_NAME,
    VALIDATE_STATUS,
)
from address_validator.steps.onemap_validate_postal_with_street import (
    OneMapValidatePostalWithStreetStep,
)
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    """Returns a shared instance of OneMapValidatePostalWithStreetStep."""
    return OneMapValidatePostalWithStreetStep()


class FakeStatus(Enum):
    """Fake status enum to simulate OneMap responses."""

    OK = 1
    ERROR = 2


class FakeResult:
    """Fake OneMapSearchResult with status and list of result addresses."""

    def __init__(self, status, result_addrs):
        """Initialize with a status and list of address dicts."""
        self.status = status
        self.result_addrs = result_addrs


class DummyClient:
    """Dummy OneMapClient that returns a predefined FakeResult."""

    def __init__(self, fake_result: FakeResult):
        """Initialize with the result to be returned on .search()."""
        self._fake_result = fake_result

    def search(self, search_field: str):
        """Return the preloaded FakeResult."""
        return self._fake_result


@pytest.mark.parametrize(
    "status, addrs, expected_validate_status",
    [
        # 1) status != OK → set validate_status to that status
        (
            FakeStatus.ERROR,
            [{ONEMAP_POSTAL_CODE: "123456", "block": "1", STREET_NAME: "Some Rd"}],
            FakeStatus.ERROR,
        ),
        # 2) status == OK but empty result_addrs → set NO_ONEMAP_MATCH
        (FakeStatus.OK, [], ValidateStatus.NO_ONEMAP_MATCH),
    ],
)
def test_non_ok_and_empty_cases(monkeypatch, step, status, addrs, expected_validate_status):
    """Should handle non-OK and empty response cases from OneMap."""
    fake_result = FakeResult(status, addrs)

    # Because the step does "from address_validator.onemap_client import OneMapClient",
    # we need to patch OneMapClient in the step's own module:
    monkeypatch.setattr(
        "address_validator.steps.onemap_validate_postal_with_street.OneMapClient",
        lambda: DummyClient(fake_result),
    )

    ctx = {
        PARSED_ADDRESS: {
            BLOCK_NUMBER: "10",
            STREET_NAME: "Main St",
            BUILDING_NAME: None,
            POSTAL_CODE: "123456",
        }
    }

    updated = step(ctx.copy())

    # 1) onemap_search_with_street must always be set (even if empty)
    assert updated[ONEMAP_RESULTS_BY_ADDRESS] == addrs

    # 2) validate_status must match what we expect
    assert updated[VALIDATE_STATUS] == expected_validate_status


def test_postcode_mismatch(monkeypatch, step):
    """Should set ADDRESS_AND_POSTCODE_MISMATCH when no postal matches are found."""
    addrs = [
        {ONEMAP_POSTAL_CODE: "111111"},
        {ONEMAP_POSTAL_CODE: "222222"},
    ]
    fake_result = FakeResult(FakeStatus.OK, addrs)

    monkeypatch.setattr(
        "address_validator.steps.onemap_validate_postal_with_street.OneMapClient",
        lambda: DummyClient(fake_result),
    )

    ctx = {
        PARSED_ADDRESS: {
            BLOCK_NUMBER: "5",
            STREET_NAME: "Edge Rd",
            BUILDING_NAME: "BlockA",
            POSTAL_CODE: "333333",
        }
    }

    updated = step(ctx.copy())

    # 1) onemap_search_with_street was recorded
    assert updated[ONEMAP_RESULTS_BY_ADDRESS] == addrs
    # 2) parsed_addr postcode "333333" is not in ["111111","222222"] => mismatch
    assert updated[VALIDATE_STATUS] == ValidateStatus.ADDRESS_AND_POSTCODE_MISMATCH


def test_postcode_match_no_validate_status(monkeypatch, step):
    """Should not set validate_status if any result matches the parsed postal code."""
    target_postcode = "987654"
    addrs = [
        {ONEMAP_POSTAL_CODE: "123123"},
        {ONEMAP_POSTAL_CODE: target_postcode},  # this one matches
        {ONEMAP_POSTAL_CODE: "555555"},
    ]
    fake_result = FakeResult(FakeStatus.OK, addrs)

    monkeypatch.setattr(
        "address_validator.steps.onemap_validate_postal_with_street.OneMapClient",
        lambda: DummyClient(fake_result),
    )

    ctx = {
        PARSED_ADDRESS: {
            BLOCK_NUMBER: "20",
            STREET_NAME: "Match St",
            BUILDING_NAME: "Apt1",
            POSTAL_CODE: target_postcode,
        }
    }

    updated = step(ctx.copy())

    assert updated[ONEMAP_RESULTS_BY_ADDRESS] == addrs
    # Because one of the result_addrs matches the parsed_addr postcode, no mismatch
    assert VALIDATE_STATUS not in updated


def test_search_field_construction_with_building_none(monkeypatch, step):
    """Should treat None building name as empty string and construct proper search field."""
    addrs = [{ONEMAP_POSTAL_CODE: "000000"}]
    fake_result = FakeResult(FakeStatus.OK, addrs)

    captured = {}

    class CapturingClient(DummyClient):
        def __init__(self, fake_result):
            super().__init__(fake_result)

        def search(self, search_field):
            captured["search_field"] = search_field
            return super().search(search_field)

    monkeypatch.setattr(
        "address_validator.steps.onemap_validate_postal_with_street.OneMapClient",
        lambda: CapturingClient(fake_result),
    )

    parsed_addr = {
        BLOCK_NUMBER: "7",
        STREET_NAME: "NoBuilding Rd",
        BUILDING_NAME: None,
        POSTAL_CODE: "000000",
    }
    ctx = {PARSED_ADDRESS: parsed_addr}

    updated = step(ctx.copy())

    # 1) onemap_search_with_street must be recorded
    assert updated[ONEMAP_RESULTS_BY_ADDRESS] == addrs

    # 2) Because building was None → "",
    #    search_field should be "7 NoBuilding Rd " (with trailing space)
    assert captured["search_field"] == "7 NoBuilding Rd "
