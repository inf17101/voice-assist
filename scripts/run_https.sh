#!/usr/bin/env bash
set -euo pipefail

# Generates a self-signed certificate for localhost (if missing) and runs uvicorn with HTTPS.
# Usage: ./scripts/run_https.sh [uvicorn args]

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$ROOT_DIR/.certs"
mkdir -p "$CERT_DIR"
KEY="$CERT_DIR/key.pem"
CERT="$CERT_DIR/cert.pem"

if [ ! -f "$KEY" ] || [ ! -f "$CERT" ]; then
  echo "Generating self-signed cert for localhost (valid 1 year)..."
  # Create cert with SAN for localhost and 127.0.0.1 (requires OpenSSL >= 1.1.1 for -addext)
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout "$KEY" -out "$CERT" -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
  echo "Created $CERT and $KEY"
else
  echo "Using existing certs: $CERT and $KEY"
fi

echo "Running uvicorn with TLS on 0.0.0.0:8000"
exec uv run uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile="$KEY" --ssl-certfile="$CERT" "$@"
