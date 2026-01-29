# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11
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
ADD ./Patron-Transform /app
ADD ./do_main.py /app/
ADD ./config.ini /app/.env
RUN mkdir /app/output

FROM python AS folio_data_import
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=app /app /app

CMD [".venv/bin/python", "./do_main.py"]
