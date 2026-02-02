import os
from dotenv import load_dotenv

load_dotenv()


class APIConfig:
    """Конфигурация API"""
    
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    CORS_ORIGINS: list = [
        "https://web.telegram.org",
        "https://telegram.org",
        "*"
    ]
    
    # Явно проверяем DEBUG
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')


api_config = APIConfig()

# Отладка
print(f"🔧 DEBUG режим: {api_config.DEBUG}")
