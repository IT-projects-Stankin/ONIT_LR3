FROM python:3.12-slim AS base

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM base AS test

COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt

COPY main.py .
COPY tests/ tests/
RUN python -m pytest -q tests


FROM base AS runtime
ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION

COPY main.py .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
