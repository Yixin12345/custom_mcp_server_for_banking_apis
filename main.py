"""Tool implementations for MCP server."""

import json
import os
from typing import Annotated

import httpx
from mcp.server.fastmcp import FastMCP
from observability import telemetry

# Initialize FastMCP server
mcp = FastMCP("new_api_mcp", stateless_http=True, json_response=True)

base_url: str = os.getenv("BASE_API_URL", f"http://127.0.0.1:{os.getenv('PORT', '8000')}")


@mcp.tool("create_customer", description="Create a new customer")
async def create_customer_tool(
    first_name: Annotated[str, "Customer's first name"],
    last_name: Annotated[str, "Customer's last name"],
    date_of_birth: Annotated[str, "Customer's date of birth (YYYY-MM-DD)"],
    ssn: Annotated[str, "Social Security Number (XXX-XX-XXXX)"],
    gender: Annotated[str, "Customer's gender (Male, Female, Other, Prefer not to say)"],
) -> str:
    """
    Create a new customer in the system via FastAPI endpoint.

    This asynchronous tool creates a new customer record with provided personal information.
    It sends a POST request to the FastAPI backend and returns the response as a JSON string.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.
        date_of_birth: Customer's date of birth in YYYY-MM-DD format.
        ssn: Social Security Number in XXX-XX-XXXX format.
        gender: Customer's gender. Accepted values: Male, Female, Other, Prefer not to say.

    Returns:
        str: JSON string containing the created customer details on success, or error details on failure.
            On success, returns the customer object from the API response.
            On HTTP errors, returns error with status code and response text.
            On other exceptions, returns error message with exception details.

    Raises:
        None: Exceptions are caught and returned as JSON error strings.
    """
    async def _runner() -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/api/v1/customers",
                    json={
                        "first_name": first_name,
                        "last_name": last_name,
                        "date_of_birth": date_of_birth,
                        "ssn": ssn,
                        "gender": gender,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                return json.dumps(response.json(), indent=2)
        except httpx.HTTPStatusError as e:
            return json.dumps({"error": f"HTTP {e.response.status_code}", "details": e.response.text}, indent=2)
        except Exception as e:
            return json.dumps({"error": "Failed to create customer", "details": str(e)}, indent=2)

    return await telemetry.observe_tool_call(
        tool_name="create_customer",
        tool_input={
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": date_of_birth,
            "ssn": ssn,
            "gender": gender,
        },
        runner=_runner,
    )


@mcp.tool("get_customer", description="Get customer details by ID")
async def get_customer_tool(customer_id: str) -> str:
    """
    Retrieve a customer by ID via FastAPI endpoint.

    This asynchronous tool fetches the details of a customer using their unique ID.
    It sends a GET request to the FastAPI backend and returns the response as a JSON string.

    Args:
        customer_id: The unique identifier of the customer.

    Returns:
        str: JSON string containing the customer details on success, or error details on failure.
            On success, returns the customer object from the API response.
            On HTTP errors, returns error with status code and response text.
            On other exceptions, returns error message with exception details.

    Raises:
        None: Exceptions are caught and returned as JSON error strings.
    """
    async def _runner() -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/api/v1/customers/{customer_id}",
                    timeout=10.0,
                )
                response.raise_for_status()
                return json.dumps(response.json(), indent=2)
        except httpx.HTTPStatusError as e:
            return json.dumps({"error": f"HTTP {e.response.status_code}", "details": e.response.text}, indent=2)
        except Exception as e:
            return json.dumps({"error": "Failed to get customer", "details": str(e)}, indent=2)

    return await telemetry.observe_tool_call(
        tool_name="get_customer",
        tool_input={"customer_id": customer_id},
        runner=_runner,
    )


@mcp.tool("list_customers", description="List all customers")
async def list_customers_tool() -> str:
    """
    List all customers via FastAPI endpoint.

    This asynchronous tool fetches the details of all customers.
    It sends a GET request to the FastAPI backend and returns the response as a JSON string.

    Returns:
        str: JSON string containing the list of customers on success, or error details on failure.
            On success, returns the list of customer objects from the API response.
            On HTTP errors, returns error with status code and response text.
            On other exceptions, returns error message with exception details.

    Raises:
        None: Exceptions are caught and returned as JSON error strings.
    """
    async def _runner() -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/api/v1/customers",
                    timeout=10.0,
                )
                response.raise_for_status()
                return json.dumps(response.json(), indent=2)
        except httpx.HTTPStatusError as e:
            return json.dumps({"error": f"HTTP {e.response.status_code}", "details": e.response.text}, indent=2)
        except Exception as e:
            return json.dumps({"error": "Failed to list customers", "details": str(e)}, indent=2)

    return await telemetry.observe_tool_call(
        tool_name="list_customers",
        tool_input={},
        runner=_runner,
    )


@mcp.tool("create_savings_account", description="Create a new savings account for a customer")
async def create_savings_account_tool(
        customer_id: Annotated[str, "Customer's unique identifier"],
        initial_deposit: Annotated[float, "Initial deposit amount"],
        account_type: Annotated[str, "Account type (default is SAVINGS)"] = "SAVINGS",
        currency: Annotated[str, "Currency for the account (default is USD)"] = "USD",
    ) -> str:
        """
        Create a new savings account for a customer via FastAPI endpoint.

        This asynchronous tool creates a new savings account for an existing customer.
        It sends a POST request to the FastAPI backend and returns the response as a JSON string.

        Args:
            customer_id: The unique identifier of the customer.
            account_type: Set to 'SAVINGS' by default for this tool.
            initial_deposit: Initial deposit amount.
            currency: Currency for the account (default is USD).

        Returns:
            str: JSON string containing the created account details on success, or error details on failure.
                On success, returns the account object from the API response.
                On HTTP errors, returns error with status code and response text.
                On other exceptions, returns error message with exception details.

        Raises:
            None: Exceptions are caught and returned as JSON error strings.
        """
        async def _runner() -> str:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{base_url}/api/v1/customers/{customer_id}/accounts",
                        json={
                            "account_type": account_type,
                            "initial_deposit": initial_deposit,
                            "currency": currency
                        },
                        timeout=10.0,
                    )
                    response.raise_for_status()
                    return json.dumps(response.json(), indent=2)
            except httpx.HTTPStatusError as e:
                return json.dumps({"error": f"HTTP {e.response.status_code}", "details": e.response.text}, indent=2)
            except Exception as e:
                return json.dumps({"error": "Failed to create savings account", "details": str(e)}, indent=2)

        return await telemetry.observe_tool_call(
            tool_name="create_savings_account",
            tool_input={
                "customer_id": customer_id,
                "initial_deposit": initial_deposit,
                "account_type": account_type,
                "currency": currency,
            },
            runner=_runner,
        )



def main():
    """Main function to start the MCP server."""
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
