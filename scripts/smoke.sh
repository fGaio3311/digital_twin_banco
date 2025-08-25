#!/usr/bin/env bash
set -e
API=${1:-http://localhost:8000}

echo "[*] ping"
curl -s $API/ping | jq

echo "[*] register"
curl -s -X POST $API/register -H "Content-Type: application/json" \
    -d '{"username":"smoke","password":"smoke"}' | jq

echo "[*] login"
TOKEN=$(curl -s -X POST $API/token -d "username=smoke&password=smoke" | jq -r .access_token)
echo "TOKEN=$TOKEN"

echo "[*] balance"
curl -s $API/balance -H "Authorization: Bearer $TOKEN" | jq
