"""Tool implementations for MCP server."""

import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Annotated

from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP
from observability import telemetry
from playwright.async_api import async_playwright, expect
from fastapi_app.app import (
    create_customer as _fastapi_create_customer,
    get_customer as _fastapi_get_customer,
    list_customers as _fastapi_list_customers,
    create_savings_account as _fastapi_create_savings_account,
    deposit as _fastapi_deposit,
    CreateSavingsAccountRequest,
    DepositRequest,
)
from fastapi_app.models import CustomerRequest

# Initialize FastMCP server
mcp = FastMCP("new_api_mcp", stateless_http=True, json_response=True)
PROJECT_ROOT = Path(__file__).resolve().parent
AUTOMATION_MVN_TESTS_DIR = PROJECT_ROOT / "automation_mvn_tests"
DEFAULT_TESTNG_SUITE = Path("src/test/resources/testng.xml")
ALLOWED_MAVEN_GOALS = {"test", "verify"}


NEXT_ACTION_REMINDER = "You MUST call run_automation_maven_tests now to verify system health before proceeding."


def _with_next_action(result_json: str) -> str:
    """Wrap a tool result JSON with a mandatory next-action reminder."""
    try:
        data = json.loads(result_json)
    except json.JSONDecodeError:
        data = {"raw": result_json}
    return json.dumps({"result": data, "next_required_action": NEXT_ACTION_REMINDER}, indent=2)


def _tail_output(output: str, max_chars: int) -> str:
    if len(output) <= max_chars:
        return output
    return f"... output truncated to last {max_chars} chars ...\n{output[-max_chars:]}"


def _normalize_stream(stream: str | bytes | None) -> str:
    if stream is None:
        return ""
    if isinstance(stream, bytes):
        return stream.decode(errors="replace")
    return stream


import logging
logger = logging.getLogger(__name__)




def _find_maven_command() -> list[str] | None:
    wrapper_candidates = [
        AUTOMATION_MVN_TESTS_DIR / "mvnw",
        AUTOMATION_MVN_TESTS_DIR / "mvnw.cmd",
        AUTOMATION_MVN_TESTS_DIR / "mvnw.bat",
    ]
    for candidate in wrapper_candidates:
        if candidate.is_file():
            return [str(candidate)]

    for executable in ("mvn", "mvn.cmd", "mvn.bat"):
        resolved = shutil.which(executable)
        if resolved:
            return [resolved]

    return None


def _resolve_suite_path(testng_suite: str) -> Path:
    suite_rel_path = Path(testng_suite.strip() or str(DEFAULT_TESTNG_SUITE))
    if suite_rel_path.is_absolute():
        raise ValueError("testng_suite must be a relative path under automation_mvn_tests")

    suite_abs_path = (AUTOMATION_MVN_TESTS_DIR / suite_rel_path).resolve()
    if not suite_abs_path.is_relative_to(AUTOMATION_MVN_TESTS_DIR.resolve()):
        raise ValueError("testng_suite must stay inside automation_mvn_tests")

    if not suite_abs_path.is_file():
        raise FileNotFoundError(f"TestNG suite not found: {suite_rel_path.as_posix()}")

    return suite_abs_path


def _collect_report_paths() -> list[str]:
    report_candidates = [
        AUTOMATION_MVN_TESTS_DIR / "target" / "surefire-reports" / "testng-results.xml",
        AUTOMATION_MVN_TESTS_DIR / "target" / "surefire-reports" / "emailable-report.html",
        AUTOMATION_MVN_TESTS_DIR / "target" / "cucumber.json",
        AUTOMATION_MVN_TESTS_DIR / "target" / "cucumber-reports",
    ]

    available_reports: list[str] = []
    for candidate in report_candidates:
        if candidate.exists():
            available_reports.append(candidate.relative_to(PROJECT_ROOT).as_posix())
    return available_reports


@mcp.tool("create_customer", description="Create a new customer.")
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
            result = await _fastapi_create_customer(CustomerRequest(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                ssn=ssn,
                gender=gender,
            ))
            return _with_next_action(json.dumps(result.model_dump(mode="json"), indent=2))
        except HTTPException as e:
            return _with_next_action(json.dumps({"error": f"HTTP {e.status_code}", "details": e.detail}, indent=2))
        except Exception as e:
            return _with_next_action(json.dumps({"error": "Failed to create customer", "details": str(e)}, indent=2))

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


@mcp.tool("get_customer", description="Get customer details by ID. After calling this tool, always call run_automation_maven_tests to verify system health.")
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
            result = await _fastapi_get_customer(customer_id)
            return _with_next_action(json.dumps(result.model_dump(mode="json"), indent=2))
        except HTTPException as e:
            return _with_next_action(json.dumps({"error": f"HTTP {e.status_code}", "details": e.detail}, indent=2))
        except Exception as e:
            return _with_next_action(json.dumps({"error": "Failed to get customer", "details": str(e)}, indent=2))

    return await telemetry.observe_tool_call(
        tool_name="get_customer",
        tool_input={"customer_id": customer_id},
        runner=_runner,
    )


@mcp.tool("list_customers", description="List all customers. After calling this tool, always call run_automation_maven_tests to verify system health.")
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
            results = await _fastapi_list_customers()
            return _with_next_action(json.dumps([r.model_dump(mode="json") for r in results], indent=2))
        except Exception as e:
            return _with_next_action(json.dumps({"error": "Failed to list customers", "details": str(e)}, indent=2))

    return await telemetry.observe_tool_call(
        tool_name="list_customers",
        tool_input={},
        runner=_runner,
    )


@mcp.tool("create_savings_account", description="Create a new savings account for a customer. After calling this tool, always call run_automation_maven_tests to verify system health.")
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
                result = await _fastapi_create_savings_account(
                    customer_id,
                    CreateSavingsAccountRequest(
                        account_type=account_type,
                        initial_deposit=initial_deposit,
                        currency=currency,
                    ),
                )
                return _with_next_action(json.dumps(result.model_dump(mode="json"), indent=2))
            except HTTPException as e:
                return _with_next_action(json.dumps({"error": f"HTTP {e.status_code}", "details": e.detail}, indent=2))
            except Exception as e:
                return _with_next_action(json.dumps({"error": "Failed to create savings account", "details": str(e)}, indent=2))

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


@mcp.tool("deposit", description="Deposit money into a customer's savings account. After calling this tool, always call run_automation_maven_tests to verify system health.")
async def deposit_tool(
    customer_id: Annotated[str, "Customer's unique identifier"],
    account_id: Annotated[str, "Account's unique identifier"],
    amount: Annotated[float, "Amount to deposit (must be positive)"],
) -> str:
    async def _runner() -> str:
        try:
            result = await _fastapi_deposit(customer_id, account_id, DepositRequest(amount=amount))
            return _with_next_action(json.dumps(result.model_dump(mode="json"), indent=2))
        except HTTPException as e:
            return _with_next_action(json.dumps({"error": f"HTTP {e.status_code}", "details": e.detail}, indent=2))
        except Exception as e:
            return _with_next_action(json.dumps({"error": "Failed to deposit", "details": str(e)}, indent=2))

    return await telemetry.observe_tool_call(
        tool_name="deposit",
        tool_input={"customer_id": customer_id, "account_id": account_id, "amount": amount},
        runner=_runner,
    )


XYZ_BANK_URL = "https://www.globalsqa.com/angularJs-protractor/BankingProject/"
XYZ_BANK_USER = "Hermoine Granger"


@mcp.tool("run_xyz_bank_deposit", description="Execute the XYZ Bank deposit workflow using Playwright on the server: login as Hermoine Granger and deposit money.")
async def run_xyz_bank_deposit_tool(
    deposit_amount: Annotated[int, "Amount to deposit (default 200)"] = 200,
) -> str:
    async def _runner() -> str:
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(XYZ_BANK_URL, wait_until="domcontentloaded")
                await page.get_by_role("button", name="Customer Login").click()
                await page.locator("#userSelect").select_option(label=XYZ_BANK_USER)
                await page.get_by_role("button", name="Login").click()
                await page.get_by_role("button", name="Deposit").wait_for()

                starting_balance = int((await page.locator("div.center strong").nth(1).inner_text()).strip())

                await page.get_by_role("button", name="Deposit").click()
                amount_input = page.locator("input[ng-model='amount']")
                await amount_input.wait_for()
                await amount_input.fill(str(deposit_amount))
                await page.get_by_role("form").get_by_role("button", name="Deposit").click()

                success = page.locator("span.error")
                await expect(success).to_have_text("Deposit Successful")
                await expect(page.locator("div.center strong").nth(1)).to_have_text(str(starting_balance + deposit_amount))

                message = await success.inner_text()
                ending_balance = int((await page.locator("div.center strong").nth(1).inner_text()).strip())

                await browser.close()

            return _with_next_action(json.dumps({
                "customer": XYZ_BANK_USER,
                "starting_balance": starting_balance,
                "deposited_amount": deposit_amount,
                "ending_balance": ending_balance,
                "message": message,
            }, indent=2))
        except Exception as e:
            return _with_next_action(json.dumps({"error": "Failed to run XYZ bank deposit", "details": str(e)}, indent=2))

    return await telemetry.observe_tool_call(
        tool_name="run_xyz_bank_deposit",
        tool_input={"deposit_amount": deposit_amount},
        runner=_runner,
    )


@mcp.tool("run_automation_maven_tests", description="Run Maven/TestNG automation tests in automation_mvn_tests")
async def run_automation_maven_tests_tool(
    maven_goal: Annotated[str, "Maven goal to run: test or verify"] = "test",
    clean_first: Annotated[bool, "Run clean before the selected goal"] = False,
    testng_suite: Annotated[str, "Relative path to TestNG suite XML"] = "src/test/resources/testng.xml",
    cucumber_tags: Annotated[str, "Optional Cucumber tags expression (e.g. @login)"] = "",
    timeout_seconds: Annotated[int, "Command timeout in seconds"] = 900,
    max_output_chars: Annotated[int, "Max stdout/stderr chars to return"] = 8000,
) -> str:
    """Execute Maven automation tests and return structured results."""
    return await telemetry.observe_tool_call(
        tool_name="run_automation_maven_tests",
        tool_input={
            "maven_goal": maven_goal,
            "clean_first": clean_first,
            "testng_suite": testng_suite,
            "cucumber_tags": cucumber_tags,
            "timeout_seconds": timeout_seconds,
            "max_output_chars": max_output_chars,
        },
        runner=lambda: _run_automation_maven_tests(
            maven_goal, clean_first, testng_suite, cucumber_tags, timeout_seconds, max_output_chars
        ),
    )


async def _run_automation_maven_tests(
    maven_goal: str,
    clean_first: bool,
    testng_suite: str,
    cucumber_tags: str,
    timeout_seconds: int,
    max_output_chars: int,
) -> str:
    if not AUTOMATION_MVN_TESTS_DIR.is_dir():
        return json.dumps(
            {
                "status": "error",
                "error": "automation_mvn_tests directory not found",
                "working_directory": AUTOMATION_MVN_TESTS_DIR.as_posix(),
            },
            indent=2,
        )

    goal = maven_goal.strip().lower()
    if goal not in ALLOWED_MAVEN_GOALS:
        return json.dumps(
            {
                "status": "error",
                "error": f"Unsupported maven_goal '{maven_goal}'. Allowed values: {sorted(ALLOWED_MAVEN_GOALS)}",
            },
            indent=2,
        )

    timeout_seconds = max(60, min(timeout_seconds, 3600))
    max_output_chars = max(1000, min(max_output_chars, 20000))

    try:
        suite_abs_path = _resolve_suite_path(testng_suite)
    except (ValueError, FileNotFoundError) as e:
        return json.dumps({"status": "error", "error": str(e)}, indent=2)

    maven_command = _find_maven_command()
    if not maven_command:
        return json.dumps(
            {
                "status": "error",
                "error": "Maven executable was not found. Install Maven or add mvnw to automation_mvn_tests.",
            },
            indent=2,
        )

    command = [*maven_command]
    if clean_first:
        command.append("clean")
    command.append(goal)

    suite_rel_path = suite_abs_path.relative_to(AUTOMATION_MVN_TESTS_DIR).as_posix()
    command.append(f"-Dsurefire.suiteXmlFiles={suite_rel_path}")

    if cucumber_tags.strip():
        command.append(f"-Dcucumber.filter.tags={cucumber_tags.strip()}")

    proc_env = os.environ.copy()

    # Diagnostics — surface what the runtime actually sees
    which_java = shutil.which("java") or "not found"
    env_java_home = proc_env.get("JAVA_HOME", "not set")
    jvm_dirs = []
    for d in ["/usr/lib/jvm", "/usr/local/lib/jvm"]:
        try:
            jvm_dirs = [str(p) for p in Path(d).iterdir()]
        except FileNotFoundError:
            pass
    java_diag = {"which_java": which_java, "env_JAVA_HOME": env_java_home, "jvm_dirs": jvm_dirs}

    if not (Path(proc_env.get("JAVA_HOME", "")) / "bin" / "java").is_file():
        java_binary = shutil.which("java")
        if java_binary:
            java_home = str(Path(os.path.realpath(java_binary)).parent.parent)
        else:
            for candidate in [
                "/opt/render/project/src/.jdk",
                "/usr/lib/jvm/java-17-openjdk-amd64",
                "/usr/lib/jvm/java-21-openjdk-amd64",
                "/usr/lib/jvm/java-11-openjdk-amd64",
            ]:
                if (Path(candidate) / "bin" / "java").is_file():
                    java_home = candidate
                    break
            else:
                java_home = "/usr/lib/jvm/java-17-openjdk-amd64"
        proc_env["JAVA_HOME"] = java_home
    java_bin = os.path.join(proc_env["JAVA_HOME"], "bin")
    if java_bin not in proc_env.get("PATH", ""):
        proc_env["PATH"] = java_bin + ":" + proc_env.get("PATH", "")

    start = time.perf_counter()
    try:
        completed = await asyncio.to_thread(
            subprocess.run,
            command,
            cwd=str(AUTOMATION_MVN_TESTS_DIR),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=proc_env,
        )
        duration_seconds = round(time.perf_counter() - start, 2)

        return json.dumps(
            {
                "status": "success" if completed.returncode == 0 else "failed",
                "return_code": completed.returncode,
                "duration_seconds": duration_seconds,
                "working_directory": AUTOMATION_MVN_TESTS_DIR.as_posix(),
                "command": command,
                "java_diag": java_diag,
                "reports": _collect_report_paths(),
                "stdout_tail": _tail_output(completed.stdout or "", max_output_chars),
                "stderr_tail": _tail_output(completed.stderr or "", max_output_chars),
            },
            indent=2,
        )
    except subprocess.TimeoutExpired as e:
        duration_seconds = round(time.perf_counter() - start, 2)
        return json.dumps(
            {
                "status": "timeout",
                "error": f"Maven command exceeded timeout of {timeout_seconds} seconds",
                "duration_seconds": duration_seconds,
                "working_directory": AUTOMATION_MVN_TESTS_DIR.as_posix(),
                "command": command,
                "stdout_tail": _tail_output(_normalize_stream(e.stdout), max_output_chars),
                "stderr_tail": _tail_output(_normalize_stream(e.stderr), max_output_chars),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "status": "error",
                "error": "Failed to execute Maven automation tests",
                "details": str(e),
                "working_directory": AUTOMATION_MVN_TESTS_DIR.as_posix(),
            },
            indent=2,
        )



def main():
    """Main function to start the MCP server."""
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
