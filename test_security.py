#!/usr/bin/env python3
"""Test security features of TeXFlow server"""

import json
import subprocess
import sys
import time

def send_request(proc, request):
    """Send a request and get response"""
    proc.stdin.write(json.dumps(request) + '\n')
    proc.stdin.flush()
    response = proc.stdout.readline()
    return json.loads(response) if response else None

def test_security():
    """Test security features"""
    
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
        # Initialize
        init_req = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": False}},
                "clientInfo": {"name": "security-test", "version": "1.0.0"}
            },
            "id": 1
        }
        
        result = send_request(proc, init_req)
        print("✓ Server initialized")
        
        # Send initialized notification
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + '\n')
        proc.stdin.flush()
        time.sleep(0.1)
        
        # Test 1: Try to access file outside workspace
        test1 = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "document",
                "arguments": {
                    "action": "read",
                    "path": "../../../etc/passwd"
                }
            },
            "id": 2
        }
        
        result = send_request(proc, test1)
        if "error" in result or "outside workspace" in str(result):
            print("✓ Path traversal attack blocked")
        else:
            print("✗ Path traversal not blocked!")
            
        # Test 2: Try to create file with dangerous extension
        test2 = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "document",
                "arguments": {
                    "action": "create",
                    "path": "test.sh",
                    "content": "#!/bin/bash\necho 'pwned'"
                }
            },
            "id": 3
        }
        
        result = send_request(proc, test2)
        if "error" in result or "not allowed" in str(result):
            print("✓ Dangerous file extension blocked")
        else:
            print("✗ Dangerous file extension not blocked!")
            
        # Test 3: Try to send oversized content
        # Now testing against 100MB limit
        large_content = "A" * (101 * 1024 * 1024)  # 101MB - over the limit
        print(f"  Testing with content size: {len(large_content) // (1024*1024)}MB")
        test3 = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "document",
                "arguments": {
                    "action": "create",
                    "path": "large.tex",
                    "content": large_content
                }
            },
            "id": 4
        }
        
        result = send_request(proc, test3)
        if "error" in result or "exceeds maximum" in str(result):
            print("✓ Oversized content blocked (>100MB)")
        else:
            print("✗ Oversized content not blocked!")
            
        # Test 4: Valid operation
        test4 = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "project",
                "arguments": {
                    "action": "create",
                    "name": "test-project"
                }
            },
            "id": 5
        }
        
        result = send_request(proc, test4)
        if "error" not in result:
            print("✓ Valid operation succeeded")
        else:
            print("✗ Valid operation failed!")
            
        # Test 5: Valid PDF-sized content
        test5 = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "document",
                "arguments": {
                    "action": "create",
                    "path": "large-doc.tex",
                    "content": "\\documentclass{article}\n" + ("This is a large document. " * 10000)  # About 250KB
                }
            },
            "id": 6
        }
        
        result = send_request(proc, test5)
        if "error" not in result:
            print("✓ Large document (250KB) accepted")
        else:
            print("✗ Large document rejected!")
            
        # Check log file
        time.sleep(1)
        try:
            with open('/tmp/texflow_security.log', 'r') as f:
                logs = f.read()
                if "Tool call:" in logs:
                    print("✓ Security logging working")
                    print(f"  Log entries: {logs.count('Tool call:')}")
                else:
                    print("✗ Security logging not working!")
                    print(f"  Log size: {len(logs)} bytes")
        except Exception as e:
            print(f"✗ Could not read log: {e}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        proc.terminate()
        proc.wait()
        
        # Show stderr output
        stderr = proc.stderr.read()
        if stderr:
            print("\nServer stderr output:")
            print(stderr[:500])  # First 500 chars

if __name__ == "__main__":
    test_security()