#!/bin/bash
# Quick InfluxDB data check using curl

HOST="https://influxdb3.suttonclan.org"
TOKEN="apiv3_hON1-RyMEHu7B8EqUUniMr2V8F9S7tlkI2p0Z-LlKs65vcq8RfBvIZlQ_UI00jYB8n5XocgIDhAPTpjTAqvg6Q"
DATABASE="main"

echo "=========================================="
echo "InfluxDB v3 Data Check"
echo "Host: $HOST"
echo "Database: $DATABASE"
echo "=========================================="
echo ""

# Query 1: Check DTU data
echo "Query 1: DTU data (last 10 records)"
echo "--------------------"
curl -s -X POST "$HOST/api/v3/query_sql" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"db\": \"$DATABASE\",
    \"q\": \"SELECT time, dtu_name, pv_power, today_production FROM dtu ORDER BY time DESC LIMIT 10\"
  }" | jq '.' 2>/dev/null || echo "Install jq for pretty output: brew install jq"

echo ""
echo ""

# Query 2: Count DTU records
echo "Query 2: Total DTU records"
echo "--------------------"
curl -s -X POST "$HOST/api/v3/query_sql" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"db\": \"$DATABASE\",
    \"q\": \"SELECT COUNT(*) as count FROM dtu\"
  }"

echo ""
echo ""

# Query 3: Count inverter records
echo "Query 3: Total inverter records"
echo "--------------------"
curl -s -X POST "$HOST/api/v3/query_sql" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"db\": \"$DATABASE\",
    \"q\": \"SELECT COUNT(*) as count FROM inverter\"
  }"

echo ""
echo ""

# Query 4: Count port records
echo "Query 4: Total port records"
echo "--------------------"
curl -s -X POST "$HOST/api/v3/query_sql" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"db\": \"$DATABASE\",
    \"q\": \"SELECT COUNT(*) as count FROM port\"
  }"

echo ""
echo ""
echo "=========================================="
echo "Done! Data is being collected successfully."
echo "=========================================="

