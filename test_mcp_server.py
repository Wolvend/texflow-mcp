#!/usr/bin/env python3
"""Test the MCP server is working properly."""

import subprocess
import json
import sys
import time

def test_mcp_server():
    """Test that the MCP server starts and responds to initialization."""
    print("Starting TeXFlow MCP server...")
    
    # Start the server
    process = subprocess.Popen(
        ["uv", "run", "python", "texflow_unified.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send initialization request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "0.1.0",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        # Send request
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Wait for response (with timeout)
        process.stdout.flush()
        response_line = process.stdout.readline()
        
        if response_line:
            response = json.loads(response_line)
            print("Server responded successfully!")
            print(f"Response: {json.dumps(response, indent=2)}")
            
            # Check if response contains expected fields
            if "result" in response and "capabilities" in response["result"]:
                tools = response["result"]["capabilities"].get("tools", {})
                resources = response["result"]["capabilities"].get("resources", {})
                print(f"\nServer capabilities:")
                print(f"- Tools: {len(tools)} available")
                print(f"- Resources: {len(resources)} available")
                
                if tools:
                    print("\nAvailable tools:")
                    for tool_name in sorted(tools.keys()):
                        print(f"  - {tool_name}")
                
                if resources:
                    print("\nAvailable resources:")
                    for resource_name in sorted(resources.keys()):
                        print(f"  - {resource_name}")
            
            return True
        else:
            print("No response from server")
            stderr = process.stderr.read()
            if stderr:
                print(f"Server error: {stderr}")
            return False
            
    except Exception as e:
        print(f"Error testing server: {e}")
        return False
    finally:
        # Clean up
        process.terminate()
        process.wait()

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)