from pydantic_settings import BaseSettings, SettingsConfigDict

class BotConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', env_prefix='TELEGRAM_', extra='ignore')
    bot_token: str
    log_level: str = "INFO"

class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', env_prefix='LLM_', extra='ignore')
    model: str
    api_key: str
    log_level: str = "INFO"

class MistralOCRConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', env_prefix='MISTRAL_', extra='ignore')
    api_key: str
