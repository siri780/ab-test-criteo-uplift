# Reproduce the whole Criteo A/B analysis with one command.
# Build:  docker build -t criteo-ab .
# Run:    docker run --rm -v "$PWD/data:/app/data" -v "$PWD/results:/app/results" criteo-ab
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY analysis/ analysis/
COPY run_all.sh .
RUN chmod +x run_all.sh

CMD ["./run_all.sh"]
