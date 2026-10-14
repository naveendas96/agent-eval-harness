FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y make && pip install --no-cache-dir -e ".[dev,dashboard]"
ENV LLM_PROVIDER=mock
CMD ["make", "demo"]
