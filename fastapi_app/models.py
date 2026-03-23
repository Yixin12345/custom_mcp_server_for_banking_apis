"""Pydantic models for FastAPI application."""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class GenderEnum(str, Enum):
    """Gender enumeration."""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    PREFER_NOT_TO_SAY = "Prefer not to say"


class CustomerRequest(BaseModel):
    """Customer data model for POST request."""
    first_name: str = Field(..., min_length=1, max_length=100, description="Customer's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Customer's last name")
    date_of_birth: date = Field(..., description="Customer's date of birth (YYYY-MM-DD)")
    ssn: Optional[str] = Field(None, pattern=r"^\d{3}-\d{2}-\d{4}$", description="Social Security Number (XXX-XX-XXXX)")
    gender: GenderEnum = Field(..., description="Customer's gender")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-05-15",
                "ssn": "123-45-6789",
                "gender": "Male"
            }
        }


class CustomerResponse(CustomerRequest):
    """Customer response model with additional metadata."""
    customer_id: str = Field(..., description="Unique customer identifier")
    created_at: str = Field(..., description="Timestamp when customer was created")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "customer_id": "cust_123456",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-05-15",
                "ssn": "123-45-6789",
                "gender": "Male",
                "created_at": "2026-02-23T10:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
