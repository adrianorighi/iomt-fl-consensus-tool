FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN true  # No dependencies to install (stdlib only)

COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

ENV PYTHONPATH=/app/src

CMD ["python", "scripts/run_demo.py", "--config", "config/scenario_baseline.json"]