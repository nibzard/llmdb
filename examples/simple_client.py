"""Simple client example for the MCP server."""

import requests

resp = requests.get("http://localhost:8000/ping")
print(resp.json())

