#!/bin/bash
# ANOMALY DETECTION TEST: Metricler göndererek anomaly detection'ı test et
# Normal metricler + Anormal metricler gönder, sistemi test et

COLLECTOR_URL="http://localhost:8080/api/v1/metrics"

echo "🤖 ANOMALY DETECTION TEST"
echo "========================="
echo ""

# ==================== PHASE 1: Normal Baseline ====================
echo "📍 PHASE 1: Normal Metricler (Baseline oluştur)"
echo "  Sending 10 normal CPU metrics..."

for i in {1..10}; do
  cpu_value=$(echo "scale=2; 35 + $RANDOM % 10" | bc)
  curl -s -X POST $COLLECTOR_URL \
    -H "Content-Type: application/json" \
    -d "{
      \"metric_name\": \"cpu_usage_percent\",
      \"metric_value\": $cpu_value,
      \"labels\": {
        \"instance\": \"app-server-1\",
        \"job\": \"node-exporter\"
      }
    }" > /dev/null
  echo -n "."
  sleep 0.5
done
echo ""
echo "✅ Normal metrics sent (CPU: 35-45%)"
echo ""

sleep 2

# ==================== PHASE 2: Anomaly - CPU Spike ====================
echo "📍 PHASE 2: ANOMALY - CPU Spike!"
echo "  Sending abnormal CPU metric (95%)..."

curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "cpu_usage_percent",
    "metric_value": 95.5,
    "labels": {
      "instance": "app-server-1",
      "job": "node-exporter"
    }
  }'
echo ""
echo "✅ Anomaly sent (CPU: 95.5% - should be detected!)"
echo ""

sleep 2

# ==================== PHASE 3: Normal Memory Baseline ====================
echo "📍 PHASE 3: Normal Memory Metricler"
echo "  Sending 10 normal memory metrics..."

for i in {1..10}; do
  mem_value=$(echo "scale=2; 8000 + $RANDOM % 1000" | bc)
  curl -s -X POST $COLLECTOR_URL \
    -H "Content-Type: application/json" \
    -d "{
      \"metric_name\": \"memory_used_mb\",
      \"metric_value\": $mem_value,
      \"labels\": {
        \"instance\": \"db-server-1\",
        \"job\": \"node-exporter\"
      }
    }" > /dev/null
  echo -n "."
  sleep 0.5
done
echo ""
echo "✅ Normal metrics sent (Memory: 8000-9000MB)"
echo ""

sleep 2

# ==================== PHASE 4: Anomaly - Memory Leak ====================
echo "📍 PHASE 4: ANOMALY - Memory Leak!"
echo "  Sending abnormal memory metric (28GB)..."

curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "memory_used_mb",
    "metric_value": 28672,
    "labels": {
      "instance": "db-server-1",
      "job": "node-exporter"
    }
  }'
echo ""
echo "✅ Anomaly sent (Memory: 28GB - should be detected!)"
echo ""

sleep 2

# ==================== PHASE 5: Normal Response Time Baseline ====================
echo "📍 PHASE 5: Normal Response Time Metricler"
echo "  Sending 10 normal response time metrics..."

for i in {1..10}; do
  resp_value=$(echo "scale=0; 50 + $RANDOM % 30" | bc)
  curl -s -X POST $COLLECTOR_URL \
    -H "Content-Type: application/json" \
    -d "{
      \"metric_name\": \"api_response_time_ms\",
      \"metric_value\": $resp_value,
      \"labels\": {
        \"instance\": \"api-gateway-1\",
        \"endpoint\": \"/api/users\"
      }
    }" > /dev/null
  echo -n "."
  sleep 0.5
done
echo ""
echo "✅ Normal metrics sent (Response: 50-80ms)"
echo ""

sleep 2

# ==================== PHASE 6: Anomaly - Slow Response ====================
echo "📍 PHASE 6: ANOMALY - Slow Response!"
echo "  Sending abnormal response time (5000ms)..."

curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "api_response_time_ms",
    "metric_value": 5000,
    "labels": {
      "instance": "api-gateway-1",
      "endpoint": "/api/users"
    }
  }'
echo ""
echo "✅ Anomaly sent (Response: 5000ms - should be detected!)"
echo ""

# ==================== SUMMARY ====================
echo ""
echo "=========================================="
echo "📊 ANOMALY DETECTION TEST SUMMARY"
echo "=========================================="
echo ""
echo "Metrics Sent:"
echo "  ✓ CPU: 10 normal + 1 anomaly (95%)"
echo "  ✓ Memory: 10 normal + 1 anomaly (28GB)"
echo "  ✓ Response Time: 10 normal + 1 anomaly (5000ms)"
echo ""
echo "Total Metrics: 33"
echo "Total Anomalies Expected: 3"
echo ""
echo "⏳ Wait 1-2 minutes for anomaly detection..."
echo ""
echo "Check Results:"
echo "  1. Dashboard: http://localhost:3000"
echo "     - 🤖 AI Anomalies Detected should show 3"
echo ""
echo "  2. Database Query:"
echo "     docker compose exec -T postgresql psql -U enod_user -d enod_monitoring -c \"SELECT COUNT(*) FROM metrics WHERE is_anomaly = TRUE;\""
echo ""
echo "  3. View Anomalies:"
echo "     docker compose exec -T postgresql psql -U enod_user -d enod_monitoring -c \"SELECT metric_name, metric_value, labels FROM metrics WHERE is_anomaly = TRUE;\""
echo ""
echo "🎯 SUCCESS CRITERIA:"
echo "  - Dashboard shows 3 anomalies"
echo "  - CPU spike (95%) detected"
echo "  - Memory leak (28GB) detected"
echo "  - Slow response (5000ms) detected"
echo ""
