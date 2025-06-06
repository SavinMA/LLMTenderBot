from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class BotConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', env_prefix='TELEGRAM_', extra='ignore')
    bot_token: str

class AnalyzerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', env_prefix='ANALYZER_', extra='ignore')
    type: Literal["mistral", "ollama"] = "mistral" # ollama

class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', env_prefix='LLM_', extra='ignore')
    model: str
    host: str

class MistralConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', env_prefix='MISTRAL_', extra='ignore')
    api_key: str    
    model: str
