# SteamStats MCP Server Specification Plan

This document outlines the plan for creating the specification for the SteamStats MCP server.

## 1. Define Core Concepts & Architecture

*   **Purpose:** Outline the server's purpose: To act as an MCP interface to the Steam Web API, providing structured access to game statistics.
*   **Technology Stack:** Confirm the technology stack: Python, FastAPI, Pydantic, Uvicorn, Requests, UV.
*   **Request Flow:** Describe the basic request flow using the diagram below.

## 2. Specify MCP Interaction

*   Define how the server handles incoming `tools/call` requests via the `/message` endpoint.
*   Specify the standard request and response format based on the MCP protocol (JSON-RPC style).

## 3. Detail MCP Commands

For each command, define:
*   `name`: The unique identifier used in the MCP message.
*   `description`: A clear explanation of what the command does.
*   `arguments`: A Pydantic model defining the expected input parameters (JSON schema).
*   `result`: A Pydantic model defining the structure of the successful response data (JSON schema).
*   `errors`: A list of potential errors specific to the command.

**Proposed Commands:**
*   `getCurrentPlayers`: (Existing) Get current player count for an app.
*   `getAppDetails`: (New) Get store page details for one or more apps.
*   `getGameSchema`: (New) Get the schema for a game's stats and achievements.
*   `getGameNews`: (New) Get the latest news articles for a game.
*   `getPlayerAchievements`: (New) Get a specific player's achievement status for a game.

## 4. Specify Robustness Enhancements

*   **Error Handling:**
    *   Define a standardized JSON-RPC error response format.
    *   Categorize common errors: Input Validation, Steam API, Network, Internal Server Errors.
    *   Specify how API errors are handled and mapped.
*   **Logging:**
    *   Specify logging format (e.g., JSON).
    *   Define log levels.
    *   Detail information to be logged per request.
*   **Input Validation:**
    *   Mandate Pydantic models for arguments.
    *   Specify how validation errors are reported.
*   **Configuration:**
    *   Confirm use of environment variables (`STEAM_API_KEY`).
    *   Consider other potential configurations.
*   **Steam API Interaction:**
    *   Document the base URL.
    *   Reiterate API key requirement.
    *   Mention rate limiting awareness.

## 5. Structure & Format

*   Organize the specification into logical sections.
*   Use clear and concise language.
*   Employ formatting like code blocks for schemas and examples.

## Request Flow Diagram

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as SteamStats MCP Server
    participant SteamAPI as Steam Web API

    Client->>Server: POST /message (tools/call, command, args)
    Server->>Server: Validate MCP message format
    alt Invalid Format
        Server-->>Client: Error Response (e.g., Invalid Request)
    else Valid Format
        Server->>Server: Parse command & arguments
        Server->>Server: Validate arguments using Pydantic
        alt Invalid Arguments
            Server-->>Client: Error Response (Validation Error)
        else Valid Arguments
            Server->>SteamAPI: Make API Request(s) (e.g., GET /ISteamUserStats/...)
            SteamAPI-->>Server: API Response (JSON data or error)
            alt Steam API Error
                Server->>Server: Log API Error
                Server-->>Client: Error Response (API Error)
            else Successful API Response
                Server->>Server: Process API data
                Server-->>Client: Success Response (result data)
            end
        end
    end