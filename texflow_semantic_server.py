#!/usr/bin/env python3
"""
TeXFlow Semantic MCP Server

This is the semantic layer entry point that exposes 4 operations instead of 27+ tools.
"""

import asyncio
import json
import sys
from typing import Any, Dict

from mcp import Router, Server
from mcp.types import Tool, TextContent

# Import the existing TeXFlow with all its functions
import texflow as original_texflow

# Import semantic layer
from src.texflow_semantic import create_semantic_tools, TeXFlowSemantic


async def main():
    """Run the semantic TeXFlow MCP server."""
    # Create server instance
    server = Server("texflow")
    router = Router()
    
    # Create TeXFlow instance (has all original methods)
    texflow_instance = original_texflow.TeXFlow()
    
    # Get semantic tools
    semantic_tools = create_semantic_tools(texflow_instance)
    
    # Register semantic tools
    for tool_def in semantic_tools:
        # Create Tool object for MCP
        tool = Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            inputSchema=tool_def["input_schema"]
        )
        
        # Register handler
        async def create_handler(tool_def):
            async def handler(arguments: dict) -> TextContent:
                try:
                    # Call the sync handler from semantic layer
                    result = tool_def["handler"](arguments)
                    
                    # Convert result to JSON string
                    if isinstance(result, dict):
                        content = json.dumps(result, indent=2)
                    else:
                        content = str(result)
                    
                    return TextContent(type="text", text=content)
                except Exception as e:
                    error_result = {"error": str(e), "type": "execution_error"}
                    return TextContent(type="text", text=json.dumps(error_result, indent=2))
            
            return handler
        
        # Register tool and handler
        server.add_tool(tool, create_handler(tool_def))
    
    # Optional: Keep a few system tools for compatibility
    @server.tool(
        name="list_printers",
        description="List all available CUPS printers"
    )
    async def list_printers(arguments: dict) -> TextContent:
        result = texflow_instance.list_printers()
        return TextContent(type="text", text=result)
    
    # Run server
    async with server:
        await server.run()


if __name__ == "__main__":
    asyncio.run(main())