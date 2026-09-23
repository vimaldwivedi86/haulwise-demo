FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends openssl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /certs && \
    openssl req -x509 -newkey rsa:2048 -nodes \
      -keyout /certs/key.pem -out /certs/cert.pem -days 365 \
      -subj "/CN=visionai_stub.internal"

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8100 8143
CMD ["./entrypoint.sh"]
