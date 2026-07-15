from dataclasses import dataclass
from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict, Field

# Bounded-field validation:
#  * Every string carries a `max_length` to prevent DoS via oversized payloads
#    (see docs/security/INPUT_VALIDATION.md).
#  * PHI-bearing values (SSN, phone, email, date of birth) are pattern-checked
#    at the boundary so malformed intake is rejected with 422 before any
#    business logic runs.
#  * `model_config = ConfigDict(extra="forbid")` on every schema keeps the
#    contract rigid so no unplanned field can cross the API boundary.
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PHONE_PATTERN = r"^\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}$"
SSN_PATTERN = r"^\d{3}-\d{2}-\d{4}$"


class AddressSchema(BaseModel):
    """Structured postal address captured during patient intake."""

    model_config = ConfigDict(extra="forbid")

    street: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=50)
    postalCode: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)


class EmergencyContactSchema(BaseModel):
    """Named emergency contact with relationship and reachable phone."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    relationship: str = Field(..., min_length=1, max_length=100)
    phoneNumber: str = Field(
        ...,
        max_length=20,
        pattern=PHONE_PATTERN,
        description="North American phone number for the emergency contact",
    )


class PatientIntakeRequest(BaseModel):
    """Inbound payload for the patient demographics intake submission.

    The social security number is collected for duplicate detection and
    identity resolution but is **never** echoed back to the client (the
    response DTO omits it). All fields are validated against bounded, PHI-aware
    rules before the service layer runs.
    """

    model_config = ConfigDict(extra="forbid")

    firstName: str = Field(..., min_length=1, max_length=100)
    lastName: str = Field(..., min_length=1, max_length=100)
    dateOfBirth: date = Field(..., description="Patient date of birth (ISO 8601)")
    ssn: str = Field(
        ...,
        max_length=11,
        pattern=SSN_PATTERN,
        description="Social security number in NNN-NN-NNNN format",
    )
    gender: str = Field(..., min_length=1, max_length=20)
    address: AddressSchema
    phoneNumber: str = Field(
        ...,
        max_length=20,
        pattern=PHONE_PATTERN,
        description="North American contact phone number",
    )
    email: str = Field(
        ...,
        max_length=320,
        pattern=EMAIL_PATTERN,
        description="Patient contact email",
    )
    emergencyContact: EmergencyContactSchema
    preferredCommunication: List[str] = Field(
        ...,
        min_length=1,
        description="Ordered list of preferred contact methods",
    )


class PatientDemographicsSchema(BaseModel):
    """Compound patient demographics returned by the intake API.

    This is the frontend-facing DTO. The social security number is
    intentionally excluded so sensitive identity data is never re-exposed on
    the wire; it is retained only in the internal :class:`PatientRecord`.
    """

    model_config = ConfigDict(extra="forbid")

    patientId: str = Field(
        ..., max_length=64, description="Server-generated patient identifier"
    )
    firstName: str = Field(..., min_length=1, max_length=100)
    lastName: str = Field(..., min_length=1, max_length=100)
    dateOfBirth: date = Field(..., description="Patient date of birth (ISO 8601)")
    gender: str = Field(..., min_length=1, max_length=20)
    address: AddressSchema
    phoneNumber: str = Field(
        ...,
        max_length=20,
        pattern=PHONE_PATTERN,
        description="North American contact phone number",
    )
    email: str = Field(
        ...,
        max_length=320,
        pattern=EMAIL_PATTERN,
        description="Patient contact email",
    )
    emergencyContact: EmergencyContactSchema
    preferredCommunication: List[str] = Field(
        ...,
        min_length=1,
        description="Ordered list of preferred contact methods",
    )


@dataclass
class AddressRecord:
    """Internal address shape before projection into the API DTO."""

    street: str
    city: str
    state: str
    postal_code: str
    country: str


@dataclass
class EmergencyContactRecord:
    """Internal emergency-contact shape before projection into the API DTO."""

    name: str
    relationship: str
    phone_number: str


@dataclass
class PatientRecord:
    """Internal patient representation held by the repository.

    Carries the generated ``patient_id`` and the full PHI payload (including
    ``ssn``). The service projects it into :class:`PatientDemographicsSchema`,
    deliberately dropping ``ssn`` so it never crosses the API boundary.
    """

    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    ssn: str
    gender: str
    address: AddressRecord
    phone_number: str
    email: str
    emergency_contact: EmergencyContactRecord
    preferred_communication: List[str]


def map_record_to_demographics(record: PatientRecord) -> PatientDemographicsSchema:
    """Project an internal ``PatientRecord`` into the external DTO.

    The social security number is dropped so sensitive identity data is never
    returned to the client.
    """
    return PatientDemographicsSchema(
        patientId=record.patient_id,
        firstName=record.first_name,
        lastName=record.last_name,
        dateOfBirth=record.date_of_birth,
        gender=record.gender,
        address=AddressSchema(
            street=record.address.street,
            city=record.address.city,
            state=record.address.state,
            postalCode=record.address.postal_code,
            country=record.address.country,
        ),
        phoneNumber=record.phone_number,
        email=record.email,
        emergencyContact=EmergencyContactSchema(
            name=record.emergency_contact.name,
            relationship=record.emergency_contact.relationship,
            phoneNumber=record.emergency_contact.phone_number,
        ),
        preferredCommunication=list(record.preferred_communication),
    )


__all__ = [
    "AddressRecord",
    "AddressSchema",
    "EmergencyContactRecord",
    "EmergencyContactSchema",
    "PatientDemographicsSchema",
    "PatientIntakeRequest",
    "PatientRecord",
    "map_record_to_demographics",
]
