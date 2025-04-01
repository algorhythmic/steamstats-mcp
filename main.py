from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# Ideally, read your Steam API key from environment variables for security.
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "your_steam_api_key_here")

class MCPMessage(BaseModel):
    jsonrpc: str
    id: int
    method: str
    params: dict

@app.post("/message")
async def mcp_message(message: MCPMessage):
    if message.method == "tools/call":
        command = message.params.get("name")
        arguments = message.params.get("arguments", {})
        if command == "getCurrentPlayers":
            appid = arguments.get("appid")
            if not appid:
                raise HTTPException(status_code=400, detail="Missing appid")
            result = get_current_players(appid)
            return {"jsonrpc": "2.0", "id": message.id, "result": result}
        # Additional commands (e.g., getPopularGames) can be added here.
        else:
            raise HTTPException(status_code=400, detail="Unknown command")
    else:
        raise HTTPException(status_code=400, detail="Unsupported method")

def get_current_players(appid: int):
    """
    Queries the Steam API endpoint to get the current number of players for a given appid.
    """
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "API request failed"}
    data = response.json()
    return data

if __name__ == "__main__":
    # Launch the server with Uvicorn.
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
