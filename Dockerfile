FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# psycopg2-binary and oracledb need libpq/libaio at runtime; build-essential
# covers any source-built wheel in requirements.txt.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libaio1t64 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source is bind-mounted by compose in development; this COPY only matters if
# the image is ever built and run without the mount.
COPY . .
