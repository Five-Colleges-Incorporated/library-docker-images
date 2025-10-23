# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.14
ARG PYTHON=registry.hub.docker.com/library/python:${PYTHON_VERSION}-slim
FROM ${PYTHON} AS python

FROM python AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
ARG REQUIREMENTS_FILE=requirements.lock
RUN --mount=type=bind,source=${REQUIREMENTS_FILE},target=requirements.txt <<UV
set -eux pipefail
uv venv --no-managed-python
uv pip install --no-cache -r requirements.txt
UV


FROM python AS setae-api
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ADD ./setae-api/app /app
ARG FASTAPI_PORT=80
CMD [".venv/bin/fastapi", "run", "main.py", "--port", "80"]
