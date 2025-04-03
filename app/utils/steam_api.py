import requests
from typing import Dict, Optional, Any

# Import shared components
from ..config import settings, app_logger
from ..core.exceptions import SteamApiException, NetworkError

def make_steam_api_request(
    interface: str,
    method: str,
    version: str,
    params: Optional[Dict[str, Any]] = None,
    api_base_url: Optional[str] = None, # Allow overriding for store API etc.
    use_key: bool = True,
    http_method: str = "GET"
) -> Dict[str, Any]:
    """
    Makes a request to the Steam Web API and handles basic errors.

    Args:
        interface: The API interface (e.g., "ISteamUserStats").
        method: The API method (e.g., "GetNumberOfCurrentPlayers").
        version: The API version (e.g., "v1").
        params: Dictionary of query parameters for the API call.
        api_base_url: The base URL for the API endpoint.
        use_key: Whether to include the STEAM_API_KEY.
        http_method: The HTTP method to use ('GET' or 'POST').

    Returns:
        The JSON response data as a dictionary.

    Raises:
        NetworkError: If there's a connection issue or timeout.
        SteamApiException: If the API returns a non-200 status code or internal errors.
    """
    if params is None:
        params = {}

    # Add API key if required
    if use_key:
        # settings.steam_api_key is validated on startup by config.py
        # No need for the placeholder check here anymore.
        params['key'] = settings.steam_api_key

    # Ensure format is json unless otherwise specified
    if 'format' not in params:
         params['format'] = 'json'

    # Determine base URL
    final_api_base_url = api_base_url if api_base_url is not None else str(settings.steam_api_base_url)

    # Construct URL based on whether it's Store API or Web API
    if final_api_base_url == str(settings.steam_store_api_base_url):
        # Store API uses query params directly, no interface/method/version path
        url = final_api_base_url + "/" + method # e.g. /api/appdetails
    else:
        # Web API structure
        url = f"{final_api_base_url}/{interface}/{method}/{version}/"

    request_args = {"params": params, "timeout": (10, 30)} # (connect timeout, read timeout)

    try:
        app_logger.debug(f"Making {http_method} request to {url} with params: {params}")
        if http_method.upper() == "GET":
            response = requests.get(url, **request_args)
        elif http_method.upper() == "POST":
             response = requests.post(url, **request_args) # Note: Steam API mostly uses GET
        else:
            raise ValueError(f"Unsupported HTTP method: {http_method}")

        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        # Even with 200 OK, some Steam endpoints might return errors internally
        data = response.json()
        app_logger.debug(f"Received response: {data}")

        # Basic check for 'response' wrapper used by some endpoints
        if isinstance(data, dict) and 'response' in data:
             if not data['response']: # Empty response often indicates an issue (e.g., invalid appid)
                 raise SteamApiException("API returned an empty response.", status_code=response.status_code, details=f"Check parameters for {interface}/{method}")
             # Check for result codes if present (common pattern)
             if 'result' in data['response'] and data['response']['result'] != 1:
                  error_msg = data['response'].get('error', 'Unknown API error result code.')
                  raise SteamApiException(f"API Error: {error_msg}", status_code=response.status_code, details=data['response'])


        # Check for 'playerstats' wrapper and success flags (common pattern)
        if isinstance(data, dict) and 'playerstats' in data:
            if not data['playerstats'].get('success', True): # Assume success if key missing? Be cautious.
                error_msg = data['playerstats'].get('error', 'Unknown API error in playerstats.')
                # Handle specific known errors
                if "Profile is private" in error_msg:
                     raise SteamApiException("Profile is private", status_code=response.status_code, details=error_msg)
                raise SteamApiException(f"API Error: {error_msg}", status_code=response.status_code, details=data['playerstats'])

        # Check for store API success flag
        # Store API specific checks (appdetails)
        if final_api_base_url == str(settings.steam_store_api_base_url) and method == 'appdetails':
             # The structure is { "appid_str": { "success": bool, "data": {...} } }
             # We don't raise an error here for individual appid failures,
             # the caller (handle_get_app_details) will process this structure.
             pass


        return data

    except requests.exceptions.Timeout as e:
        app_logger.error(f"Timeout connecting to Steam API: {e}")
        raise NetworkError("Timeout connecting to Steam API.", details=str(e)) from e
    except requests.exceptions.ConnectionError as e:
        app_logger.error(f"Connection error connecting to Steam API: {e}")
        raise NetworkError("Could not connect to Steam API.", details=str(e)) from e
    except requests.exceptions.HTTPError as e:
        app_logger.error(f"HTTP error from Steam API: {e.response.status_code} - {e.response.text}")
        raise SteamApiException(f"Steam API returned status {e.response.status_code}", status_code=e.response.status_code, details=e.response.text) from e
    except requests.exceptions.JSONDecodeError as e:
         app_logger.error(f"Failed to decode JSON response from Steam API: {e}")
         raise SteamApiException("Invalid JSON response received from Steam API.", details=str(e)) from e
    except requests.exceptions.RequestException as e:
        app_logger.error(f"An unexpected network error occurred: {e}")
        raise NetworkError("An unexpected network error occurred.", details=str(e)) from e