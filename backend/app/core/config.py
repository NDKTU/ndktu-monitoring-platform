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


class AuthConfig(BaseModel):
    secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int


class AdminConfig(BaseModel):
    login: str
    password: str

class HikvisionConfig(BaseModel):
    enabled: bool = False


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="APP__",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    database: DatabaseConfig
    app: AppConfig
    auth: AuthConfig
    admin: AdminConfig
    hikvision: HikvisionConfig = HikvisionConfig()

settings = Settings()
