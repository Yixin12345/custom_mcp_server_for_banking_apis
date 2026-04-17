FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    openjdk-21-jdk \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright
RUN playwright install chromium && playwright install-deps chromium

COPY . .

CMD uvicorn asgi:app --host 0.0.0.0 --port $PORT