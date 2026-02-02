import hmac
import hashlib
import json
from urllib.parse import parse_qsl
from typing import Optional
from fastapi import Request, HTTPException
from api.config import api_config


def verify_telegram_auth(init_data: str) -> Optional[int]:
    """
    Проверяет подпись данных от Telegram WebApp
    
    Args:
        init_data: Строка initData от Telegram WebApp
        
    Returns:
        user_id если авторизация успешна, иначе None
    """
    if not init_data:
        return None
    
    try:
        # Парсим данные
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        
        # Получаем hash
        received_hash = parsed.pop('hash', None)
        if not received_hash:
            return None
        
        # Сортируем и формируем строку для проверки
        data_check_string = '\n'.join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )
        
        # Создаём секретный ключ
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=api_config.BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Вычисляем hash
        computed_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Сравниваем
        if not hmac.compare_digest(computed_hash, received_hash):
            return None
        
        # Извлекаем user_id
        user_data = parsed.get('user', '{}')
        user = json.loads(user_data)
        
        return user.get('id')
    
    except Exception as e:
        print(f"Auth error: {e}")
        return None


async def get_user_id(request: Request) -> int:
    """
    Dependency для получения user_id из запроса
    
    Использование:
        @app.get("/tasks")
        async def get_tasks(user_id: int = Depends(get_user_id)):
            ...
    """
    # Получаем initData из заголовка Authorization
    auth_header = request.headers.get('Authorization', '')
    
    # Для разработки: если DEBUG, можно передать user_id напрямую
    if api_config.DEBUG:
        debug_user = request.headers.get('X-Debug-User-Id')
        if debug_user:
            return int(debug_user)
    
    # Проверяем авторизацию Telegram
    user_id = verify_telegram_auth(auth_header)
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid Telegram authorization"
        )
    
    return user_id


class TelegramAuthMiddleware:
    """
    Middleware для проверки авторизации Telegram
    (альтернатива Depends для глобальной проверки)
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Пропускаем статику и health-check
            path = scope.get("path", "")
            if path.startswith("/api/"):
                # Здесь можно добавить глобальную проверку
                pass
        
        await self.app(scope, receive, send)
