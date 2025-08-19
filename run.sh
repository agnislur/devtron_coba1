#!/bin/sh
echo "Sending Create VNF Request to Tacker POC..."

# Ambil URL dari Environment Variable agar tidak hardcoded
# Anda akan setting TACKER_URL ini di langkah pipeline nanti
curl -X POST "$TACKER_URL" \
     -H "Content-Type: application/json" \
     -d '{
           "vnf_name": "my-first-vnf",
           "description": "Created from Devtron pipeline"
         }'

echo "Request sent."
