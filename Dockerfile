# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

# Instala dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia y compila dependencias
COPY requirements.txt .
RUN pip install --user --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Crea usuario no-root
RUN useradd -m -u 1000 appuser

# Copia dependencias compiladas del builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copia código fuente
COPY --chown=appuser:appuser . .

# Configura PATH para pip packages instalados con --user
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_INPUT=1

# Cambia a usuario no-root
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
