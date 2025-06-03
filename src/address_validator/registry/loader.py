"""
This module provides a dynamic registration mechanism for address validation
steps by country. Each country-specific module located in
`address_validator.registry` is expected to register its step loader function
using the `register_steps_for_country` decorator.

When `load_all_country_steps` is called, it dynamically imports all modules
under the registry package so their registration decorators are executed.

Usage:
    1. Define your country's step loader function and decorate it:
        @register_steps_for_country("SG")
        def get_steps(): ...

    2. Call `load_all_country_steps()` once at startup to populate the
       `country_step_registry`.

Attributes:
    country_step_registry (dict[str, Callable]):
        Maps country codes (e.g., "SG") to functions that return a list of steps.

"""

import importlib
import pkgutil
from typing import Callable

import address_validator.registry as registry_pkg

country_step_registry: dict[str, Callable] = {}


def register_steps_for_country(country_code: str):
    """
    Decorator to register a function that returns validation steps for a specific country.

    Args:
        country_code (str): ISO-style country code, e.g., "SG".

    Returns:
        Callable: A decorator that registers the function in `country_step_registry`.
    """

    def wrapper(step_list_fn):
        country_step_registry[country_code] = step_list_fn
        return step_list_fn

    return wrapper


def load_all_country_steps():
    """
    Dynamically import all modules in the `address_validator.registry` package to trigger step registration.

    This function looks for all submodules in the `address_validator.registry` package
    and imports them so that any `@register_steps_for_country(...)` decorators are executed.

    Raises:
        ImportError: If any module in the registry package fails to import.
    """
    package = "address_validator.registry"
    for _, modname, _ in pkgutil.iter_modules(registry_pkg.__path__):
        full_module = f"{package}.{modname}"
        importlib.import_module(full_module)
