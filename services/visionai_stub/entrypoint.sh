#!/bin/sh
set -e

# Plain HTTP listener: matches the main-branch client, which calls the
# vendor over http:// (seeded issue 1).
uvicorn main:app --host 0.0.0.0 --port 8100 &

# TLS listener on a self-signed cert: matches the compliant-branch client,
# which calls the vendor over https://.
uvicorn main:app --host 0.0.0.0 --port 8143 \
  --ssl-keyfile /certs/key.pem --ssl-certfile /certs/cert.pem &

wait -n
