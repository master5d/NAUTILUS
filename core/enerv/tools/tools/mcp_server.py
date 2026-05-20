#!/usr/bin/env python3
"""MCP server for the Facet indexing system."""

import json
import subprocess
import sys
from typing import Any

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ToolResult,
)

server = Server("facet-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available facet tools."""
    return [
        Tool(
            name="facet_current_info",
            description="Show metadata and children for a folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Path to the folder to inspect"
                    }
                },
                "required": ["folder_path"]
            }
        ),
        Tool(
            name="facet_index",
            description="Rebuild aggregated index (with debounce, unless forced)",
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "Force rebuild without debounce",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="facet_audit",
            description="Audit current state without making changes (always safe)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="facet_init",
            description="Initialize .facets directory for a root",
            inputSchema={
                "type": "object",
                "properties": {
                    "root_path": {
                        "type": "string",
                        "description": "Path to the root directory to initialize"
                    }
                },
                "required": ["root_path"]
            }
        ),
        Tool(
            name="facet_validate",
            description="Validate all meta.json files against schema",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> ToolResult:
    """Execute a facet CLI tool."""
    try:
        if name == "facet_current_info":
            result = subprocess.run(
                ["facet", "current-info", arguments["folder_path"]],
                capture_output=True,
                text=True,
                check=True
            )
            return ToolResult(
                content=[TextContent(type="text", text=result.stdout)],
                isError=False
            )
        elif name == "facet_index":
            cmd = ["facet", "index"]
            if arguments.get("force"):
                cmd.append("--force")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return ToolResult(
                content=[TextContent(type="text", text=result.stdout or "Index rebuilt successfully")],
                isError=False
            )
        elif name == "facet_audit":
            result = subprocess.run(
                ["facet", "audit"],
                capture_output=True,
                text=True,
                check=True
            )
            return ToolResult(
                content=[TextContent(type="text", text=result.stdout)],
                isError=False
            )
        elif name == "facet_init":
            result = subprocess.run(
                ["facet", "init", arguments["root_path"]],
                capture_output=True,
                text=True,
                check=True
            )
            return ToolResult(
                content=[TextContent(type="text", text=result.stdout or "Initialized successfully")],
                isError=False
            )
        elif name == "facet_validate":
            result = subprocess.run(
                ["facet", "validate"],
                capture_output=True,
                text=True,
                check=True
            )
            return ToolResult(
                content=[TextContent(type="text", text=result.stdout or "All files valid")],
                isError=False
            )
        else:
            return ToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True
            )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or e.stdout or f"Exit code {e.returncode}"

        # Provide helpful suggestions based on error
        suggestion = ""
        if "No facet root found" in error_msg:
            suggestion = "\n💡 Try: Set FACET_ROOT=/path/to/root or cd into a root directory"
        elif ".facets not found" in error_msg:
            suggestion = "\n💡 Try: facet init /path/to/root"
        elif "Invalid JSON" in error_msg or "validation" in error_msg.lower():
            suggestion = "\n💡 Check that .facets/meta.json has correct schema (use facet validate)"

        full_message = f"❌ Command failed:\n{error_msg}{suggestion}"
        return ToolResult(
            content=[TextContent(type="text", text=full_message)],
            isError=True
        )
    except Exception as e:
        return ToolResult(
            content=[TextContent(type="text", text=f"❌ Unexpected error: {str(e)}")],
            isError=True
        )


def main():
    """Entry point for the MCP server."""
    import anyio
    anyio.run(server.run_async)


if __name__ == "__main__":
    main()
