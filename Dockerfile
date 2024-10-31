# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.4
ARG PYTHON_IMAGE_TAG=python:${PYTHON_VERSION}-slim
ARG VIRTUAL_ENV=/root/.venv

FROM ${PYTHON_IMAGE_TAG} AS base
ARG VIRTUAL_ENV
ENV \
    # Output goes straight away to stdout/stderr
    PYTHONBUFFERED=1 \
    # Do not write .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    # Set virtual environment path
    VIRTUAL_ENV=${VIRTUAL_ENV} \
    # Add virtual environment to path
    PATH="${VIRTUAL_ENV}/bin:${PATH}"
# Install git
RUN apt update && apt install -y git wget && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# Install OPA
RUN wget https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static -O opa \
    && chmod u+x ./opa

FROM base AS build-base
ENV \
    # Make uv compile Python code to .pyc files
    UV_COMPILE_BYTECODE=1 \
    # Set the default uv cache directory
    UV_CACHE_DIR=/root/.cache/uv \
    # Copy from the cache instead of linking since it's a mounted volume
    UV_LINK_MODE=copy \
    # Directory to use for the virtual environment
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV}
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
# Copy build dependency information
COPY ./uv.lock ./pyproject.toml ./

FROM build-base AS build-development
# Install project dependencies without installing the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project
# Install project itself
COPY ./.git ./.git
COPY ./tauth ./tauth
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

FROM build-base AS build-production
# Install project dependencies without installing the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev
# Install project itself
COPY ./.git ./.git
COPY ./tauth ./tauth
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

FROM base AS local
# Copy the project's virtual environment from the build stage
COPY --from=build-development ${VIRTUAL_ENV} ${VIRTUAL_ENV}
# Copy necessary files
COPY ./pyproject.toml ./pyproject.toml
COPY ./resources ./resources
COPY ./tauth ./tauth

FROM local AS development
CMD ["python", "-m", "tauth"]

FROM local AS debug
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "tauth"]

FROM local AS test
COPY ./tests ./tests
CMD ["python", "-m", "pytest", "-v"]

FROM base AS production
# Copy the project's virtual environment from the build stage
COPY --from=build-production ${VIRTUAL_ENV} ${VIRTUAL_ENV}
# Copy necessary files
COPY ./pyproject.toml ./pyproject.toml
COPY ./resources ./resources
COPY ./tauth ./tauth
CMD [ "python", "-m", "tauth" ]
