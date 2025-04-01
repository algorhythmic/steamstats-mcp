# A list of steam api endpoints to be used in the steamstats MCP server

## GetUserStatsForGame

Retrieves detailed statistics for a user in a specific game.

Example URL:
text
https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v1/?key=<API_KEY>&steamid=<STEAM_ID>&appid=<GAME_APPID>
Parameters:
key: Your API key.
steamid: The Steam ID of the user.
appid: The unique identifier for the game

## GetGlobalStatsForGame

Retrieves aggregated values for global stats if supported by the game.

Example URL:
text
https://api.steampowered.com/ISteamUserStats/GetGlobalStatsForGame/v1/?key=<API_KEY>&appid=<GAME_APPID>
Parameters:
key: Your API key.
appid: The unique identifier for the game

## GetSchemaForGame

Provides metadata about a specific game's stats and achievements.

Example URL:
text
https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key=<API_KEY>&appid=<GAME_APPID>
Parameters:
key: Your API key.
appid: The unique identifier for the game

## GetSupportedAPIList

Returns a list of all supported Steam Web API interfaces and methods.

Example URL:

text
https://api.steampowered.com/ISteamWebAPIUtil/GetSupportedAPIList/v1/?key=<API_KEY>&format=json
Use case: Explore available APIs dynamically

## GetAppList

Retrieves a list of all Steam apps (games, software, etc.).

Example URL:

text
https://api.steampowered.com/ISteamApps/GetAppList/v0002/?key=<API_KEY>&format=json
Use case: Access the complete list of Steam applications for further querying

## GetGlobalAchievementPercentagesForApp

Retrieves global achievement percentages for a specific game.

Example URL:

text
https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid=<GAME_ID>&format=json
Use case: Analyze achievement completion rates across all players globally

## AppDetails (Steam Store API)

Provides detailed information about a specific app (game).

Example URL:

text
https://store.steampowered.com/api/appdetails?appids=<APP_ID>
Use case: Retrieve pricing, descriptions, and other store-related details