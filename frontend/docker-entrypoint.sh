#!/bin/sh
# Rewrite the backend proxy target at container start.
# BACKEND_URL defaults to "http://backend:8000" (Docker Compose).
BACKEND_URL="${BACKEND_URL:-http://backend:8000}"

sed -i "s|http://backend:8000|${BACKEND_URL}|g" /etc/nginx/conf.d/default.conf

exec nginx -g "daemon off;"
