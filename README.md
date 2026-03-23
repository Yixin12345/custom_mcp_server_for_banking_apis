# new_api_mcp

`new_api_mcp` is being established as an **MCP server layer** that exposes selected API capabilities as safe, structured tools for AI clients.

## Deploy On Render (Streamable MCP)

This repository is ready to deploy as one public web service that exposes:

- MCP endpoint: `/mcp/`
- FastAPI health/API endpoints: `/health`, `/api/v1/...`

### 1. Push to GitHub

Push this project to a GitHub repository.

### 2. Create the Render service

1. In Render, choose **New +** -> **Blueprint**.
2. Select your GitHub repo.
3. Render will detect `render.yaml` and create the service.

### 3. Confirm deployment

- Health: `https://<your-service-name>.onrender.com/health`
- MCP: `https://<your-service-name>.onrender.com/mcp/`

### 4. MCP client config

Use `mcp.json` with your real Render URL:

```json
{
  "servers": {
    "new_api_mcp": {
      "url": "https://<your-service-name>.onrender.com/mcp/"
    }
  }
}
```

### 5. Add MCP auth (Bearer token)

Set an environment variable on your server:

- `MCP_AUTH_TOKEN=<strong-random-secret>`

When `MCP_AUTH_TOKEN` is set, requests to `/mcp` and `/mcp/` must include:

- `Authorization: Bearer <strong-random-secret>`

Example client config:

```json
{
  "servers": {
    "new_api_mcp": {
      "url": "https://<your-service-name>.onrender.com/mcp/",
      "type": "http",
      "headers": {
        "Authorization": "Bearer <strong-random-secret>"
      }
    }
  }
}
```

## Purpose

The project is intended to provide:

- A clear MCP interface over existing/new APIs
- Strong input/output validation
- Reliable error handling and observability
- A foundation for secure, scalable tool execution

## What this project is establishing

1. **MCP-first architecture** for tool-based integrations  
2. **Reusable API adapters** that can be mapped to tools/resources  
3. **Operational standards** (logging, retries, timeout strategy, auth handling)  
4. **Documentation and conventions** for contributors

## Scope (Phase 1)

- [ ] Project scaffold and configuration
- [ ] MCP server bootstrap
- [ ] First set of API-backed tools
- [ ] Centralized config/env management
- [ ] Developer documentation

## Automation tool: Maven tests

The MCP server now exposes a tool named `run_automation_maven_tests` that runs the Maven-based suite in `automation_mvn_tests`.

Tool parameters:

- `maven_goal`: `test` or `verify` (default `test`)
- `clean_first`: run `clean` before the goal (default `false`)
- `testng_suite`: relative suite path (default `src/test/resources/testng.xml`)
- `cucumber_tags`: optional tag filter (example: `@login`)
- `timeout_seconds`: run timeout in seconds
- `max_output_chars`: max stdout/stderr returned

Example Copilot prompts:

- "Use `new_api_mcp` and run `run_automation_maven_tests` with defaults."
- "Use `new_api_mcp` and run `run_automation_maven_tests` with `clean_first=true` and `cucumber_tags=@login`."

Runtime prerequisites on the MCP server host:

- Java (matching the project target, currently 21)
- Maven (`mvn`) or Maven Wrapper (`mvnw`) available
- Browser + WebDriver needed by Selenium tests (Chrome/Chromedriver for current step definitions)
