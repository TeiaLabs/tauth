# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.4
ARG PYTHON_IMAGE_TAG=python:${PYTHON_VERSION}-slim
ARG VIRTUAL_ENV=/opt/env

# Base stage for common setup
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
WORKDIR /app

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
COPY ./docs/uv.lock ./docs/pyproject.toml ./

FROM build-base AS build-development
# Install project dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

FROM base AS development
# Copy the project's virtual environment from the build stage
COPY --from=build-development ${VIRTUAL_ENV} ${VIRTUAL_ENV}
# Copy necessary files
COPY ./tauth ./tauth
COPY ./docs ./docs
CMD [ "mkdocs", "serve", "--verbose", "--config-file", "./docs/mkdocs.yaml" ]

FROM build-base AS build-production
# Install project dependencies 
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev
COPY ./tauth ./tauth
COPY ./docs ./docs
RUN mkdocs build --verbose --config-file ./docs/mkdocs.yaml

FROM base as production
COPY --from=build-production /app/site /app/site
CMD [ "python", "-m", "http.server", "--directory", "/app/site" ]