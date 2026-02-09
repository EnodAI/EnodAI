#!/bin/bash
# Test Deduplication with Escalation & Recovery
# This demonstrates: First → Escalation → Duplicates → Recovery

COLLECTOR_URL="http://localhost:8080/api/v1/alerts"

echo "🧪 DEDUPLICATION TEST: Escalation + Recovery Scenario"
echo "===================================================="
echo ""

# ==================== PHASE 1: First Occurrence (WARNING) ====================
echo "📍 PHASE 1: First MongoDB Warning (14:00)"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "MongoDBSlowQueries",
      "severity": "warning",
      "instance": "mongo-prod-1:27017",
      "job": "mongodb"
    },
    "annotations": {
      "description": "MongoDB on mongo-prod-1 is experiencing slow queries. WiredTiger cache usage is at 75% (3.2GB of 4GB). Current connections: 450/500. Average query time increased from 50ms to 180ms in the last 5 minutes. Top slow query: db.users.find() taking 2.5s."
    },
    "startsAt": "2026-02-09T14:00:00Z"
  }]'

echo -e "\n✅ Sent: First occurrence (WARNING)"
echo "Expected: LLM Analysis #1 (reason: first_occurrence)"
echo ""
sleep 3

# ==================== PHASE 2: Duplicate (SAME WARNING) ====================
echo "📍 PHASE 2: Same Warning (14:05)"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "MongoDBSlowQueries",
      "severity": "warning",
      "instance": "mongo-prod-1:27017",
      "job": "mongodb"
    },
    "annotations": {
      "description": "MongoDB on mongo-prod-1 is experiencing slow queries. WiredTiger cache usage is at 76% (3.24GB of 4GB). Current connections: 455/500. Average query time: 185ms."
    },
    "startsAt": "2026-02-09T14:05:00Z"
  }]'

echo -e "\n✅ Sent: Duplicate warning"
echo "Expected: NO LLM (duplicate_same_severity)"
echo ""
sleep 3

# ==================== PHASE 3: Escalation (WARNING → CRITICAL) ====================
echo "📍 PHASE 3: ESCALATION - Critical Alert (14:30)"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "MongoDBSlowQueries",
      "severity": "critical",
      "instance": "mongo-prod-1:27017",
      "job": "mongodb"
    },
    "annotations": {
      "description": "CRITICAL: MongoDB on mongo-prod-1 connection pool EXHAUSTED! WiredTiger cache at 95% (3.8GB of 4GB). Current connections: 500/500 (MAX). Database is rejecting new connections. Application errors spiking. Average query time: 5000ms (was 180ms). Top errors: MongoNetworkError: connection timed out."
    },
    "startsAt": "2026-02-09T14:30:00Z"
  }]'

echo -e "\n✅ Sent: Escalation (WARNING → CRITICAL)"
echo "Expected: LLM Analysis #2 (reason: escalation) 🔥"
echo ""
sleep 3

# ==================== PHASE 4: More Critical Duplicates ====================
echo "📍 PHASE 4: Critical Duplicate (14:35)"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "MongoDBSlowQueries",
      "severity": "critical",
      "instance": "mongo-prod-1:27017",
      "job": "mongodb"
    },
    "annotations": {
      "description": "CRITICAL: MongoDB on mongo-prod-1 still down. Connection pool full."
    },
    "startsAt": "2026-02-09T14:35:00Z"
  }]'

echo -e "\n✅ Sent: Critical duplicate"
echo "Expected: NO LLM (duplicate_same_severity)"
echo ""
sleep 3

# ==================== PHASE 5: Recovery (CRITICAL → WARNING) ====================
echo "📍 PHASE 5: RECOVERY - Back to Warning (15:00)"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "MongoDBSlowQueries",
      "severity": "warning",
      "instance": "mongo-prod-1:27017",
      "job": "mongodb"
    },
    "annotations": {
      "description": "MongoDB on mongo-prod-1 RECOVERING. Service was restarted at 14:45. WiredTiger cache dropped to 45% (1.8GB of 4GB). Current connections: 220/500 (stabilizing). Average query time: 95ms (improving from 5000ms). No connection errors in last 5 minutes. System appears to be recovering normally."
    },
    "startsAt": "2026-02-09T15:00:00Z"
  }]'

echo -e "\n✅ Sent: Recovery (CRITICAL → WARNING)"
echo "Expected: LLM Analysis #3 (reason: recovery) ⭐"
echo ""

echo ""
echo "========================================"
echo "📊 TEST SUMMARY"
echo "========================================"
echo "Total Alerts Sent: 5"
echo "Expected LLM Analyses: 3"
echo "  1. First WARNING (14:00) - first_occurrence"
echo "  2. CRITICAL (14:30) - escalation 🔥"
echo "  3. WARNING (15:00) - recovery ⭐"
echo ""
echo "Dedup Rate: 40% (2 duplicates skipped)"
echo ""
echo "⏳ Wait 60 seconds for Ollama to process..."
echo "Then check dashboard at: http://localhost:3000"
echo ""
