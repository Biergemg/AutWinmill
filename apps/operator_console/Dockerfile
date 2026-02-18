# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY apps/operator_console/requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final
FROM python:3.12-slim

WORKDIR /app

# 1. Crear grupo y usuario de sistema sin privilegios
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 2. Instalar dependencias desde wheels
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# 3. Copiar código y asignar permisos al usuario no-root
COPY apps/operator_console /app/apps/operator_console
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# 4. Cambiar al usuario seguro
USER appuser

ENV OPERATOR_DATA_DIR=/app/data
EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8088/health').read()" || exit 1

# 5. Usar exec form para que las señales de parada (SIGTERM) lleguen a la app
CMD ["uvicorn", "apps.operator_console.app.main:app", "--host", "0.0.0.0", "--port", "8088"]