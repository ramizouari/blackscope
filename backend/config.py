from pydantic_settings import BaseSettings


class Config(BaseSettings):
    default_model: str = "deepseek-chat"
    default_vl_model: str = "Qwen/Qwen3-VL-30B-A3B-Instruct"
    headless_browser: bool = True
    browser_width: int = 1920
    browser_height: int = 1080
    deepseek_api_key: str | None = None
    openai_api_key: str | None = None
    huggingfacehub_api_token: str | None = None
    mode : str = "dev"
    client_host : str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False


config = Config()
