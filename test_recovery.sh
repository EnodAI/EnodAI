#!/bin/bash
# RECOVERY TEST: Alert'in düzelmesini test et
# CRITICAL → WARNING geçişinde "recovery" analizi yapılmalı

COLLECTOR_URL="http://localhost:8080/api/v1/alerts"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "⭐ RECOVERY TEST: Alert Düzelme Senaryosu"
echo "=========================================="
echo ""

# ==================== PHASE 1: CRITICAL Alert ====================
echo "📍 PHASE 1: CRITICAL Alert Gönder"
curl -s -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d "[{
    \"labels\": {
      \"alertname\": \"HighMemoryUsage\",
      \"severity\": \"critical\",
      \"instance\": \"app-server-99:9090\",
      \"job\": \"node-exporter\"
    },
    \"annotations\": {
      \"description\": \"CRITICAL: Memory usage at 95% on app-server-99! Used: 30.4GB/32GB. OOM killer activated. Killed 3 processes in last 5 minutes: java (PID 1234), python (PID 5678), node (PID 9012). Swap usage: 8GB/8GB (100%). System becoming unstable!\"
    },
    \"startsAt\": \"$TIMESTAMP\"
  }]" > /dev/null

echo "✅ CRITICAL alert sent"
echo ""
echo "⏳ Waiting 60 seconds for LLM to analyze..."
sleep 60

# ==================== PHASE 2: WARNING Alert (Recovery) ====================
echo ""
echo "📍 PHASE 2: WARNING Alert Gönder (Recovery)"
TIMESTAMP2=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

curl -s -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d "[{
    \"labels\": {
      \"alertname\": \"HighMemoryUsage\",
      \"severity\": \"warning\",
      \"instance\": \"app-server-99:9090\",
      \"job\": \"node-exporter\"
    },
    \"annotations\": {
      \"description\": \"Memory usage RECOVERING on app-server-99. Admin restarted memory-leaking services. Current: 18GB/32GB (56%). OOM killer no longer active. Swap freed: 2GB/8GB used. Top processes normal. System stabilizing.\"
    },
    \"startsAt\": \"$TIMESTAMP2\"
  }]" > /dev/null

echo "✅ WARNING (recovery) alert sent ⭐"
echo ""
echo "⏳ Waiting 60 seconds for LLM to analyze recovery..."
sleep 60

# ==================== PHASE 3: Check Results ====================
echo ""
echo "=========================================="
echo "📊 RECOVERY TEST RESULTS"
echo "=========================================="
echo ""

docker compose exec -T postgresql psql -U enod_user -d enod_monitoring -c "
SELECT
  a.alert_name,
  a.severity,
  a.labels->>'instance' as instance,
  r.metadata->>'analysis_reason' as reason,
  SUBSTRING(a.annotations->>'description', 1, 80) as description_preview
FROM alerts a
INNER JOIN ai_analysis_results r ON a.id = r.alert_id
WHERE a.alert_name = 'HighMemoryUsage'
  AND a.labels->>'instance' = 'app-server-99:9090'
ORDER BY a.created_at;
" 2>/dev/null

echo ""
echo "🎯 EXPECTED RESULTS:"
echo "  - First alert (CRITICAL): analysis_reason = 'first_occurrence'"
echo "  - Second alert (WARNING): analysis_reason = 'recovery' ⭐"
echo ""
echo "Check Dashboard: http://localhost:3000"
echo "  - Look for 'warning ⭐' in severity column (recovery indicator)"
echo ""
