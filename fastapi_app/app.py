"""FastAPI application with customer management endpoints."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi_app.config import settings
from fastapi_app.models import CustomerRequest, CustomerResponse, ErrorResponse

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI REST API for customer management with MCP integration",
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# In-memory storage for customers and accounts (for demo purposes)
customer_store: dict[str, dict] = {}
mock_accounts_db = {}

class CreateSavingsAccountRequest(BaseModel):
    account_type: str = "SAVINGS"
    initial_deposit: float = Field(..., example=100.00)
    currency: str = Field("USD", example="USD")

    @validator("initial_deposit")
    def validate_deposit(cls, v):
        if v < 0:
            raise ValueError("Initial deposit cannot be negative")
        return v


class CreateSavingsAccountResponse(BaseModel):
    account_id: str
    account_number: str
    message: str


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


@app.post(
    f"{settings.api_prefix}/customers",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer",
    tags=["Customers"],
)
async def create_customer(customer: CustomerRequest) -> CustomerResponse:
    """
    Create a new customer with the provided information.
    
    Args:
        customer: Customer data containing:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - date_of_birth: Customer's date of birth (YYYY-MM-DD)
            - ssn: Social Security Number (XXX-XX-XXXX format)
            - gender: Customer's gender
    
    Returns:
        CustomerResponse: Created customer with ID and timestamp
        
    Raises:
        HTTPException: If validation fails or SSN already exists
    """
    try:
        # Generate unique customer ID
        customer_id = f"cust_{uuid.uuid4().hex[:12]}"
        
        # Check if SSN already exists (only if SSN is provided)
        if customer.ssn:
            for stored_customer in customer_store.values():
                if stored_customer["ssn"] == customer.ssn:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Customer with SSN {customer.ssn} already exists"
                    )
        
        # Create response
        response = CustomerResponse(
            customer_id=customer_id,
            first_name=customer.first_name,
            last_name=customer.last_name,
            date_of_birth=customer.date_of_birth,
            ssn=customer.ssn,
            gender=customer.gender,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        
        # Store customer
        customer_store[customer_id] = response.model_dump()
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create customer: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/customers/{{customer_id}}",
    response_model=CustomerResponse,
    tags=["Customers"],
)
async def get_customer(customer_id: str) -> CustomerResponse:
    """
    Retrieve a customer by ID.
    
    Args:
        customer_id: The customer's unique identifier
        
    Returns:
        CustomerResponse: The customer data
        
    Raises:
        HTTPException: If customer not found
    """
    if customer_id not in customer_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    
    customer_data = customer_store[customer_id]
    return CustomerResponse(**customer_data)


@app.get(
    f"{settings.api_prefix}/customers",
    response_model=list[CustomerResponse],
    tags=["Customers"],
)
async def list_customers() -> list[CustomerResponse]:
    """
    List all customers.
    
    Returns:
        List of all customers
    """
    return [CustomerResponse(**customer) for customer in customer_store.values()]


@app.post(
    f"{settings.api_prefix}/customers/{{customer_id}}/accounts",
    response_model=CreateSavingsAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new savings account",
    tags=["Accounts"],
)
async def create_savings_account(customer_id: str, payload: CreateSavingsAccountRequest) -> CreateSavingsAccountResponse:
    """
    Create a new savings account for a customer.
    This function validates that the customer does not already have an existing savings account,
    generates a unique account ID and account number, and stores the account information in the mock database.
    Args:
        customer_id: Customer's unique identifier
        payload (CreateSavingsAccountRequest): Request object containing account_type,
                                               initial_deposit, and currency details.
    Returns:
        CreateSavingsAccountResponse: Response object containing the newly created account_id,
                                     account_number, and a success message.
    Raises:
        HTTPException: If the customer not found or already has an existing savings account.
    Example:
        >>> request = CreateSavingsAccountRequest(
        ...     customer_id="cust_123",
        ...     account_type="SAVINGS",
        ...     initial_deposit=1000.0,
        ...     currency="USD"
        ... )
        >>> response = create_savings_account("cust_123", request)
        >>> print(response.account_number)
        'SV-A1B2C3D4'
    """
    # Verify customer exists
    if customer_id not in customer_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    
    # Check if customer already has a savings account (simple rule)
    for acct in mock_accounts_db.values():
        if acct["customer_id"] == customer_id and acct["account_type"] == "SAVINGS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer already has a savings account"
            )

    # Generate account ID and account number
    account_id = str(uuid.uuid4())
    account_number = f"SV-{str(uuid.uuid4())[:8].upper()}"

    # Store in mock DB
    mock_accounts_db[account_id] = {
        "customer_id": customer_id,
        "account_type": payload.account_type,
        "initial_deposit": payload.initial_deposit,
        "currency": payload.currency,
        "account_number": account_number
    }

    return CreateSavingsAccountResponse(
        account_id=account_id,
        account_number=account_number,
        message="Savings account created successfully"
    )



@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Generic exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "details": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
