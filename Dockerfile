FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck and debugging
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV LLM_API_BASE=http://mock-llm:8080
ENV LLM_API_KEY=mock-key-not-needed

CMD ["tail", "-f", "/dev/null"]
