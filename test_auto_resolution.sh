#!/bin/bash
# AUTO-RESOLUTION TEST: Recovery tespit edilince eski alert resolved olmalı

COLLECTOR_URL="http://localhost:8080/api/v1/alerts"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "🔄 AUTO-RESOLUTION TEST"
echo "======================="
echo ""

# CRITICAL alert
echo "📍 Sending CRITICAL alert..."
curl -s -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d "[{
    \"labels\": {
      \"alertname\": \"DatabaseConnections\",
      \"severity\": \"critical\",
      \"instance\": \"db-test-1:5432\",
      \"job\": \"postgresql\"
    },
    \"annotations\": {
      \"description\": \"CRITICAL: PostgreSQL connections at 100% on db-test-1! Connection limit reached: 500/500. New connections FAILING!\"
    },
    \"startsAt\": \"$TIMESTAMP\"
  }]" > /dev/null
echo "✅ CRITICAL sent"
sleep 60

echo ""
echo "📍 Sending WARNING (recovery) alert..."
TIMESTAMP2=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
curl -s -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d "[{
    \"labels\": {
      \"alertname\": \"DatabaseConnections\",
      \"severity\": \"warning\",
      \"instance\": \"db-test-1:5432\",
      \"job\": \"postgresql\"
    },
    \"annotations\": {
      \"description\": \"PostgreSQL connections RECOVERING on db-test-1. Admin killed idle connections. Current: 280/500 (56%). System stabilizing.\"
    },
    \"startsAt\": \"$TIMESTAMP2\"
  }]" > /dev/null
echo "✅ WARNING (recovery) sent"
sleep 60

echo ""
echo "=========================================="
echo "📊 AUTO-RESOLUTION RESULTS"
echo "=========================================="
echo ""

docker compose exec -T postgresql psql -U enod_user -d enod_monitoring -c "
SELECT
  SUBSTRING(id::text, 1, 8) as id,
  severity,
  status,
  CASE 
    WHEN ends_at::text LIKE '0001%' THEN 'Not set'
    ELSE to_char(ends_at, 'HH24:MI:SS')
  END as ends_at,
  to_char(created_at, 'HH24:MI:SS') as created_at
FROM alerts
WHERE alert_name = 'DatabaseConnections'
  AND labels->>'instance' = 'db-test-1:5432'
ORDER BY created_at;
" 2>/dev/null

echo ""
echo "🎯 EXPECTED:"
echo "  - CRITICAL alert: status = 'resolved', ends_at = set ✅"
echo "  - WARNING alert:  status = 'firing', ends_at = 'Not set'"
echo ""
echo "📊 Active Alerts count should DECREASE by 1"
echo ""
