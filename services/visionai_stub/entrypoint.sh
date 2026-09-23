#!/bin/bash
set -e

# Plain HTTP listener.
uvicorn main:app --host 0.0.0.0 --port 8100 &

# TLS listener on a self-signed cert.
uvicorn main:app --host 0.0.0.0 --port 8143 \
  --ssl-keyfile /certs/key.pem --ssl-certfile /certs/cert.pem &

wait -n
