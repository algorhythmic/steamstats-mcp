from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Command Argument Models (Based on STEAMSTATS_MCP_SPECIFICATION.md) ---
# These models define the expected input structure for each tool.

class GetCurrentPlayersArgs(BaseModel):
    """Arguments for the getCurrentPlayers tool."""
    appid: int = Field(..., description="The Steam Application ID of the game.")

class GetAppDetailsArgs(BaseModel):
    """Arguments for the getAppDetails tool."""
    appids: List[int] = Field(..., description="A list of Steam Application IDs.")
    country: Optional[str] = Field(None, description="ISO 3166 country code for regional pricing/filtering (e.g., 'US', 'GB'). Optional.")

class GetGameSchemaArgs(BaseModel):
    """Arguments for the getGameSchema tool."""
    appid: int = Field(..., description="The Steam Application ID of the game.")

class GetGameNewsArgs(BaseModel):
    """Arguments for the getGameNews tool."""
    appid: int = Field(..., description="The Steam Application ID of the game.")
    count: int = Field(10, description="Number of news items to retrieve.")
    maxlength: int = Field(300, description="Maximum length of the 'contents' field for each news item. 0 for full content.")

class GetPlayerAchievementsArgs(BaseModel):
    """Arguments for the getPlayerAchievements tool."""
    steamid: str = Field(..., description="The player's 64-bit Steam ID.")
    appid: int = Field(..., description="The Steam Application ID of the game.")

class GetUserStatsForGameArgs(BaseModel):
    """Arguments for the getUserStatsForGame tool."""
    steamid: str = Field(..., description="The player's 64-bit Steam ID.")
    appid: int = Field(..., description="The Steam Application ID of the game.")

class GetSupportedApiListArgs(BaseModel):
    """Arguments for the getSupportedApiList tool (no arguments required)."""
    pass

class GetAppListArgs(BaseModel):
    """Arguments for the getAppList tool (no arguments required)."""
    pass

class GetGlobalAchievementPercentagesArgs(BaseModel):
    """Arguments for the getGlobalAchievementPercentages tool."""
    # Note: 'appid' is aliased to 'gameid' for the underlying Steam API call.
    appid: int = Field(..., alias="gameid", description="The Steam Application ID of the game. Mapped to 'gameid' for the API call.")

class GetGlobalStatsForGameArgs(BaseModel):
    """Arguments for the getGlobalStatsForGame tool."""
    appid: int = Field(..., description="The Steam Application ID of the game.")
    stat_names: List[str] = Field(..., description="List of specific global stat API names to retrieve.")
    start_date: Optional[int] = Field(None, description="Optional Unix timestamp for the start date.")
    end_date: Optional[int] = Field(None, description="Optional Unix timestamp for the end date.")