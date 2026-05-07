from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientSettings(BaseSettings):
    # Application settings for the mic client
    # First we provide default values for each setting, and also specify the corresponding environment variable name using the `alias` parameter in the Field function.
    assistant_api_base_url: str = Field(
        default="http://localhost:8000", alias="ASSISTANT_API_BASE_URL"
    )
    assistant_api_timeout_seconds: float = Field(
        default=300.0, alias="ASSISTANT_API_TIMEOUT_SECONDS"
    )
    mic_sample_rate: int = Field(default=16000, alias="MIC_SAMPLE_RATE")
    mic_channels: int = Field(default=1, alias="MIC_CHANNELS")
    mic_block_size: int = Field(default=1024, alias="MIC_BLOCK_SIZE")
    playback_sample_rate: int = Field(default=22050, alias="PLAYBACK_SAMPLE_RATE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    fallback_path: str = Field(default="assets/fallback_audio", alias="FALLBACK_PATH")

    # We configure the settings model to read from a .env file, and to ignore any extra fields that are not defined in the model. This allows us to have a flexible configuration setup, where we can easily add new settings without having to worry about validation errors for unknown fields.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# lru_cache is a decorator that allows us to cache the result of the get_settings function, so that it only reads the configuration from the environment variables once, and then returns the cached settings object on subsequent calls. This can improve performance by avoiding unnecessary re-reading of environment variables, while still allowing us to easily access the settings throughout our application.
@lru_cache(maxsize=1)
def get_client_settings() -> ClientSettings:
    return ClientSettings()
