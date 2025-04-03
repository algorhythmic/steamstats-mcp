from typing import Optional, Any

# --- Custom Exceptions ---

class SteamApiException(Exception):
    """Custom exception for Steam API specific errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

class NetworkError(Exception):
    """Custom exception for network-related errors during API calls."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details