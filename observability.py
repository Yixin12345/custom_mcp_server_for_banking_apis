"""Langfuse observability helpers for MCP tool execution."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class MCPObservability:
    """Optional Langfuse integration for MCP server telemetry."""

    SENSITIVE_KEYS = {"ssn", "password", "secret", "token", "authorization"}

    def __init__(self) -> None:
        self.client: Any | None = None
        self.enabled = os.getenv("LANGFUSE_ENABLED", "true").lower() in {"1", "true", "yes"}
        if not self.enabled:
            return

        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "").strip()
        host = os.getenv("LANGFUSE_HOST", "").strip() or os.getenv("LANGFUSE_BASE_URL", "").strip()

        # Langfuse requires credentials; leave integration disabled if missing.
        if not public_key or not secret_key:
            return

        try:
            from langfuse import Langfuse

            kwargs: dict[str, Any] = {"public_key": public_key, "secret_key": secret_key}
            if host:
                kwargs["host"] = host
            self.client = Langfuse(**kwargs)
        except Exception as exc:
            self.client = None
            logger.warning("Langfuse initialization failed: %s", exc)

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            sanitized: dict[str, Any] = {}
            for key, item in value.items():
                if key.lower() in self.SENSITIVE_KEYS:
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = self._sanitize(item)
            return sanitized
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        return value

    def _trim_output(self, text: str, limit: int = 2500) -> str:
        return text if len(text) <= limit else f"{text[:limit]}... [truncated]"

    async def observe_tool_call(
        self,
        *,
        tool_name: str,
        tool_input: dict[str, Any],
        runner: Callable[[], Awaitable[str]],
    ) -> str:
        """Observe a tool call with Langfuse when configured."""

        if self.client is None:
            return await runner()

        sanitized_input = self._sanitize(tool_input)
        started = time.perf_counter()
        try:
            with self.client.start_as_current_observation(
                name=f"mcp.tool.{tool_name}",
                input=sanitized_input,
                metadata={"component": "mcp_server", "tool": tool_name},
            ):
                result = await runner()
                self.client.create_event(
                    name="mcp.tool.result",
                    output=self._trim_output(result),
                    metadata={
                        "tool": tool_name,
                        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                    },
                )
                return result
        except Exception as exc:
            self.client.create_event(
                name="mcp.tool.error",
                output={"error": str(exc)},
                metadata={
                    "tool": tool_name,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
                level="ERROR",
            )
            raise

    def shutdown(self) -> None:
        """Flush and shutdown Langfuse client."""

        if self.client is None:
            return
        try:
            self.client.shutdown()
        except Exception as exc:
            logger.warning("Langfuse shutdown failed: %s", exc)


telemetry = MCPObservability()
