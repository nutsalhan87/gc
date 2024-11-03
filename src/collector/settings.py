from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COLLECTOR_")

    db_uri: str = Field(default=...)
    self_url: str = Field(default=...)
    registry_url: str = Field(default=...)
    position_x: int = Field(default=...)
    position_y: int = Field(default=...)


settings = Settings()
