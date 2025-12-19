"""
MCP (Model Context Protocol) Server for Swiss Ephemeris Engine.

This allows AI agents (Claude, Gemini, ChatGPT) to invoke ephemeris calculations
as a tool, making Proveniq the canonical source of astrological truth.
"""

import json
import sys
import asyncio
from typing import Any

# MCP Server implementation using stdio transport
class MCPServer:
    """
    MCP Server exposing TrueArk Ephemeris as AI-callable tools.
    
    Tools:
    - calculate_chart: Compute natal chart for given datetime/location
    - store_chart: Compute and persist chart to database
    - get_chart: Retrieve stored chart by ID
    - list_charts: List stored charts with filtering
    """
    
    def __init__(self):
        self.tools = {
            "calculate_chart": {
                "description": "Calculate a natal chart with planetary positions, angles, and houses for a given datetime and location. Uses Swiss Ephemeris for arcsecond precision.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "datetime_utc": {
                            "type": "string",
                            "description": "ISO 8601 UTC datetime (e.g., '1990-01-15T12:30:00Z')"
                        },
                        "latitude": {
                            "type": "number",
                            "description": "Geographic latitude in decimal degrees (-90 to 90)"
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Geographic longitude in decimal degrees (-180 to 180)"
                        }
                    },
                    "required": ["datetime_utc", "latitude", "longitude"]
                }
            },
            "store_chart": {
                "description": "Calculate a natal chart and persist it to the database, creating a permanent truth record. Optionally link to an entity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "datetime_utc": {
                            "type": "string",
                            "description": "ISO 8601 UTC datetime (e.g., '1990-01-15T12:30:00Z')"
                        },
                        "latitude": {
                            "type": "number",
                            "description": "Geographic latitude in decimal degrees"
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Geographic longitude in decimal degrees"
                        },
                        "entity_id": {
                            "type": "string",
                            "description": "Optional ID to link chart to an external entity"
                        },
                        "entity_type": {
                            "type": "string",
                            "description": "Optional type of entity (person, event, asset, etc.)"
                        }
                    },
                    "required": ["datetime_utc", "latitude", "longitude"]
                }
            },
            "get_chart": {
                "description": "Retrieve a previously stored chart by its ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "chart_id": {
                            "type": "string",
                            "description": "UUID of the stored chart"
                        }
                    },
                    "required": ["chart_id"]
                }
            },
            "list_charts": {
                "description": "List stored charts with optional filtering by entity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "Filter by entity ID"
                        },
                        "entity_type": {
                            "type": "string",
                            "description": "Filter by entity type"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default 100)"
                        }
                    },
                    "required": []
                }
            }
        }
        
        import os
        self.api_base = os.getenv("TRUEARK_API_URL", "http://localhost:8000")
    
    async def handle_request(self, request: dict) -> dict:
        """Handle incoming MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            return self._response(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "trueark-ephemeris",
                    "version": "1.0.0"
                }
            })
        
        elif method == "tools/list":
            tools_list = [
                {"name": name, **spec}
                for name, spec in self.tools.items()
            ]
            return self._response(request_id, {"tools": tools_list})
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            try:
                result = await self._call_tool(tool_name, arguments)
                return self._response(request_id, {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                })
            except Exception as e:
                return self._error(request_id, -32000, str(e))
        
        elif method == "notifications/initialized":
            return None  # No response needed for notifications
        
        else:
            return self._error(request_id, -32601, f"Method not found: {method}")
    
    async def _call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Execute a tool call via HTTP to the API."""
        import urllib.request
        import urllib.error
        
        if tool_name == "calculate_chart":
            url = f"{self.api_base}/chart"
            data = json.dumps(arguments).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            
        elif tool_name == "store_chart":
            url = f"{self.api_base}/chart/store"
            data = json.dumps(arguments).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            
        elif tool_name == "get_chart":
            chart_id = arguments.get("chart_id")
            url = f"{self.api_base}/charts/{chart_id}"
            req = urllib.request.Request(url)
            
        elif tool_name == "list_charts":
            params = []
            if arguments.get("entity_id"):
                params.append(f"entity_id={arguments['entity_id']}")
            if arguments.get("entity_type"):
                params.append(f"entity_type={arguments['entity_type']}")
            if arguments.get("limit"):
                params.append(f"limit={arguments['limit']}")
            
            query = "&".join(params)
            url = f"{self.api_base}/charts" + (f"?{query}" if query else "")
            req = urllib.request.Request(url)
            
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise Exception(f"API error {e.code}: {error_body}")
    
    def _response(self, request_id: Any, result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    
    def _error(self, request_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


async def main():
    """Run MCP server on stdio."""
    server = MCPServer()
    
    # Read from stdin, write to stdout
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    
    writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())
    
    while True:
        try:
            line = await reader.readline()
            if not line:
                break
            
            request = json.loads(line.decode().strip())
            response = await server.handle_request(request)
            
            if response:
                writer.write((json.dumps(response) + "\n").encode())
                await writer.drain()
                
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    asyncio.run(main())
