# tests/unit_tests/test_onemap_validate_postal_with_street.py

from enum import Enum

import pytest

from address_validator.onemap_client import ONEMAP_POSTCODE_KEY
from address_validator.steps.onemap_validate_postal_with_street import (
    OneMapValidatePostalWithStreetStep,
)
from address_validator.validation import ValidateStatus


@pytest.fixture
def step():
    return OneMapValidatePostalWithStreetStep()


class FakeStatus(Enum):
    OK = 1
    ERROR = 2


class FakeResult:
    def __init__(self, status, result_addrs):
        """
        Create a fake OneMap response:
        - status should be a member of FakeStatus,
        - result_addrs is a list of dicts, each containing ONEMAP_POSTCODE_KEY (and other keys).
        """
        self.status = status
        self.result_addrs = result_addrs


class DummyClient:
    """
    DummyClient simply returns the pre-packaged FakeResult when .search() is called.
    """

    def __init__(self, fake_result: FakeResult):
        self._fake_result = fake_result

    def search(self, search_field: str):
        return self._fake_result


@pytest.mark.parametrize(
    "status, addrs, expected_validate_status",
    [
        # 1) status != OK → set validate_status to that status
        (
            FakeStatus.ERROR,
            [{ONEMAP_POSTCODE_KEY: "123456", "block": "1", "road": "Some Rd"}],
            FakeStatus.ERROR,
        ),
        # 2) status == OK but empty result_addrs → set NO_ONEMAP_MATCH
        (FakeStatus.OK, [], ValidateStatus.NO_ONEMAP_MATCH),
    ],
)
def test_non_ok_and_empty_cases(monkeypatch, step, status, addrs, expected_validate_status):
    """
    - If status != OK, ctx['validate_status'] == status
    - If status == OK but result_addrs == [], ctx['validate_status'] == NO_ONEMAP_MATCH
    In all cases, ctx['onemap_search_with_street'] must be set to result_addrs.
    """
    fake_result = FakeResult(status, addrs)

    # Because the step does "from address_validator.onemap_client import OneMapClient",
    # we need to patch OneMapClient in the step's own module:
    monkeypatch.setattr(
        "address_validator.steps.onemap_validate_postal_with_street.OneMapClient",
        lambda: DummyClient(fake_result),
    )

    ctx = {
        "parsed": {
            "house_number": "10",
            "road": "Main St",
            "building": None,
            "postcode": "123456",
        }
    }

    updated = step(ctx.copy())

    # 1) onemap_search_with_street must always be set (even if empty)
    assert updated["onemap_search_with_street"] == addrs

    # 2) validate_status must match what we expect
    assert updated["validate_status"] == expected_validate_status


def test_postcode_mismatch(monkeypatch, step):
    """
    If status == OK and result_addrs is non-empty, but none contain
    the parsed postcode, then ctx['validate_status'] == BLK_STREET_AND_POSTCODE_MISMATCH.
    """
    addrs = [
        {ONEMAP_POSTCODE_KEY: "111111"},
        {ONEMAP_POSTCODE_KEY: "222222"},
    ]
    fake_result = FakeResult(FakeStatus.OK, addrs)

    monkeypatch.setattr(
        "address_validator.steps.onemap_validate_postal_with_street.OneMapClient",
        lambda: DummyClient(fake_result),
    )

    ctx = {
        "parsed": {
            "house_number": "5",
            "road": "Edge Rd",
            "building": "BlockA",
            "postcode": "333333",
        }
    }

    updated = step(ctx.copy())

    # 1) onemap_search_with_street was recorded
    assert updated["onemap_search_with_street"] == addrs
    # 2) parsed postcode "333333" is not in ["111111","222222"] => mismatch
    assert updated["validate_status"] == ValidateStatus.BLK_STREET_AND_POSTCODE_MISMATCH


def test_postcode_match_no_validate_status(monkeypatch, step):
    """
    If status == OK and at least one returned address has the same postcode,
    then no 'validate_status' key should be set.
    """
    target_postcode = "987654"
    addrs = [
        {ONEMAP_POSTCODE_KEY: "123123"},
        {ONEMAP_POSTCODE_KEY: target_postcode},  # this one matches
        {ONEMAP_POSTCODE_KEY: "555555"},
    ]
    fake_result = FakeResult(FakeStatus.OK, addrs)

    monkeypatch.setattr(
        "address_validator.steps.onemap_validate_postal_with_street.OneMapClient",
        lambda: DummyClient(fake_result),
    )

    ctx = {
        "parsed": {
            "house_number": "20",
            "road": "Match St",
            "building": "Apt1",
            "postcode": target_postcode,
        }
    }

    updated = step(ctx.copy())

    assert updated["onemap_search_with_street"] == addrs
    # Because one of the result_addrs matches the parsed postcode, no mismatch
    assert "validate_status" not in updated


def test_search_field_construction_with_building_none(monkeypatch, step):
    """
    If parsed['building'] is None, we treat building as "",
    so search_field becomes "<house_number> <road> " (with trailing space).
    We verify that by capturing the search_field that DummyClient.search() sees.
    """
    addrs = [{ONEMAP_POSTCODE_KEY: "000000"}]
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

    parsed = {
        "house_number": "7",
        "road": "NoBuilding Rd",
        "building": None,
        "postcode": "000000",
    }
    ctx = {"parsed": parsed}

    updated = step(ctx.copy())

    # 1) onemap_search_with_street must be recorded
    assert updated["onemap_search_with_street"] == addrs

    # 2) Because building was None → "",
    #    search_field should be "7 NoBuilding Rd " (with trailing space)
    assert captured["search_field"] == "7 NoBuilding Rd "
