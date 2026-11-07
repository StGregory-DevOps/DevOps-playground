FROM python:3.12-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
COPY app ./app 
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
