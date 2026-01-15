from pydantic_settings import BaseSettings


class Config(BaseSettings):
    default_model: str = "deepseek-chat"
    headless_browser: bool = True
    deepseek_api_key: str | None = None
    openai_api_key: str | None = None
    huggingfacehub_api_token: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False


config = Config()
