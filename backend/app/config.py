import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:password123@127.0.0.1:5433/asistencia_db"
    BLYNK_AUTH_TOKEN: str = "-8ChkPCYpa0re-gcEiM69azP-AKHJJoN"
    BLYNK_SERVER_URL: str = "https://blynk.cloud/external/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        extra = "ignore"

settings = Settings()
