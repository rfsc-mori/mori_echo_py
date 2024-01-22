# Build args
ARG UID=1000
ARG GID=1000
ARG USERNAME=rfsc

# Base image
FROM python:3.12-alpine as base

# Create non-root user
ARG UID
ARG GID
ARG USERNAME

RUN addgroup \
    --system \
    --gid ${GID} \
    ${USERNAME}

RUN adduser \
    --system \
    --disabled-password \
    --shell /bin/sh \
    --uid ${UID} \
    --ingroup ${USERNAME} \
    ${USERNAME}

# Switch to non-root user
USER ${USERNAME}

# Set workdir
WORKDIR /usr/local/mori_echo_py

# Setup virtual env
RUN python -m venv .venv
ENV VIRTUAL_ENV="/usr/local/mori_echo_py/.venv" \
    PATH="/usr/local/mori_echo_py/.venv/bin:$PATH"

# Install poetry
RUN pip install poetry

# Install dependencies
COPY ./pyproject.toml ./poetry.lock ./
RUN poetry run pip install --upgrade pip setuptools
RUN poetry install --no-root --no-dev

# Copy project
COPY . ./

# Run linters
FROM base as lint
RUN poetry install --only linter --no-root --no-dev

RUN poetry run mypy .
RUN poetry run ruff check .

RUN touch .lint_success

# Run tests
FROM base as test
RUN poetry install --with test --no-root

RUN poetry run tox

RUN touch .test_success

# Install application
FROM base as build
# Require success from lint and test stages
COPY --from=lint /usr/local/mori_echo_py/.lint_success ./
COPY --from=test /usr/local/mori_echo_py/.test_success ./

RUN pip install .

# Final step
FROM python:3.12-alpine as runtime

LABEL org.opencontainers.image.source=https://github.com/rfsc-mori/mori_echo_py

# Use non-root user
ARG UID
ARG GID
ARG USERNAME

RUN addgroup \
    --system \
    --gid ${GID} \
    ${USERNAME}

RUN adduser \
    --system \
    --disabled-password \
    --no-create-home \
    --shell /bin/sh \
    --uid ${UID} \
    --ingroup ${USERNAME} \
    ${USERNAME}

# Setup virtual environment
WORKDIR /usr/local/mori_echo_py
COPY --from=build /usr/local/mori_echo_py/.venv .venv

ENV VIRTUAL_ENV="/usr/local/mori_echo_py/.venv" \
    PATH="/usr/local/mori_echo_py/.venv/bin:$PATH"

RUN chown -R root:root .

# Run application as non-root user
USER ${USERNAME}

ENTRYPOINT [ "MoriEchoPy" ]
