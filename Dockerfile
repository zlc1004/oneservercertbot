FROM python:3.12-slim-bookworm

# 1. Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 2. Install System Dependencies & Docker CLI in one layer
# Using 'slim' version saves ~300MB, so we add curl/ca-certs back in
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.0.3.tgz | tar -xz \
    && mv docker/docker /usr/local/bin/ \
    # Create the CLI plugins directory
    && mkdir -p /usr/local/lib/docker/cli-plugins \
    # Download the Docker Compose binary (v2.27.1 as an example)
    && curl -SL https://github.com/docker/compose/releases/download/v2.27.1/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose \
    && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
    && rm -rf docker \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 4. Install App Requirements
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# 5. Copy App Code
COPY . .

CMD ["python", "bot.py"]