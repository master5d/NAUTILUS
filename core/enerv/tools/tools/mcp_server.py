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
        Tool(
            name="facet_ingest",
            description="Ingest a document file (Markdown/Text) into the Nautilus Knowledge Graph (performs normalizations, vector embeddings, and Neo4j similar-to link mapping)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file to ingest"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force re-ingestion even if content hash matches",
                        "default": False
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="facet_search",
            description="Perform a semantic vector similarity search against the Nautilus Knowledge Graph, returning top matching documents and snippets",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term or query phrase"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of top results to return",
                        "default": 5
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum similarity score threshold",
                        "default": 0.6
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="facet_graphrag",
            description="Perform a GraphRAG synthesis to answer a question using relevant Knowledge Graph document and relationship context",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to synthesize an answer for"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of anchor nodes to query",
                        "default": 5
                    }
                },
                "required": ["question"]
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
        elif name == "facet_ingest":
            cmd = ["facet", "ingest", arguments["file_path"]]
            if arguments.get("force"):
                cmd.append("--force")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return ToolResult(
                content=[TextContent(type="text", text=result.stdout or "Document successfully ingested into the knowledge graph.")],
                isError=False
            )
        elif name == "facet_search":
            cmd = ["facet", "search", arguments["query"]]
            if "top_k" in arguments:
                cmd.extend(["--top-k", str(arguments["top_k"])])
            if "min_score" in arguments:
                cmd.extend(["--min-score", str(arguments["min_score"])])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return ToolResult(
                content=[TextContent(type="text", text=result.stdout)],
                isError=False
            )
        elif name == "facet_graphrag":
            cmd = ["facet", "graphrag", arguments["question"]]
            if "top_k" in arguments:
                cmd.extend(["--top-k", str(arguments["top_k"])])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return ToolResult(
                content=[TextContent(type="text", text=result.stdout)],
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
