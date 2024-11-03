FROM python:3.12.6

WORKDIR /gc

RUN python3 -m venv .venv
RUN .venv/bin/pip install -U pip setuptools
RUN .venv/bin/pip install poetry

COPY pyproject.toml poetry.lock ./
RUN .venv/bin/poetry install

COPY src/common ./common
COPY src/registry ./registry
COPY src/collector ./collector
COPY src/producer ./producer

ENV PATH="$PATH:/gc/.venv/bin"