"""
Integration tests for the /validation/ FastAPI endpoint.

Covers success, input validation failure, and internal server error scenarios.
"""

from fastapi.testclient import TestClient

from address_validator.constants import (
    COUNTRY_CODE_SINGAPORE,
    PARSED_ADDRESS,
    RAW_ADDRESS,
    VALIDATE_STATUS,
    VALIDATED_AT,
)
from address_validator.validation import AddressValidationFlow, ValidateStatus
from app.main import app

client = TestClient(app)


def test_validate_address_success():
    """Should return 200 and a valid response when address is well-formed."""
    payload = {
        "address": "288E Jurong East Street 21, #12-34, Singapore 605288",
        "country": COUNTRY_CODE_SINGAPORE,
    }

    response = client.post("/validation/", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data[RAW_ADDRESS] == payload["address"]
    assert isinstance(data[PARSED_ADDRESS], dict)
    assert isinstance(data["final_context"], dict)
    assert data[VALIDATE_STATUS] == ValidateStatus.VALID.value
    assert VALIDATED_AT in data  # can be None if not used yet


def test_validate_address_missing_address_field():
    """Should return 422 if required 'address' field is missing."""
    payload = {"country": COUNTRY_CODE_SINGAPORE}

    response = client.post("/validation/", json=payload)
    assert response.status_code == 422  # Missing required field


def test_validate_address_internal_error(monkeypatch):
    """Should return 500 and error detail if validation raises an exception."""

    def mock_validate(*args, **kwargs):
        raise RuntimeError("Simulated error")

    monkeypatch.setattr(AddressValidationFlow, "validate", mock_validate)

    payload = {
        "address": "26 Ridout Road, Singapore 248420",
        "country": COUNTRY_CODE_SINGAPORE,
    }

    response = client.post("/validation/", json=payload)
    assert response.status_code == 500
    assert response.json()["detail"] == "Simulated error"
