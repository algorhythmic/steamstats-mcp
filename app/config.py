import os
import logging
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration settings."""

    # Model config
    model_config = SettingsConfigDict(
        env_file='.env',          # Load .env file
        env_file_encoding='utf-8',
        extra='ignore',           # Ignore extra env vars
        case_sensitive=False      # Env vars are case-insensitive
    )

    # Steam API Key - crucial, will raise error if missing due to no default
    steam_api_key: str = Field(..., validation_alias='STEAM_API_KEY')

    # Logging configuration
    log_level: str = Field("INFO", validation_alias='LOG_LEVEL')

    # Server configuration
    host: str = Field("0.0.0.0", validation_alias='HOST')
    port: int = Field(8000, validation_alias='PORT')

    # Steam API URLs
    steam_api_base_url: HttpUrl = Field("https://api.steampowered.com", validation_alias='STEAM_API_BASE_URL')
    steam_store_api_base_url: HttpUrl = Field("https://store.steampowered.com/api", validation_alias='STEAM_STORE_API_BASE_URL')


# Instantiate settings early to catch missing env vars on import
try:
    settings = Settings()
except Exception as e:
    # Log critical error and exit if config fails to load (e.g., missing STEAM_API_KEY)
    logging.basicConfig(level="CRITICAL", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.critical(f"Failed to load application settings: {e}")
    # In a real app, you might want a more graceful shutdown or specific handling
    raise SystemExit(f"Configuration error: {e}")


# --- Logging Setup ---
# Configure logging based on loaded settings
logging.basicConfig(
    level=settings.log_level.upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    # Consider adding handlers for file logging or structured JSON logging later
)
# Get a logger instance specifically for the config module (optional)
config_logger = logging.getLogger(__name__)

# Log a warning if the default placeholder key is used (optional but helpful)
# Note: BaseSettings should prevent the placeholder if '...' is used and no .env value exists.
# This check remains useful if a default value like "YOUR_API_KEY_HERE" was set in .env
if settings.steam_api_key == "YOUR_API_KEY_HERE":
     config_logger.warning("STEAM_API_KEY is set to the default placeholder value in the environment. Steam API calls will likely fail.")

config_logger.info(f"Application settings loaded. Log level: {settings.log_level}")

# --- Exported Logger ---
# Provide a logger instance for other modules to import easily
# Using the root logger configuration applied above
app_logger = logging.getLogger("steamstats_mcp_app") # Use a specific name for the app's logger