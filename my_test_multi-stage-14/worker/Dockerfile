# ---- builder (уже собрано разработчиком) ----
FROM python:3.12-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- runtime — допиши сам ----


FROM python:3.12-slim 
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY --chown=appuser:appuser . .
USER appuser
CMD ["python", "main.py"]