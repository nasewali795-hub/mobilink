from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./mobile_money_gateway.db"
    SECRET_KEY: str = "mobile_money_gateway_secret_key_2026_secure!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4

    GATEWAY_WS_SECRET: str = "gateway_ws_secret_2026"
    GATEWAY_HEARTBEAT_TIMEOUT: int = 30

    USSD_TIMEOUT_SECONDS: int = 120
    SMS_PARSE_TIMEOUT_SECONDS: int = 180
    QUEUE_PROCESS_INTERVAL: float = 1.0

    MAX_TRANSACTION_AMOUNT: float = 50000.0
    DEFAULT_FEE_PERCENTAGE: float = 2.5
    MIN_FEE: float = 10.0

    SIMULATION_MODE: bool = False
    SIMULATION_DELAY_SECONDS: float = 3.0
    SIMULATION_SUCCESS_RATE: float = 0.9

    class Config:
        env_file = ".env"


settings = Settings()
