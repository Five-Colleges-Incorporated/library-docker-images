# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.14
ARG PYTHON=registry.hub.docker.com/library/python:${PYTHON_VERSION}-slim
FROM ${PYTHON} AS python

FROM python AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
ARG REQUIREMENTS_FILE=requirements.lock
RUN --mount=type=bind,source=${REQUIREMENTS_FILE},target=requirements.txt <<UV
#! /usr/bin/env bash
set -euo pipefail
uv venv --no-managed-python
uv pip install --no-cache -r requirements.txt
UV


FROM python AS setae-api
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ADD ./setae-api/app /app

ENV BARCODE_REGEX='^(^(^\d{2,}\*-[A-Z]{2,3}$)|(((\d{8,}\*-?)|([-`:% \+\.\(\)\/\\a-zà-üA-ZÀ-Ü0-9]+))(=?[a-zA-Z]{2,3})?$))$'
HEALTHCHECK --interval=15m CMD curl -f http://localhost/ || exit 1
CMD [".venv/bin/fastapi", "run", "main.py", "--port", "80"]
