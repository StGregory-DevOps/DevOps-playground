# ---- builder (уже собрано разработчиком) ----
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app


FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
COPY --from=builder --chown=appuser:appuser /app/app ./app
COPY --chown=appuser:appuser . . 
ENV PATH="/opt/venv/bin:$PATH"
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
