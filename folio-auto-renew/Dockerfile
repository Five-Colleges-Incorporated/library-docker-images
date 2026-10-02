# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.15-rc
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

FROM python AS folio-auto-renew
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ADD ./do_main.py /app/

CMD [".venv/bin/python", "./do_main.py"]
