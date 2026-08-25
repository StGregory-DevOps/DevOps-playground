FROM python:3.12-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt


FROM python:3.12-slim

WORKDIR /app

RUN useradd -m appuser
COPY --from=builder --chown=appuser:appuser /opt/venv/ /opt/venv/
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

USER appuser

CMD ["python", "worker.py"]
