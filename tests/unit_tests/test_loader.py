# tests/unit_tests/test_loader_registry.py

import importlib

import pytest

from address_validator.registry.loader import country_step_registry, load_all_country_steps, register_steps_for_country


def test_default_registry_not_empty():
    """
    After importing all registry modules via load_all_country_steps(),
    country_step_registry should have at least one entry (assuming
    your code actually registers some country steps).
    """
    # Clear any existing entries, then reload
    country_step_registry.clear()
    load_all_country_steps()
    assert country_step_registry, "Expected at least one country to be registered"


def test_register_steps_for_country_decorator():
    """
    If we define a dummy step function and decorate it with
    @register_steps_for_country('ZZZ'), then country_step_registry
    should contain 'ZZZ' mapped to our function.
    """
    country_step_registry.clear()

    @register_steps_for_country("ZZZ")
    def dummy_steps():
        return [lambda ctx: ctx]

    # After decoration, "ZZZ" should be in the registry mapping,
    # and the value should be our dummy_steps function.
    assert "ZZZ" in country_step_registry
    assert country_step_registry["ZZZ"] is dummy_steps


def test_registering_same_country_overwrites_previous():
    """
    If you decorate two different functions with the same country code,
    the registry should end up mapping to the second one (i.e. last one wins).
    """
    country_step_registry.clear()

    @register_steps_for_country("ABC")
    def first_fn():
        return []

    @register_steps_for_country("ABC")
    def second_fn():
        return []

    assert country_step_registry["ABC"] is second_fn


def test_load_all_country_steps_idempotent(tmp_path, monkeypatch):
    """
    load_all_country_steps should import each .py under address_validator/registry only once
    and not crash if called multiple times.
    We won't create real files here, but we can at least call it twice to make sure nothing breaks.
    """
    country_step_registry.clear()
    # First call should populate whatever modules are there
    load_all_country_steps()
    # Capture snapshot of registry after first load
    first_snapshot = dict(country_step_registry)

    # Calling again should not raise any errors, and registry should remain the same
    load_all_country_steps()
    second_snapshot = dict(country_step_registry)

    assert first_snapshot == second_snapshot
