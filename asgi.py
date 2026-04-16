"""ASGI entrypoint for deploying FastAPI + MCP streamable HTTP on Render."""

from contextlib import asynccontextmanager
import hmac
import os

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse
from starlette.routing import Route
from starlette.routing import Mount

from fastapi_app.app import app as fastapi_app
from main import mcp
from observability import telemetry

# Mounted at /mcp, so MCP endpoint should be the mount root.
mcp.settings.streamable_http_path = "/"
if os.getenv("MCP_DISABLE_DNS_REBINDING_PROTECTION", "true").lower() in {"1", "true", "yes"}:
    mcp.settings.transport_security.enable_dns_rebinding_protection = False

MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "").strip()


class MCPAuthMiddleware(BaseHTTPMiddleware):
    """Enforce Bearer token auth for MCP routes when MCP_AUTH_TOKEN is configured."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp") and MCP_AUTH_TOKEN:
            auth_header = request.headers.get("authorization", "")
            token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""
            if not token or not hmac.compare_digest(token, MCP_AUTH_TOKEN):
                return JSONResponse(status_code=401, content={"error": "Unauthorized"})
        return await call_next(request)


@asynccontextmanager
async def lifespan(_: Starlette):
    async with mcp.session_manager.run():
        try:
            yield
        finally:
            telemetry.shutdown()


async def redirect_mcp(_):
    return RedirectResponse(url="/mcp/", status_code=307)


async def oauth_not_supported(_):
    """Return a well-formed OAuth error so the MCP SDK discovery doesn't crash with ZodError."""
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "error_description": "OAuth not supported; use static Bearer token."},
    )


app = Starlette(
    routes=[
        Route("/.well-known/oauth-authorization-server", endpoint=oauth_not_supported),
        Route("/.well-known/oauth-protected-resource", endpoint=oauth_not_supported),
        Route("/mcp", endpoint=redirect_mcp, methods=["GET", "POST", "OPTIONS"]),
        Mount("/mcp", app=mcp.streamable_http_app()),
        Mount("/", app=fastapi_app),
    ],
    lifespan=lifespan,
)
app.add_middleware(MCPAuthMiddleware)
