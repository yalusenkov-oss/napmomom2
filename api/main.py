from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.config import api_config
from api.routes import tasks_router
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события приложения"""
    # Startup
    await init_db()
    print("✅ API сервер запущен")
    
    yield
    
    # Shutdown
    print("⏹ API сервер остановлен")


# Создаём приложение
app = FastAPI(
    title="TaskBot API",
    description="API для Telegram Mini App TaskBot",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты API
app.include_router(tasks_router)


# Health check
@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "ok", "service": "TaskBot API"}


# Статика для Mini App (production: проверяем несколько местоположений)
# Возможные варианты раздачи статики:
# - webapp_dist/ (копия собранного фронтенда из webapp2 -> deploy_railway/webapp_dist)
# - webapp/dist (стандартный путь для старого webapp)
# - webapp/ (dev fallback)
webapp_dist_candidates = [
    Path(__file__).parent.parent / "webapp_dist",
    Path(__file__).parent.parent / "webapp" / "dist",
    Path(__file__).parent.parent / "webapp",
]

for candidate in webapp_dist_candidates:
    if candidate.exists():
        print(f"📁 Служу статику из: {candidate}")
        app.mount("/", StaticFiles(directory=candidate, html=True), name="webapp")
        break


# Для запуска напрямую
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
