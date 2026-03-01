from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig(BaseModel):
    name: str
    user: str
    password: str
    host: str
    port: int
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class AppConfig(BaseModel):
    port: int
    host: str
    debug: bool
    app: str



class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="APP__",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    database: DatabaseConfig = DatabaseConfig()
    app: AppConfig = AppConfig()

settings = Settings()
