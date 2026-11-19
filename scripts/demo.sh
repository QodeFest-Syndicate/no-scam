#!/usr/bin/env bash
# Walk through every endpoint. Start the server first:
#   uv run uvicorn src.service.main:app --port 8000
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"

echo "== health =="
curl -s "$BASE/health"; echo

echo "== meta =="
curl -s "$BASE/api/meta"; echo

echo "== scenarios =="
curl -s "$BASE/api/scenarios"; echo

echo "== assess: scam sample (rules) =="
curl -s -X POST "$BASE/api/assess?mode=rules" \
  -H "Content-Type: application/json" \
  -d '{"message":{"sender":"Amir (Son)","familiarContact":true,"channel":"whatsapp","text":"Hi Mak, it is Amir. Please pay RM500 right now at https://urgent-family-pay.example and do not call me."}}'; echo

echo "== assess: benign message =="
curl -s -X POST "$BASE/api/assess" \
  -H "Content-Type: application/json" \
  -d '{"message":{"sender":"Aisyah","familiarContact":true,"text":"See you at 3pm, call me later."}}'; echo

echo "== recovery: clicked link =="
curl -s -X POST "$BASE/api/recovery" \
  -H "Content-Type: application/json" \
  -d '{"incident":"clicked_link"}'; echo

echo "== recovery: sent money =="
curl -s -X POST "$BASE/api/recovery" \
  -H "Content-Type: application/json" \
  -d '{"incident":"sent_money"}'; echo
