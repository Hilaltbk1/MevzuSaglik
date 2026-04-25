#!/bin/bash

# Test 1: Cloudflare Worker üzerinden
echo "=== TEST 1: Cloudflare Worker üzerinden ==="
curl -X POST "https://mevzusaglik.mevzusaglik.workers.dev/session/create_session" \
  -H "X-API-Key: 5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af" \
  -H "Content-Type: application/json" \
  -d '{"user_name": "test"}' \
  -v

echo -e "\n\n=== TEST 2: Doğrudan Hugging Face Spaces'e ==="
curl -X POST "https://hilal1-mevzusaglik.hf.space/session/create_session" \
  -H "X-API-Key: 5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af" \
  -H "Content-Type: application/json" \
  -d '{"user_name": "test"}' \
  -v
