from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable

from address_validator.registry.loader import country_step_registry, load_all_country_steps
from address_validator.search import SearchSrc


@dataclass
class ValidationResult:
    raw_addr: str
    norm_addr: str | None  # the cleaned/standardized address
    parsed_addr: dict[str, str] | None
    property_type: str | None  # e.g. "HDB", "Condo", "Landed"

    status: str | None  # "valid" / "not_found" / "error"
    validated_at: datetime | None
    source: SearchSrc | None  # "cache" / "onemap" / "streetdirectory"


class AddressValidationFlow:
    @classmethod
    def validate(cls, address: str, country: str, ctx: dict | None = None) -> dict:
        load_all_country_steps()
        steps_fn = country_step_registry.get(country)
        if not steps_fn:
            return {"valid": False, "error": "Unsupported country"}

        builder = ValidationFlowBuilder(address, extra_context=ctx)
        for step in steps_fn():
            builder.add_step(step)
        return builder.build()


class ValidationFlowBuilder:
    def __init__(self, raw_address: str, extra_context: dict | None = None):
        self.raw_address = raw_address
        self.steps: list[Callable[[dict], dict]] = []

        # Initialize context with raw address and default valid status
        self.context: dict[str, object] = {
            "raw_address": raw_address,
            "validate_status": ValidateStatus.VALID,
        }

        # Merge extra fields like street/city/postal if provided
        if extra_context:
            self.context.update(extra_context)

    def add_step(self, step_fn: Callable[[dict], dict]) -> "ValidationFlowBuilder":
        self.steps.append(step_fn)
        return self

    def build(self) -> dict:
        for step in self.steps:
            step_name = getattr(step, "__class__", type(step)).__name__
            # print(f"\n➡️ Running step: {step_name}")
            result = step(self.context)
            # print(f"🧪 Context after {step_name}: {result}")
            if result.get("validate_status") != ValidateStatus.VALID:
                print(f"❌ Validation failed at step: {step_name}")
                # print("Flow builder returning {result}")
                return result  # Early exit on failure
        return result


class ValidateStatus(Enum):
    VALID = "valid"
    ADDRESS_EMPTY = "address_empty"
    EXPANSION_FAILED = "expansion_failed"
    PARSE_FAILED = "parse_failed"
    POSTAL_CODE_MISSING = "postal_code_missing"
    STREET_NAME_MISSING = "street_name_missing"
    UNIT_NUMBER_MISSING = "unit_number_missing"  # Optional depending on context
    BLOCK_NUMBER_MISSING = "block_number_missing"
    BLOCK_NUMBER_MISMATCH = "block_number_mismatch"

    INVALID_POSTAL_CODE = "invalid_postal_code"
    ONEMAP_POSTAL_LOOKUP_FAILED = "onemap_lookup_failed"
    MULTIPLE_MATCHES = "multiple_onemap_matches"
    NO_ONEMAP_MATCH = "no_onemap_match"
    NO_STREETDIRECTORY_MATCH = "no_streetdirectory_match"
    BLK_STREET_AND_POSTCODE_MISMATCH = "block_street_and_postcode_mismatch"
    UNSUPPORTED_COUNTRY = "unsupported_country"
    MISSING_COUNTRY_INFO = "missing_country_info"
    VALIDATION_INTERNAL_ERROR = "validation_internal_error"
    STEP_EXECUTION_FAILED = "step_execution_failed"
    TIMEOUT_OCCURRED = "timeout_occurred"
    DEPENDENCY_FAILURE = "dependency_failure"
