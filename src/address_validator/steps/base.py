"""
Abstract base class for address validation steps.

This module defines the `ValidationStep` interface, which all validation
steps in the address validation pipeline must implement. Each step performs
some processing on the input context dictionary and returns the updated context.
"""

from abc import ABC, abstractmethod


class ValidationStep(ABC):
    """
    Abstract base class for a validation step in the address pipeline.

    Each subclass must implement the `__call__` method, which takes a context
    dictionary (`ctx`) and returns a (possibly modified) version of that context.
    This allows for flexible and composable validation pipelines across countries.

    Example:
        class MyStep(ValidationStep):
            def __call__(self, ctx: dict) -> dict:
                ctx["processed"] = True
                return ctx
    """

    @abstractmethod
    def __call__(self, ctx: dict) -> dict:
        """
        Process the given address validation context.

        Args:
            ctx (dict): The current address validation context.

        Returns:
            dict: The updated context after applying this step.
        """
        pass
