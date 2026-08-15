FROM python:3.11-slim AS builder

WORKDIR /deps

RUN python -m venv /opt/venv/
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

RUN useradd -m produser
COPY --from=builder --chown=produser:produser /opt/venv/ /opt/venv/
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY --chown=produser:produser app/ app/
RUN mkdir -p /app/db && chown -R produser:produser /app/db/
ENV DATABASE_URL=sqlite:////app/db/products.db

EXPOSE 6800

USER produser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6800"]


