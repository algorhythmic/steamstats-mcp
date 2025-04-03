import asyncio
import json
from typing import List, Optional, Dict, Any, Union

# FastAPI & Pydantic
from fastapi import FastAPI, Request, status, Response
from fastapi.responses import JSONResponse, StreamingResponse # Keep StreamingResponse for potential future SSE use
from pydantic import BaseModel, Field, ValidationError

# Uvicorn for running
import uvicorn
# from mcp.types import Tool # No longer needed here

# Project-specific imports
from .config import settings, app_logger
from .models import * # Import all tool argument models (though not directly used in main.py, needed by handlers)
from .core.exceptions import SteamApiException, NetworkError
from .api.endpoints.steam_tools import TOOL_HANDLERS, get_tool_definitions

# --- Redefined MCP Models & Constants (Simpler Structure) ---

# MCP Error Codes
MCP_ERROR_PARSE_ERROR = -32700
MCP_ERROR_INVALID_REQUEST = -32600
MCP_ERROR_METHOD_NOT_FOUND = -32601
MCP_ERROR_INVALID_PARAMS = -32602
MCP_ERROR_INTERNAL_ERROR = -32603
MCP_ERROR_STEAM_API_ERROR = -32000 # Custom server error start
MCP_ERROR_NETWORK_ERROR = -32001

# MCP Models
class MCPBaseRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[int, str]

class MCPToolsCallParams(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class MCPToolsCallRequest(MCPBaseRequest):
    method: str = "tools/call"
    params: MCPToolsCallParams

class MCPErrorData(BaseModel):
    type: str
    details: Any

class MCPError(BaseModel):
    code: int
    message: str
    data: Optional[MCPErrorData] = None

class MCPErrorResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[int, str]] = None
    error: MCPError

class MCPSuccessResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[int, str]
    result: Dict[str, Any] = Field(default_factory=dict)

# --- Error Response Helper ---

def create_error_response(
    request_id: Optional[Union[int, str]],
    code: int,
    message: str,
    data_type: Optional[str] = None,
    data_details: Optional[Any] = None
) -> JSONResponse:
    """Creates a standardized JSON-RPC error response for FastAPI."""
    error_data = None
    if data_type:
        error_data = MCPErrorData(type=data_type, details=data_details or message)

    error = MCPError(code=code, message=message, data=error_data)
    response_content = MCPErrorResponse(id=request_id, error=error)

    # Determine appropriate HTTP status code
    http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
    if code == MCP_ERROR_PARSE_ERROR or code == MCP_ERROR_INVALID_REQUEST:
        http_status = status.HTTP_400_BAD_REQUEST
    elif code == MCP_ERROR_METHOD_NOT_FOUND:
        http_status = status.HTTP_404_NOT_FOUND
    elif code == MCP_ERROR_INVALID_PARAMS:
        http_status = status.HTTP_422_UNPROCESSABLE_ENTITY

    return JSONResponse(
        status_code=http_status,
        content=response_content.model_dump(exclude_none=True)
    )

# --- FastAPI Application Setup ---

app = FastAPI(
    title="SteamStats MCP Server (FastAPI)",
    description="Provides Steam statistics and data via the Model Context Protocol.",
    version=settings.steam_api_key, # Example: Use a setting here if desired
)

# --- Exception Handlers ---

@app.exception_handler(SteamApiException)
async def steam_api_exception_handler(request: Request, exc: SteamApiException):
    request_id = None
    try: # Try to get request ID, might fail if request parsing failed earlier
        body = await request.json()
        request_id = body.get("id")
    except Exception: pass
    app_logger.error(f"Steam API Error during request {request.url}: {exc.message}")
    return create_error_response(
        request_id=request_id,
        code=MCP_ERROR_STEAM_API_ERROR,
        message=f"Steam API Error: {exc.message}",
        data_type="SteamApiError",
        data_details={"status_code": exc.status_code, "details": exc.details}
    )

@app.exception_handler(NetworkError)
async def network_exception_handler(request: Request, exc: NetworkError):
    request_id = None
    try:
        body = await request.json()
        request_id = body.get("id")
    except Exception: pass
    app_logger.error(f"Network Error during request {request.url}: {exc.message}")
    return create_error_response(
        request_id=request_id,
        code=MCP_ERROR_NETWORK_ERROR,
        message=f"Network Error: {exc.message}",
        data_type="NetworkError",
        data_details={"details": exc.details}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = None
    try:
        body = await request.json()
        request_id = body.get("id")
    except Exception: pass
    app_logger.exception(f"Unhandled exception during request {request.url}")
    return create_error_response(
        request_id=request_id,
        code=MCP_ERROR_INTERNAL_ERROR,
        message="An unexpected internal server error occurred.",
        data_type="InternalServerError",
        data_details=str(exc)
    )

# --- MCP Endpoints ---

@app.get("/message")
async def mcp_sse_endpoint(request: Request):
    """Handles Server-Sent Events (SSE) connection requests."""
    # This endpoint establishes the connection.
    # For a simple implementation, we just keep it open.
    # A more advanced version could push server-initiated events here.

    async def event_generator(request: Request):
        # Send an initial event (optional, but might help client confirm connection)
        yield f"event: info\ndata: {json.dumps({'message': 'SSE connection established'})}\n\n"
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    app_logger.info("SSE client disconnected.")
                    break
                # Send a keep-alive comment every 15 seconds (optional)
                # Helps prevent timeouts in some network configurations
                yield ": keep-alive\n\n"
                await asyncio.sleep(15)
        except asyncio.CancelledError: # pragma: no cover
            app_logger.info("SSE connection cancelled.")
        except Exception as e:
            app_logger.error(f"Error in SSE event generator: {e}", exc_info=True)
        finally:
            app_logger.info("Closing SSE event generator.")

    # Return the streaming response for SSE
    return StreamingResponse(event_generator(request), media_type="text/event-stream")

@app.get("/")
async def get_server_info():
    """Provides basic server information and capabilities."""
    return {
        "name": "SteamStats MCP Server (FastAPI)",
        "version": settings.steam_api_key,
        "description": "Provides Steam statistics and data via the Model Context Protocol.",
        "protocol_version": "1.0",
        "capabilities": {
            "tools": True,
            "resources": False,
            "streaming": False # Set to False as we removed the SSE endpoint for now
        }
    }

@app.get("/tools")
async def get_tools() -> Dict[str, List[Dict[str, Any]]]: # Revert return type hint
    """Returns the list of available tools and their schemas."""
    # Revert to returning the dictionary structure {"tools": [...]}
    return {"tools": get_tool_definitions()} # Use imported function

@app.post("/message", response_model=Union[MCPSuccessResponse, MCPErrorResponse])
async def mcp_message(request: Request):
    """Handles incoming JSON-RPC messages for tool calls."""
    request_id = None
    try:
        body = await request.json()
        request_id = body.get("id")

        # Basic JSON-RPC validation
        if body.get("jsonrpc") != "2.0" or "method" not in body or "params" not in body:
             raise ValueError("Invalid JSON-RPC request structure.") # Caught by generic handler

        # Use Pydantic for robust request parsing
        mcp_request = MCPToolsCallRequest.model_validate(body)
        request_id = mcp_request.id # Update request_id

        if mcp_request.method != "tools/call":
            # Use METHOD_NOT_FOUND error code
            return create_error_response(
                request_id=request_id,
                code=MCP_ERROR_METHOD_NOT_FOUND,
                message=f"Unsupported method: {mcp_request.method}",
                data_type="MethodNotFound"
            )

        tool_name = mcp_request.params.name
        tool_args_dict = mcp_request.params.arguments

        if tool_name not in TOOL_HANDLERS:
             return create_error_response(
                 request_id=request_id,
                 code=MCP_ERROR_METHOD_NOT_FOUND, # Or INVALID_PARAMS depending on spec interpretation
                 message=f"Tool '{tool_name}' not found.",
                 data_type="ToolNotFound"
             )

        args_model, handler_func = TOOL_HANDLERS[tool_name]

        # Validate tool arguments
        try:
            tool_args = args_model.model_validate(tool_args_dict)
        except ValidationError as e:
            app_logger.warning(f"Invalid parameters for tool '{tool_name}': {e.errors()}")
            return create_error_response(
                request_id=request_id,
                code=MCP_ERROR_INVALID_PARAMS,
                message=f"Invalid parameters for tool '{tool_name}'.",
                data_type="ValidationError",
                data_details=e.errors()
            )

        # Execute the tool handler (can raise SteamApiException, NetworkError, or others)
        app_logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")
        # Handlers are async, await them directly
        result_data = await handler_func(tool_args)
        app_logger.info(f"Tool '{tool_name}' executed successfully.")

        # Format successful response
        response_content = MCPSuccessResponse(id=request_id, result=result_data)
        # Return standard JSONResponse for POST
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_content.model_dump(exclude_none=True)
        )

    except json.JSONDecodeError:
        # Handle cases where the request body isn't valid JSON
        return create_error_response(
            request_id=None, # ID might not be available
            code=MCP_ERROR_PARSE_ERROR,
            message="Failed to parse JSON request body.",
            data_type="ParseError"
        )
    except ValueError as e:
         # Catch basic structure errors before Pydantic validation
         app_logger.warning(f"Invalid Request Structure: {e}")
         return create_error_response(
             request_id=request_id, # Use ID if available
             code=MCP_ERROR_INVALID_REQUEST,
             message=str(e),
             data_type="InvalidRequest"
         )
    # Specific exceptions (SteamApiException, NetworkError) are handled by @app.exception_handler
    # Generic Exception is also handled by @app.exception_handler

# --- Main Execution Guard Removed ---
# Run the server using: uvicorn app.main:app --host <host> --port <port> --reload