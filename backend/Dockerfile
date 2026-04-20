FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (Docker layer caching)
COPY pyproject.toml .
RUN pip install uv && uv pip install --system \
    fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic \
    pydantic pydantic-settings redis python-jose[cryptography] \
    passlib[bcrypt] python-multipart openpyxl docker pyyaml httpx

# Copy application code
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
