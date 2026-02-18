FROM python:3.12-slim

# 1. Crear grupo y usuario de sistema sin privilegios
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# 2. Instalar dependencias como root
COPY apps/operator_console/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 3. Copiar código y asignar permisos al usuario no-root
COPY apps/operator_console /app/apps/operator_console
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# 4. Cambiar al usuario seguro
USER appuser

ENV OPERATOR_DATA_DIR=/app/data
EXPOSE 8088

# 5. Usar exec form para que las señales de parada (SIGTERM) lleguen a la app
CMD ["uvicorn", "apps.operator_console.app.main:app", "--host", "0.0.0.0", "--port", "8088"]
