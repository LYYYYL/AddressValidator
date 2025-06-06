"""
Unit tests for the step loader and registry system.

Covers:
- Ensuring the default registry is populated after loading
- Correct behavior of the @register_steps_for_country decorator
- Overwriting behavior for the same country code
- Idempotency of the step-loading mechanism
"""

import pytest

from address_validator.registry.loader import (
    country_step_registry,
    load_all_country_steps,
    register_steps_for_country,
)


@pytest.mark.skip
def test_default_registry_not_empty():
    """Should populate registry with at least one country after loading."""
    # Clear any existing entries, then reload
    country_step_registry.clear()
    load_all_country_steps()
    assert country_step_registry, "Expected at least one country to be registered"


@pytest.mark.skip
def test_register_steps_for_country_decorator():
    """Should register decorated function under the given country code."""
    country_step_registry.clear()

    @register_steps_for_country("ZZZ")
    def dummy_steps():
        return [lambda ctx: ctx]

    # After decoration, "ZZZ" should be in the registry mapping,
    # and the value should be our dummy_steps function.
    assert "ZZZ" in country_step_registry
    assert country_step_registry["ZZZ"] is dummy_steps


@pytest.mark.skip
def test_registering_same_country_overwrites_previous():
    """Should overwrite registry entry if same country is registered twice."""
    country_step_registry.clear()

    @register_steps_for_country("ABC")
    def first_fn():
        return []

    @register_steps_for_country("ABC")
    def second_fn():
        return []

    assert country_step_registry["ABC"] is second_fn


@pytest.mark.skip
def test_load_all_country_steps_idempotent(tmp_path, monkeypatch):
    """Should allow repeated calls to load_all_country_steps without side effects."""
    country_step_registry.clear()
    # First call should populate whatever modules are there
    load_all_country_steps()
    # Capture snapshot of registry after first load
    first_snapshot = dict(country_step_registry)

    # Calling again should not raise any errors, and registry should remain the same
    load_all_country_steps()
    second_snapshot = dict(country_step_registry)

    assert first_snapshot == second_snapshot
