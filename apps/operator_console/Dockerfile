FROM python:3.12-slim

WORKDIR /app

COPY apps/operator_console/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/operator_console /app/apps/operator_console

ENV OPERATOR_DATA_DIR=/app/data
RUN mkdir -p /app/data

EXPOSE 8088

CMD ["uvicorn", "apps.operator_console.app.main:app", "--host", "0.0.0.0", "--port", "8088"]

