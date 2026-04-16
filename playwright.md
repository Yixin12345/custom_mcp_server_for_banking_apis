# Playwright Implementation — HTTP Transport

This document describes how the Playwright-based deposit workflow works in the HTTP version of this project.

---

## HTTP Transport — Architecture

This project is an **HTTP MCP server** deployed on Render. There is no `@playwright/mcp` sidecar available — Playwright runs directly inside the MCP server process.

```
MCP Client (Claude.ai / API)
  └── HTTP → custom-mcp-server-for-banking-apis.onrender.com/mcp/
                └── run_xyz_bank_deposit tool
                      └── async_playwright → Chromium (headless, server-side)
```

---

## Repository Layout (relevant files)

```
main.py                                          # MCP server (FastMCP over HTTP, stateless)
asgi.py                                          # ASGI entrypoint (Starlette)
fastapi_app/
  app.py                                         # FastAPI REST backend (runs in same process)
  models.py                                      # Pydantic request/response schemas
  config.py                                      # Settings
scripts/
  xyz_bank_deposit.py                            # Playwright deposit reference spec (sync)
automation_mvn_tests/                            # Java/Selenium/Cucumber tests
.github/prompts/xyz-deposit-txn.md              # Prompt that triggers the deposit workflow
observability.py                                 # Langfuse telemetry
```

---

## Deposit Workflow

### How it is triggered

The user (or Claude) invokes the `/xyz-deposit-txn` prompt, which loads `.github/prompts/xyz-deposit-txn.md`:

```markdown
1. Call `run_xyz_bank_deposit` with default parameters (deposit_amount: 200).
   The server runs Playwright internally against the XYZ Bank demo site and returns the result.
```

### What the server does (step by step)

`run_xyz_bank_deposit` in `main.py` launches Chromium headless and executes:

```
1. page.goto("https://www.globalsqa.com/angularJs-protractor/BankingProject/")
2. click "Customer Login" button
3. select_option("#userSelect", label="Hermoine Granger")
4. click "Login" button
5. wait for "Deposit" button → read starting_balance from div.center strong nth(1)
6. click "Deposit" button
7. fill input[ng-model='amount'] with deposit_amount
8. click form's "Deposit" button
9. expect(span.error).to_have_text("Deposit Successful")        ← asserts success
10. expect(div.center strong nth(1)).to_have_text(starting + amount)  ← asserts balance
11. read ending_balance
```

Returns structured JSON:
```json
{
  "customer": "Hermoine Granger",
  "starting_balance": 1000,
  "deposited_amount": 200,
  "ending_balance": 1200,
  "message": "Deposit Successful"
}
```

### Reference spec

`scripts/xyz_bank_deposit.py` is the **sync Playwright reference spec** — same selectors and logic, written with `sync_playwright` for readability. It is not executed by the server; it exists so developers can read it alongside the async implementation in `main.py`.

---

## Key Differences from stdio Version

| Aspect | stdio | HTTP |
|---|---|---|
| Browser control | `@playwright/mcp` sidecar; Claude calls tools step-by-step | `async_playwright` runs inside server process |
| `run_xyz_bank_deposit` tool | Commented out (not needed) | Active — encapsulates all browser steps |
| Assertions | `expect()` calls in `xyz_bank_deposit.py` (sync) | `await expect()` in `main.py` (async) |
| Observability | None | Langfuse via `telemetry.observe_tool_call()` |
| Result format | JSON returned by tool | JSON wrapped with `_with_next_action()` |

---

## MCP Server Registration

`mcp.json` registers the HTTP server with a Bearer token:

```json
{
  "servers": {
    "new_api_mcp": {
      "type": "http",
      "url": "https://custom-mcp-server-for-banking-apis.onrender.com/mcp/",
      "headers": { "Authorization": "Bearer <token>" }
    }
  }
}
```
