FROM python:3.11-slim

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код API и базы данных
COPY api/ ./api/
COPY database/ ./database/

# Статика фронтенда
COPY webapp_dist/ ./webapp_dist/

# Создаём папку для данных
RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
