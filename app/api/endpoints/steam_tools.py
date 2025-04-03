from typing import Dict, Any, List

# Import shared components & types
from ...config import app_logger, settings # Relative imports for sibling/parent modules
from ...core.exceptions import SteamApiException, NetworkError
from ...models import (
    GetCurrentPlayersArgs, GetAppDetailsArgs, GetGameSchemaArgs, GetGameNewsArgs,
    GetPlayerAchievementsArgs, GetUserStatsForGameArgs, GetSupportedApiListArgs,
    GetAppListArgs, GetGlobalAchievementPercentagesArgs, GetGlobalStatsForGameArgs
)
from ...utils.steam_api import make_steam_api_request

# --- Command Handler Functions ---

async def handle_get_current_players(args: GetCurrentPlayersArgs) -> Dict[str, Any]:
    """Retrieves the current number of players for a given Steam AppID."""
    app_logger.info(f"Handling getCurrentPlayers for appid: {args.appid}")
    api_params = {"appid": args.appid}
    try:
        result = make_steam_api_request(
            interface="ISteamUserStats",
            method="GetNumberOfCurrentPlayers",
            version="v1",
            params=api_params
        )
        return result
    except (SteamApiException, NetworkError) as e:
        raise e

async def handle_get_app_details(args: GetAppDetailsArgs) -> Dict[str, Any]:
    """Retrieves store page details for one or more Steam AppIDs."""
    app_logger.info(f"Handling getAppDetails for appids: {args.appids}, country: {args.country}")
    appids_str = ",".join(map(str, args.appids))
    api_params = {"appids": appids_str}
    if args.country:
        api_params["cc"] = args.country
        api_params["l"] = "en"

    try:
        result = make_steam_api_request(
            interface="",
            method="appdetails",
            version="",
            params=api_params,
            api_base_url=str(settings.steam_store_api_base_url),
            use_key=False
        )
        return {str(k): v for k, v in result.items()}
    except (SteamApiException, NetworkError) as e:
        raise e

async def handle_get_game_schema(args: GetGameSchemaArgs) -> Dict[str, Any]:
    """Retrieves the game schema (stats and achievements definitions) for a given AppID."""
    app_logger.info(f"Handling getGameSchema for appid: {args.appid}")
    api_params = {"appid": args.appid}
    try:
        result = make_steam_api_request(
            interface="ISteamUserStats",
            method="GetSchemaForGame",
            version="v2",
            params=api_params
        )
        if 'game' not in result:
             raise SteamApiException(f"Schema not found for appid {args.appid}", details="API returned success but no 'game' object.")
        return result
    except (SteamApiException, NetworkError) as e:
        if isinstance(e, SteamApiException) and e.status_code == 500 and e.details and "Requested app has no stats" in str(e.details):
             raise SteamApiException(f"Schema not found or app has no stats for appid {args.appid}", status_code=e.status_code, details=e.details) from e
        raise e

async def handle_get_game_news(args: GetGameNewsArgs) -> Dict[str, Any]:
    """Retrieves the latest news items for a given AppID."""
    app_logger.info(f"Handling getGameNews for appid: {args.appid}, count: {args.count}, maxlength: {args.maxlength}")
    api_params = {
        "appid": args.appid,
        "count": args.count,
        "maxlength": args.maxlength
    }
    try:
        result = make_steam_api_request(
            interface="ISteamNews",
            method="GetNewsForApp",
            version="v2",
            params=api_params
        )
        if 'appnews' not in result:
             raise SteamApiException(f"News not found for appid {args.appid}", details="API returned success but no 'appnews' object.")
        return result
    except (SteamApiException, NetworkError) as e:
        raise e

async def handle_get_player_achievements(args: GetPlayerAchievementsArgs) -> Dict[str, Any]:
    """Retrieves a player's achievement status for a specific game."""
    app_logger.info(f"Handling getPlayerAchievements for steamid: {args.steamid}, appid: {args.appid}")
    api_params = {
        "steamid": args.steamid,
        "appid": args.appid,
        "l": "english"
    }
    try:
        result = make_steam_api_request(
            interface="ISteamUserStats",
            method="GetPlayerAchievements",
            version="v1",
            params=api_params
        )
        if 'playerstats' not in result:
             raise SteamApiException(f"Could not retrieve player achievements for steamid {args.steamid}, appid {args.appid}", details="API returned success but no 'playerstats' object.")
        if 'achievements' not in result['playerstats']:
             result['playerstats']['achievements'] = []
        return result
    except (SteamApiException, NetworkError) as e:
        raise e

async def handle_get_user_stats_for_game(args: GetUserStatsForGameArgs) -> Dict[str, Any]:
    """Retrieves detailed statistics for a user in a specific game."""
    app_logger.info(f"Handling getUserStatsForGame for steamid: {args.steamid}, appid: {args.appid}")
    api_params = {
        "steamid": args.steamid,
        "appid": args.appid
    }
    try:
        result = make_steam_api_request(
            interface="ISteamUserStats",
            method="GetUserStatsForGame",
            version="v1",
            params=api_params
        )
        if 'playerstats' not in result:
             raise SteamApiException(f"Could not retrieve user stats for steamid {args.steamid}, appid {args.appid}", details="API returned success but no 'playerstats' object.")
        if 'stats' not in result['playerstats']:
            result['playerstats']['stats'] = []
        if 'achievements' not in result['playerstats']:
             result['playerstats']['achievements'] = []
        return result
    except (SteamApiException, NetworkError) as e:
        raise e

async def handle_get_supported_api_list(args: GetSupportedApiListArgs) -> Dict[str, Any]:
    """Retrieves the complete list of supported Steam Web API interfaces and methods."""
    app_logger.info("Handling getSupportedApiList")
    api_params = {}
    try:
        result = make_steam_api_request(
            interface="ISteamWebAPIUtil",
            method="GetSupportedAPIList",
            version="v1",
            params=api_params
        )
        if 'apilist' not in result or 'interfaces' not in result.get('apilist', {}):
             raise SteamApiException("Invalid response structure for GetSupportedAPIList", details="API response missing 'apilist' or 'apilist.interfaces'.")
        return result
    except (SteamApiException, NetworkError) as e:
        raise e

async def handle_get_app_list(args: GetAppListArgs) -> Dict[str, Any]:
    """Retrieves the complete list of public applications available on Steam."""
    app_logger.info("Handling getAppList")
    api_params = {}
    try:
        result = make_steam_api_request(
            interface="ISteamApps",
            method="GetAppList",
            version="v2",
            params=api_params
        )
        if 'applist' not in result or 'apps' not in result.get('applist', {}):
             raise SteamApiException("Invalid response structure for GetAppList", details="API response missing 'applist' or 'applist.apps'.")
        return result
    except (SteamApiException, NetworkError) as e:
        raise e

async def handle_get_global_achievement_percentages(args: GetGlobalAchievementPercentagesArgs) -> Dict[str, Any]:
    """Retrieves the global achievement completion percentages for a specific game."""
    app_logger.info(f"Handling getGlobalAchievementPercentages for gameid (aliased from appid): {args.appid}")
    api_params = args.model_dump(by_alias=True)
    try:
        result = make_steam_api_request(
            interface="ISteamUserStats",
            method="GetGlobalAchievementPercentagesForApp",
            version="v2",
            params=api_params
        )
        if 'achievementpercentages' not in result or 'achievements' not in result.get('achievementpercentages', {}):
             raise SteamApiException(f"Could not retrieve achievement percentages for gameid {args.appid}", details="API response missing 'achievementpercentages' or 'achievementpercentages.achievements'. Check gameid.")
        return result
    except (SteamApiException, NetworkError) as e:
        if isinstance(e, SteamApiException) and e.status_code == 400:
             raise SteamApiException(f"Invalid gameid or no achievements found for gameid {args.appid}", status_code=e.status_code, details=e.details) from e
        raise e

async def handle_get_global_stats_for_game(args: GetGlobalStatsForGameArgs) -> Dict[str, Any]:
    """Retrieves aggregated global stats for a specific game."""
    app_logger.info(f"Handling getGlobalStatsForGame for appid: {args.appid}, stats: {args.stat_names}")
    api_params = {
        "appid": args.appid,
        "count": len(args.stat_names),
    }
    for i, stat_name in enumerate(args.stat_names):
        api_params[f"name[{i}]"] = stat_name
    if args.start_date is not None:
        api_params["startdate"] = args.start_date
    if args.end_date is not None:
        api_params["enddate"] = args.end_date

    try:
        result = make_steam_api_request(
            interface="ISteamUserStats",
            method="GetGlobalStatsForGame",
            version="v1",
            params=api_params
        )
        if 'response' not in result:
             raise SteamApiException("Invalid response structure for GetGlobalStatsForGame", details="API response missing 'response'.")
        if 'globalstats' not in result['response']:
             if result['response'].get('result') != 1:
                  error_msg = result['response'].get('error', f'Unknown error retrieving global stats for {args.appid}')
                  raise SteamApiException(error_msg, details=result['response'])
             else:
                  app_logger.warning(f"GetGlobalStatsForGame for appid {args.appid} returned result=1 but no 'globalstats' object. Returning empty stats.")
                  result['response']['globalstats'] = {}
        return result
    except (SteamApiException, NetworkError) as e:
        raise e


# --- Tool Mapping and Dispatch ---

TOOL_HANDLERS = {
    "getCurrentPlayers": (GetCurrentPlayersArgs, handle_get_current_players),
    "getAppDetails": (GetAppDetailsArgs, handle_get_app_details),
    "getGameSchema": (GetGameSchemaArgs, handle_get_game_schema),
    "getGameNews": (GetGameNewsArgs, handle_get_game_news),
    "getPlayerAchievements": (GetPlayerAchievementsArgs, handle_get_player_achievements),
    "getUserStatsForGame": (GetUserStatsForGameArgs, handle_get_user_stats_for_game),
    "getSupportedApiList": (GetSupportedApiListArgs, handle_get_supported_api_list),
    "getAppList": (GetAppListArgs, handle_get_app_list),
    "getGlobalAchievementPercentages": (GetGlobalAchievementPercentagesArgs, handle_get_global_achievement_percentages),
    "getGlobalStatsForGame": (GetGlobalStatsForGameArgs, handle_get_global_stats_for_game),
}

def get_tool_definitions() -> List[Dict[str, Any]]:
    """Generates the tool definitions based on Pydantic models."""
    definitions = []
    for name, (args_model, _) in TOOL_HANDLERS.items():
        schema = args_model.model_json_schema()
        definitions.append({
            "name": name,
            "description": args_model.__doc__ or f"Tool to handle {name}",
            "input_schema": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
            }
        })
    return definitions