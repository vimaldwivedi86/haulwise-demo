#!/bin/bash
set -e

python -m db_migrate
python -m db_seed

exec uvicorn main:app --host 0.0.0.0 --port 8000
