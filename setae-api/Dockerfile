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
ADD ./setae-api/app /app
ADD ./alma-rest-item.xsl ./prefix-suffix.csv /app/

FROM python AS setae-api
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=app /app /app

ENV BARCODE_REGEX='^(^(^\d{2,}\*-[A-Z]{2,3}$)|(((\d{8,}\*-?)|([-`:% \+\.\(\)\/\\a-zà-üA-ZÀ-Ü0-9]+))(=?[a-zA-Z]{2,3})?$))$'
CMD [".venv/bin/fastapi", "run", "main.py", "--port", "80"]
