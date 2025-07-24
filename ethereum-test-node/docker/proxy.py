#!/usr/bin/env python3
"""
Simple RPC Proxy for Sepolia
Redirects requests to external Sepolia RPC endpoint
"""

import json
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# External Sepolia RPC endpoint
EXTERNAL_RPC_URL = os.getenv("EXTERNAL_RPC_URL", "https://sepolia.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161")

class RPCProxyHandler(BaseHTTPRequestHandler):
    """HTTP request handler for RPC proxy"""
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse JSON request
            request_data = json.loads(post_data.decode('utf-8'))
            logger.info(f"Received request: {request_data.get('method', 'unknown')}")
            
            # Forward request to external RPC
            response = requests.post(
                EXTERNAL_RPC_URL,
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            # Return response
            self.send_response(response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            self.wfile.write(response.content)
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get('id', 1),
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom logging"""
        logger.info(f"{self.address_string()} - {format % args}")

def main():
    """Main function"""
    port = int(os.getenv("PROXY_PORT", "8545"))
    server_address = ('', port)
    
    logger.info(f"Starting RPC proxy on port {port}")
    logger.info(f"Forwarding to: {EXTERNAL_RPC_URL}")
    
    httpd = HTTPServer(server_address, RPCProxyHandler)
    logger.info(f"Server started on port {port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        httpd.shutdown()

if __name__ == "__main__":
    main() 