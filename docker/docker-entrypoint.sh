#!/bin/bash
set -e

PORT=${PORT:-5000}

gunicorn --workers=5 --bind=0.0.0.0:${PORT} app:main
