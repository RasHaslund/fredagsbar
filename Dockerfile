FROM python:3.12-slim

# Gør uv tilgængelig til installation af projektets afhængigheder.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Afhængigheder installeres separat, så laget kan genbruges ved kodeændringer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Den lokale .venv udelades via .dockerignore.
COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "api.py"]