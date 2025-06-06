"""
Unit tests for validation logic including AddressValidationFlow and ValidationFlowBuilder.

Tests:
- Unsupported country behavior
- Early exit from step builders
- End-to-end flow with registered dummy steps
- ValidationResult data structure
"""

import pytest

from address_validator.constants import STREET_NAME, UNIT_NUMBER, VALIDATE_STATUS
from address_validator.registry.loader import country_step_registry, load_all_country_steps
from address_validator.search import SearchSrc
from address_validator.utils.common import current_utc_isoformat
from address_validator.validation import AddressValidationFlow, ValidateStatus, ValidationFlowBuilder


def test_validate_unsupported_country(monkeypatch):
    """Should return early with 'Unsupported country' error if none registered."""
    # Temporarily clear registry for a fake country
    country_step_registry.clear()

    result = AddressValidationFlow.validate("123 Main St", country="Narnia")
    assert result == {"valid": False, "error": "Unsupported country"}


def test_builder_early_exit_on_failure(monkeypatch):
    """Should stop running steps when a failure status is set in the context."""

    # Create two dummy steps:
    def step1(ctx):
        # step1 does nothing, leaves status VALID
        return ctx

    def step2(ctx):
        # step2 fails with a specific status
        ctx[VALIDATE_STATUS] = ValidateStatus.PARSE_FAILED
        return ctx

    def step3(ctx):
        # This should never run
        ctx[VALIDATE_STATUS] = ValidateStatus.BLOCK_NUMBER_MISMATCH
        return ctx

    builder = ValidationFlowBuilder(raw_address="foo", extra_context=None)
    # Initial context has validate_status = VALID
    assert builder.context[VALIDATE_STATUS] == ValidateStatus.VALID

    builder.add_step(step1)
    builder.add_step(step2)
    builder.add_step(step3)

    result_ctx = builder.build()
    # After step2, builder should exit early with PARSE_FAILED
    assert result_ctx[VALIDATE_STATUS] == ValidateStatus.PARSE_FAILED
    # step3 should never have run, so context should not have BLOCK_NUMBER_MISMATCH
    assert result_ctx[VALIDATE_STATUS] != ValidateStatus.BLOCK_NUMBER_MISMATCH


def test_builder_all_steps_pass(monkeypatch):
    """Should return context with VALID status if all steps succeed."""

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
    assert final_ctx[VALIDATE_STATUS] == ValidateStatus.VALID
    assert final_ctx["foo"] == 1
    assert final_ctx["bar"] == 2
    assert final_ctx["initial"] is True


def test_flow_integration_register_and_run(monkeypatch):
    """Should register and run dummy steps for a fake country."""

    # Create dummy steps to register
    def fake_step_good(ctx):
        ctx["step_good_ran"] = True
        return ctx

    def fake_step_bad(ctx):
        ctx["step_bad_ran"] = True
        ctx[VALIDATE_STATUS] = ValidateStatus.BLOCK_NUMBER_MISMATCH
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
    assert result[VALIDATE_STATUS] == ValidateStatus.BLOCK_NUMBER_MISMATCH


# ----------------------------------------
# Test default registry is not empty (if actual countries are defined)
# ----------------------------------------
@pytest.mark.skip
def test_default_registry_not_empty():
    """Should contain at least one country step after loading defaults."""
    # (Assumes your real loader populates at least one country)
    load_all_country_steps()
    assert len(country_step_registry) >= 1


# ----------------------------------------
# Test that ValidationResult dataclass holds its fields correctly
# ----------------------------------------
def test_validation_result_dataclass():
    """Should store and expose all fields correctly in ValidationResult."""
    from address_validator.validation import ValidationResult

    vr = ValidationResult(
        raw_addr="123 Example St",
        norm_addr="123 Example St, Unit 01-01",
        parsed_addr={STREET_NAME: "Example St", UNIT_NUMBER: "01-01"},
        property_type="HDB",
        status="valid",
        validated_at=current_utc_isoformat(),
        source=SearchSrc.CACHE,
    )

    assert vr.raw_addr == "123 Example St"
    assert vr.norm_addr.startswith("123 Example St")
    assert vr.parsed_addr[STREET_NAME] == "Example St"
    assert vr.property_type == "HDB"
    assert vr.status == "valid"
    assert vr.source == SearchSrc.CACHE
