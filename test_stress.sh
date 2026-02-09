#!/bin/bash
# STRESS TEST: Sistemin CPU throttling ve deduplication'ını zorla
# Bu test çok sayıda alert göndererek sistemi test eder

COLLECTOR_URL="http://localhost:8080/api/v1/alerts"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "🔥 STRESS TEST: Sistemin Sınırlarını Zorla"
echo "==========================================="
echo ""

# ==================== PHASE 1: Alert Spam (20 Alert) ====================
echo "📍 PHASE 1: Alert Spam - Aynı alert 20 kez (19'u duplicate olmalı)"
for i in {1..20}; do
  curl -s -X POST $COLLECTOR_URL \
    -H "Content-Type: application/json" \
    -d "[{
      \"labels\": {
        \"alertname\": \"HighCPUUsage\",
        \"severity\": \"warning\",
        \"instance\": \"app-server-1:9090\",
        \"job\": \"node-exporter\"
      },
      \"annotations\": {
        \"description\": \"CPU usage is at 85% on app-server-1. Process load average: 12.5 (8 cores). Top processes: java (45%), mysql (25%), nginx (15%). Memory usage: 28GB/32GB.\"
      },
      \"startsAt\": \"$TIMESTAMP\"
    }]" > /dev/null

  echo -n "."
  sleep 0.2
done
echo ""
echo "✅ 20 alert gönderildi (Expected: 1 LLM, 19 duplicate)"
echo ""

sleep 2

# ==================== PHASE 2: Farklı Serverlar (5 Alert) ====================
echo "📍 PHASE 2: Farklı Serverlar - 5 farklı server aynı alert (5 unique)"
for server in 1 2 3 4 5; do
  curl -s -X POST $COLLECTOR_URL \
    -H "Content-Type: application/json" \
    -d "[{
      \"labels\": {
        \"alertname\": \"DiskSpaceWarning\",
        \"severity\": \"warning\",
        \"instance\": \"db-server-$server:9100\",
        \"job\": \"node-exporter\"
      },
      \"annotations\": {
        \"description\": \"Disk usage is at 82% on db-server-$server. Partition: /var/lib/mysql (450GB/550GB used). Growth rate: 2GB/hour. ETA to 90%: 18 hours. Top consumers: mysql-bin logs (120GB), slow-query logs (35GB).\"
      },
      \"startsAt\": \"$TIMESTAMP\"
    }]" > /dev/null

  echo "  ✓ db-server-$server alert sent"
  sleep 0.5
done
echo "✅ 5 server alert gönderildi (Expected: 5 LLM)"
echo ""

sleep 2

# ==================== PHASE 3: Escalation Chain ====================
echo "📍 PHASE 3: Escalation Chain - WARNING → CRITICAL → WARNING"

# WARNING
curl -s -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "PostgreSQLConnections",
      "severity": "warning",
      "instance": "postgres-master:5432",
      "job": "postgresql"
    },
    "annotations": {
      "description": "PostgreSQL connections at 75% on postgres-master. Current: 375/500 connections. Connection pool saturation. Idle connections: 45. Active queries: 330. Waiting: 12. Average query time: 250ms."
    },
    "startsAt": "'$TIMESTAMP'"
  }]' > /dev/null
echo "  ✓ WARNING sent"
sleep 2

# Duplicate WARNING
curl -s -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "PostgreSQLConnections",
      "severity": "warning",
      "instance": "postgres-master:5432",
      "job": "postgresql"
    },
    "annotations": {
      "description": "PostgreSQL connections at 76% on postgres-master."
    },
    "startsAt": "'$TIMESTAMP'"
  }]' > /dev/null
echo "  ✓ Duplicate WARNING sent (should skip)"
sleep 2

# ESCALATION: CRITICAL
curl -s -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "PostgreSQLConnections",
      "severity": "critical",
      "instance": "postgres-master:5432",
      "job": "postgresql"
    },
    "annotations": {
      "description": "CRITICAL: PostgreSQL connection limit REACHED on postgres-master! Current: 500/500 connections (100%). New connection attempts FAILING. Application errors: connection timeout. Connection wait queue: 45 queries waiting. System rejecting new connections!"
    },
    "startsAt": "'$TIMESTAMP'"
  }]' > /dev/null
echo "  ✓ ESCALATION: CRITICAL sent 🔥"
sleep 2

# Duplicate CRITICAL
for i in {1..5}; do
  curl -s -X POST $COLLECTOR_URL \
    -H "Content-Type: application/json" \
    -d '[{
      "labels": {
        "alertname": "PostgreSQLConnections",
        "severity": "critical",
        "instance": "postgres-master:5432",
        "job": "postgresql"
      },
      "annotations": {
        "description": "CRITICAL: PostgreSQL still at 500/500 connections."
      },
      "startsAt": "'$TIMESTAMP'"
    }]' > /dev/null
  echo -n "."
  sleep 0.5
done
echo ""
echo "  ✓ 5 Duplicate CRITICAL sent (should skip)"
sleep 3

# RECOVERY: WARNING
curl -s -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "PostgreSQLConnections",
      "severity": "warning",
      "instance": "postgres-master:5432",
      "job": "postgresql"
    },
    "annotations": {
      "description": "PostgreSQL connections RECOVERING on postgres-master. Admin killed 150 idle connections. Current: 280/500 connections (56%). Connection wait queue cleared. New connections accepting. Application errors resolved. System stabilizing."
    },
    "startsAt": "'$TIMESTAMP'"
  }]' > /dev/null
echo "  ✓ RECOVERY: WARNING sent ⭐"

echo ""
echo "✅ Escalation chain complete"
echo ""

# ==================== SUMMARY ====================
echo "=========================================="
echo "📊 STRESS TEST SUMMARY"
echo "=========================================="
echo ""
echo "Total Alerts Sent: ~33"
echo ""
echo "Expected Results:"
echo "  - Alert Spam: 20 alerts → 1 LLM (19 duplicates)"
echo "  - Different Servers: 5 alerts → 5 LLM (5 unique)"
echo "  - Escalation Chain: 8 alerts → 3 LLM (1 first + 1 escalation + 1 recovery)"
echo ""
echo "Expected LLM Calls: 9"
echo "Expected Duplicates: 24"
echo "Expected Dedup Rate: 73%"
echo ""
echo "⏳ Wait 2-3 minutes for Ollama to process..."
echo "Then check:"
echo "  - Dashboard: http://localhost:3000"
echo "  - Active Alerts should be ~33"
echo "  - LLM Analyses should be ~9"
echo "  - Duplicates Skipped should be ~24"
echo ""
