"""
FastAPI route for validating a single address via POST.

Provides an endpoint at `/validation/` which accepts a raw address string and
optional pre-parsed context fields, then returns structured validation results.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from address_validator.constants import (
    COUNTRY_CODE_SINGAPORE,
    PARSED_ADDRESS,
    PROPERTY_TYPE,
    RAW_ADDRESS,
    VALIDATE_STATUS,
    VALIDATED_AT,
)
from address_validator.validation import AddressValidationFlow

router = APIRouter(prefix="/validation", tags=["validation"])


class ValidationRequest(BaseModel):
    """
    Request body for the address validation endpoint.

    Attributes:
        address (str): Raw address string (e.g., "288E Jurong East Street 21, #12-34, Singapore 605288").
        country (str): Country code (defaults to SG).
        extra_context (dict | None): Optional parsed fields to assist validation.
    """

    address: str = Field(..., json_schema_extra={"example": "288E Jurong East Street 21, #12-34, Singapore 605288"})

    country: str = Field(
        COUNTRY_CODE_SINGAPORE,
        json_schema_extra={"example": COUNTRY_CODE_SINGAPORE, "description": "country code (defaults to SG)"},
    )
    extra_context: dict[str, Any] | None = Field(
        None, description="Optional parsed_addr fields (e.g. {parsed_addr: {...}})"
    )


class ValidationResponse(BaseModel):
    """
    Response body returned after successful address validation.

    Attributes:
        raw_address (str): The original address string.
        parsed_address (dict): Parsed address components (e.g. block, street, unit).
        property_type (str | None): Detected property type, if any.
        validate_status (str): Validation outcome (e.g. valid, mismatch).
        validated_at (datetime | None): Timestamp of validation.
        final_context (dict): The full result context for debugging.
    """

    raw_address: str | None
    parsed_address: dict[str, Any] | None
    property_type: str | None
    validate_status: str | None
    validated_at: datetime | None
    # We’ll also return the entire context dict so the caller can inspect it:
    final_context: dict[str, Any]


###################################################################################################
# routers
###################################################################################################


@router.post("/", response_model=ValidationResponse)
async def validate_address(request: ValidationRequest):
    """
    Validate a single address by executing the configured pipeline.

    Args:
        request (ValidationRequest): Request body with address and optional context.

    Returns:
        ValidationResponse: Structured validation result.

    Raises:
        HTTPException: If any unexpected error occurs during validation.
    """
    try:
        # todo: move extraction to its own function
        result_ctx = AddressValidationFlow.validate(
            address=request.address, country=request.country, ctx=request.extra_context or {}
        )
    except Exception as e:
        # any unexpected error becomes a 500 in the Swagger UI
        raise HTTPException(status_code=500, detail=str(e)) from e

    resp = ValidationResponse(
        raw_address=result_ctx.get(RAW_ADDRESS),
        parsed_address=result_ctx.get(PARSED_ADDRESS),
        property_type=result_ctx.get(PROPERTY_TYPE),
        validate_status=result_ctx.get(VALIDATE_STATUS),
        validated_at=result_ctx.get(VALIDATED_AT),
        final_context=result_ctx.copy(),
    )
    return resp
