#!/usr/bin/env python3
"""Test script for TeXFlow MCP server"""

import json
import subprocess
import sys

def test_server():
    """Test the TeXFlow server with basic MCP protocol messages."""
    
    # Start the server process
    cmd = [
        "/home/wolvend/miniconda3/envs/texflow/bin/python",
        "texflow_server_fixed.py",
        "/tmp/test_texflow"
    ]
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Send initialize request
        initialize_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": False
                    }
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        
        proc.stdin.write(json.dumps(initialize_request) + '\n')
        proc.stdin.flush()
        
        # Read response
        response = proc.stdout.readline()
        if response:
            print("Initialize response:", response.strip())
            
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            proc.stdin.write(json.dumps(initialized_notification) + '\n')
            proc.stdin.flush()
            
            # List tools
            list_tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 2
            }
            proc.stdin.write(json.dumps(list_tools_request) + '\n')
            proc.stdin.flush()
            
            # Read response
            response = proc.stdout.readline()
            if response:
                print("List tools response:", response.strip())
                result = json.loads(response)
                if "result" in result and "tools" in result["result"]:
                    print(f"Found {len(result['result']['tools'])} tools")
                    for tool in result['result']['tools']:
                        print(f"  - {tool['name']}: {tool['description']}")
        else:
            print("No response from server")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        proc.terminate()
        proc.wait()
        
        # Check for any stderr output
        stderr = proc.stderr.read()
        if stderr:
            print("Server errors:", stderr)

if __name__ == "__main__":
    test_server()