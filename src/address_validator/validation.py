"""
Core validation pipeline that executes country-specific steps on raw addresses.

Includes the `AddressValidationFlow` entry point, step orchestration via
`ValidationFlowBuilder`, and the result structure used to report validation status.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable

from address_validator.constants import DEBUG_PRINT, RAW_ADDRESS, VALIDATE_STATUS, VALIDATED_AT
from address_validator.registry.loader import country_step_registry, load_all_country_steps
from address_validator.search import SearchSrc
from address_validator.utils.common import current_utc_isoformat


@dataclass
class ValidationResult:
    """
    Represents a structured result returned after address validation.

    Attributes:
        raw_addr (str): Original address input string.
        norm_addr (str | None): Cleaned or standardized address string.
        parsed_addr (dict | None): Parsed address components (e.g., house, road, unit).
        property_type (str | None): Inferred property type (e.g., HDB, Condo).
        status (str | None): Result status string ("valid", "not_found", "error").
        validated_at (datetime | None): When the validation occurred.
        source (SearchSrc | None): Source system used (cache, onemap, etc.).
    """

    raw_addr: str
    norm_addr: str | None  # the cleaned/standardized address
    parsed_addr: dict[str, str] | None
    property_type: str | None  # e.g. "HDB", "Condo", "Landed"

    status: str | None  # "valid" / "not_found" / "error"
    validated_at: datetime | None
    source: SearchSrc | None  # "cache" / "onemap" / "streetdirectory"


class AddressValidationFlow:
    """
    Public interface for validating addresses via the configured country pipeline.

    Usage:
        AddressValidationFlow.validate(address="123 HDB Street", country="SG")
    """

    @classmethod
    def validate(cls, address: str, country: str, ctx: dict | None = None) -> dict:
        """
        Run the full address validation pipeline for a given country.

        Args:
            address (str): The full raw address string to validate.
            country (str): Country code (e.g., "SG") to select the pipeline.
            ctx (dict | None): Optional pre-filled context with fields like postal, street, etc.

        Returns:
            dict: Final validation context, possibly containing errors or parsed results.
        """
        load_all_country_steps()
        steps_fn = country_step_registry.get(country)
        if not steps_fn:
            return {"valid": False, "error": "Unsupported country"}

        builder = ValidationFlowBuilder(address, extra_context=ctx)
        for step in steps_fn():
            builder.add_step(step)

        if ctx is not None:
            ctx[VALIDATED_AT] = current_utc_isoformat()
        return builder.build()


class ValidationFlowBuilder:
    """Builder class to apply a sequence of validation steps to an address context."""

    def __init__(self, raw_address: str, extra_context: dict | None = None):
        self.raw_address = raw_address
        self.steps: list[Callable[[dict], dict]] = []

        # Initialize context with raw address and default valid status
        self.context: dict[str, object] = {
            RAW_ADDRESS: raw_address,
            VALIDATE_STATUS: ValidateStatus.VALID,
        }

        # Merge extra fields like street/city/postal if provided
        if extra_context:
            self.context.update(extra_context)

    def add_step(self, step_fn: Callable[[dict], dict]) -> "ValidationFlowBuilder":
        """
        Register a step function to be run in sequence.

        Args:
            step_fn (Callable): A step that accepts and returns a context dict.

        Returns:
            ValidationFlowBuilder: Fluent self-return for chaining.
        """
        self.steps.append(step_fn)
        return self

    def build(self) -> dict:
        """
        Execute the registered steps in order until one fails.

        Returns:
            dict: The final validation context, or early failure result.
        """
        for step in self.steps:
            step_name = getattr(step, "__class__", type(step)).__name__

            if DEBUG_PRINT:
                print(f"\n➡️ Running step: {step_name}")
            result = step(self.context)
            if DEBUG_PRINT:
                print(f"🧪 Context after {step_name}: {result}")
            if result.get(VALIDATE_STATUS) != ValidateStatus.VALID:
                if DEBUG_PRINT:
                    print(f"❌ Validation failed at step: {step_name}")
                    print("Flow builder returning {result}")
                return result  # Early exit on failure
        return result


class ValidateStatus(Enum):
    """
    Enum of all known validation statuses in the pipeline.

    Used to determine step failure, user feedback, and downstream logic.
    """

    VALID = "Valid"
    ADDRESS_EMPTY = "Address empty"
    EXPANSION_FAILED = "expansion_failed"
    PARSE_FAILED = "parse_failed"
    POSTAL_CODE_MISSING = "Postal code missing"
    STREET_NAME_MISSING = "Street name missing"
    UNIT_NUMBER_MISSING = "Unit number missing"  # Optional depending on context
    BLOCK_NUMBER_MISSING = "Block number missing"
    BLOCK_NUMBER_MISMATCH = "Block number mismatch"

    INVALID_POSTAL_CODE = "Invalid postal code"
    ONEMAP_POSTAL_LOOKUP_FAILED = "onemap_lookup_failed"
    MULTIPLE_MATCHES = "multiple_onemap_matches"
    NO_ONEMAP_MATCH = "no_onemap_match"
    NO_STREETDIRECTORY_MATCH = "no_streetdirectory_match"
    ADDRESS_AND_POSTCODE_MISMATCH = "Block/Street and postal code do not match"
    UNSUPPORTED_COUNTRY = "unsupported_country"
    MISSING_COUNTRY_INFO = "missing_country_info"
    VALIDATION_INTERNAL_ERROR = "validation_internal_error"
    STEP_EXECUTION_FAILED = "step_execution_failed"
    TIMEOUT_OCCURRED = "Timeout occured"
    DEPENDENCY_FAILURE = "dependency_failure"
