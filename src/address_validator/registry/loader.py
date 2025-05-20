import importlib
import pkgutil
from typing import Callable

import address_validator.registry as registry_pkg

country_step_registry: dict[str, Callable] = {}


def register_steps_for_country(country_code: str):
    def wrapper(step_list_fn):
        country_step_registry[country_code] = step_list_fn
        return step_list_fn

    return wrapper


def load_all_country_steps():
    package = "address_validator.registry"
    for _, modname, _ in pkgutil.iter_modules(registry_pkg.__path__):
        full_module = f"{package}.{modname}"
        importlib.import_module(full_module)
