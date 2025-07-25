# Base stage
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS uv-base

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dev 
FROM uv-base AS dev

# install all - includes dev
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv venv && . .venv/bin/activate && uv sync --frozen

ADD . /app

ENV PATH="/app/.venv/bin:$PATH"

CMD [ "python", "csse3200bot/__main__.py" ]

# Prd Builder
FROM uv-base AS prod-builder

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv build --verbose

ADD . /app

# Prod 
FROM python:3.13-slim-bookworm AS prod

WORKDIR /app

# Put the app back in
COPY --from=prod-builder /app /app

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8080

ENTRYPOINT ["python", "-m", "csse3200bot"]