# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.14
ARG PYTHON=registry.hub.docker.com/library/python:${PYTHON_VERSION}-slim
FROM ${PYTHON} AS python

FROM python AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
ARG REQUIREMENTS_FILE=requirements.lock
ADD ${REQUIREMENTS_FILE} requirements.txt
RUN <<UV
#! /usr/bin/env bash
set -euo pipefail
uv venv --no-managed-python
uv pip install --no-cache -r requirements.txt
UV

FROM scratch AS app
ADD ./folio_data_import/src /app
ADD ./do_main.py /app/

FROM python AS folio_data_import
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=app /app /app

CMD ["python", "./do_main.py"]
