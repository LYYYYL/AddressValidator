# tests/unit_tests/test_validation_flow_and_status.py

from datetime import datetime, timezone

import pytest

from address_validator import validation as validation_module
from address_validator.registry.loader import country_step_registry, load_all_country_steps
from address_validator.search import SearchSrc
from address_validator.validation import ValidateStatus


# ----------------------------
# Tests for ValidateStatus enum
# ----------------------------
def test_validate_status_members_exist():
    """
    Ensure that key members of the ValidateStatus enum exist and have correct values.
    """
    # Spot-check a few entries
    assert ValidateStatus.VALID.value == "valid"
    assert ValidateStatus.ADDRESS_EMPTY.value == "address_empty"
    assert ValidateStatus.STREET_NAME_MISSING.value == "street_name_missing"
    assert ValidateStatus.UNIT_NUMBER_MISSING.value == "unit_number_missing"
    assert ValidateStatus.NO_ONEMAP_MATCH.value == "no_onemap_match"
    assert ValidateStatus.TIMEOUT_OCCURRED.value == "timeout_occurred"
    # Ensure that all members are indeed instances of ValidateStatus
    for member in ValidateStatus:
        assert isinstance(member, ValidateStatus)


# ----------------------------------------
# Tests for AddressValidationFlow & Builder
# ----------------------------------------
from address_validator.validation import AddressValidationFlow, ValidationFlowBuilder


def test_validate_unsupported_country(monkeypatch):
    """
    If no steps are registered for a given country, AddressValidationFlow.validate should
    immediately return {"valid": False, "error": "Unsupported country"}.
    """
    # Temporarily clear registry for a fake country
    country_step_registry.clear()

    result = AddressValidationFlow.validate("123 Main St", country="Narnia")
    assert result == {"valid": False, "error": "Unsupported country"}


def test_builder_early_exit_on_failure(monkeypatch):
    """
    Given a sequence of steps, if any step sets validate_status != VALID,
    builder.build() should immediately return that context dictionary.
    """

    # Create two dummy steps:
    def step1(ctx):
        # step1 does nothing, leaves status VALID
        return ctx

    def step2(ctx):
        # step2 fails with a specific status
        ctx["validate_status"] = ValidateStatus.PARSE_FAILED
        return ctx

    def step3(ctx):
        # This should never run
        ctx["validate_status"] = ValidateStatus.BLOCK_NUMBER_MISMATCH
        return ctx

    builder = ValidationFlowBuilder(raw_address="foo", extra_context=None)
    # Initial context has validate_status = VALID
    assert builder.context["validate_status"] == ValidateStatus.VALID

    builder.add_step(step1)
    builder.add_step(step2)
    builder.add_step(step3)

    result_ctx = builder.build()
    # After step2, builder should exit early with PARSE_FAILED
    assert result_ctx["validate_status"] == ValidateStatus.PARSE_FAILED
    # step3 should never have run, so context should not have BLOCK_NUMBER_MISMATCH
    assert result_ctx["validate_status"] != ValidateStatus.BLOCK_NUMBER_MISMATCH


def test_builder_all_steps_pass(monkeypatch):
    """
    If all steps leave status VALID, builder.build() should return the final context
    with validate_status still VALID.
    """

    def step1(ctx):
        ctx["foo"] = 1
        return ctx

    def step2(ctx):
        ctx["bar"] = 2
        return ctx

    builder = ValidationFlowBuilder(raw_address="bar", extra_context={"initial": True})
    builder.add_step(step1)
    builder.add_step(step2)

    final_ctx = builder.build()
    assert final_ctx["validate_status"] == ValidateStatus.VALID
    assert final_ctx["foo"] == 1
    assert final_ctx["bar"] == 2
    assert final_ctx["initial"] is True


def test_flow_integration_register_and_run(monkeypatch):
    """
    Simulate registering steps for a fake country, then calling AddressValidationFlow.validate.
    Confirm that registered steps run in order and early fail/return works.
    """

    # Create dummy steps to register
    def fake_step_good(ctx):
        ctx["step_good_ran"] = True
        return ctx

    def fake_step_bad(ctx):
        ctx["step_bad_ran"] = True
        ctx["validate_status"] = ValidateStatus.BLOCK_NUMBER_MISMATCH
        return ctx

    def fake_step_never(ctx):
        ctx["should_not_run"] = True
        return ctx

    # Monkeypatch registry to use our fake country "Atlantis"
    monkeypatch.setitem(country_step_registry, "Atlantis", lambda: [fake_step_good, fake_step_bad, fake_step_never])

    # Run validation
    result = AddressValidationFlow.validate("1 Atlantis Ave", country="Atlantis")

    # Because fake_step_bad sets BLOCK_NUMBER_MISMATCH, flow should stop there
    assert result["step_good_ran"] is True
    assert result["step_bad_ran"] is True
    assert "should_not_run" not in result
    assert result["validate_status"] == ValidateStatus.BLOCK_NUMBER_MISMATCH


# ----------------------------------------
# Test default registry is not empty (if actual countries are defined)
# ----------------------------------------
@pytest.mark.skip
def test_default_registry_not_empty():
    """
    After load_all_country_steps(), there should be at least one entry in country_step_registry.
    """
    # (Assumes your real loader populates at least one country)
    load_all_country_steps()
    assert len(country_step_registry) >= 1


# ----------------------------------------
# Test that ValidationResult dataclass holds its fields correctly
# ----------------------------------------
def test_validation_result_dataclass():
    """
    Ensure that ValidationResult can be instantiated and its fields accessed.
    """
    from address_validator.validation import ValidationResult

    vr = ValidationResult(
        raw_addr="123 Example St",
        norm_addr="123 Example St, Unit 01-01",
        parsed_addr={"road": "Example St", "unit": "01-01"},
        property_type="HDB",
        status="valid",
        validated_at=datetime.now(timezone.utc),
        source=SearchSrc.CACHE,
    )

    assert vr.raw_addr == "123 Example St"
    assert vr.norm_addr.startswith("123 Example St")
    assert vr.parsed_addr["road"] == "Example St"
    assert vr.property_type == "HDB"
    assert vr.status == "valid"
    assert isinstance(vr.validated_at, datetime)
    assert vr.source == SearchSrc.CACHE
