#!/bin/bash

echo "🚀 EnodAI Test Data Generator"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COLLECTOR_URL="http://localhost:8080"
AI_SERVICE_URL="http://localhost:8082"

# Check if services are running
echo -e "${BLUE}Checking services...${NC}"
if ! curl -s "${COLLECTOR_URL}/health" > /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Collector service is not responding at ${COLLECTOR_URL}${NC}"
    echo "Please make sure Docker containers are running: docker-compose ps"
    exit 1
fi

if ! curl -s "${AI_SERVICE_URL}/health" > /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: AI Service is not responding at ${AI_SERVICE_URL}${NC}"
fi

echo -e "${GREEN}✅ Services are running${NC}"
echo ""

# Send test metrics
echo -e "${BLUE}📊 Sending test metrics...${NC}"
for i in {1..10}; do
  # Generate random CPU value (some anomalies)
  if [ $((i % 3)) -eq 0 ]; then
    # Anomaly: high CPU
    cpu_value=$((85 + RANDOM % 15))
  else
    # Normal: moderate CPU
    cpu_value=$((30 + RANDOM % 40))
  fi

  memory_value=$((40 + RANDOM % 40))

  # Send CPU metric
  curl -s -X POST "${COLLECTOR_URL}/api/v1/metrics" \
    -H "Content-Type: application/json" \
    -d "{
      \"metric_name\": \"cpu_usage\",
      \"metric_value\": ${cpu_value},
      \"labels\": {
        \"host\": \"test-server-${i}\",
        \"environment\": \"test\",
        \"region\": \"us-east-1\"
      }
    }" > /dev/null

  echo -e "  ${GREEN}✓${NC} Sent CPU metric: ${cpu_value}% on test-server-${i}"

  # Send Memory metric
  curl -s -X POST "${COLLECTOR_URL}/api/v1/metrics" \
    -H "Content-Type: application/json" \
    -d "{
      \"metric_name\": \"memory_usage\",
      \"metric_value\": ${memory_value},
      \"labels\": {
        \"host\": \"test-server-${i}\",
        \"environment\": \"test\",
        \"region\": \"us-east-1\"
      }
    }" > /dev/null

  echo -e "  ${GREEN}✓${NC} Sent Memory metric: ${memory_value}% on test-server-${i}"

  sleep 0.5
done

echo ""
echo -e "${BLUE}🚨 Sending test alerts...${NC}"

# Send critical alert
curl -s -X POST "${COLLECTOR_URL}/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "HighCPUUsage",
      "severity": "critical",
      "instance": "test-server-3",
      "job": "node-exporter"
    },
    "annotations": {
      "description": "CPU usage is above 90% for 5 minutes on test-server-3",
      "summary": "Critical: High CPU detected",
      "runbook_url": "https://wiki.example.com/runbooks/high-cpu"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "generatorURL": "http://prometheus:9090/graph"
  }]' > /dev/null

echo -e "  ${GREEN}✓${NC} Sent critical alert: HighCPUUsage"

sleep 1

# Send warning alert
curl -s -X POST "${COLLECTOR_URL}/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "HighMemoryUsage",
      "severity": "warning",
      "instance": "test-server-5",
      "job": "node-exporter"
    },
    "annotations": {
      "description": "Memory usage is above 80% on test-server-5",
      "summary": "Warning: High memory usage detected"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "generatorURL": "http://prometheus:9090/graph"
  }]' > /dev/null

echo -e "  ${GREEN}✓${NC} Sent warning alert: HighMemoryUsage"

sleep 1

# Send disk alert
curl -s -X POST "${COLLECTOR_URL}/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "DiskSpaceLow",
      "severity": "warning",
      "instance": "test-server-7",
      "job": "node-exporter",
      "device": "/dev/sda1"
    },
    "annotations": {
      "description": "Disk space is below 20% on /dev/sda1",
      "summary": "Warning: Low disk space"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "generatorURL": "http://prometheus:9090/graph"
  }]' > /dev/null

echo -e "  ${GREEN}✓${NC} Sent warning alert: DiskSpaceLow"

echo ""
echo -e "${GREEN}✅ All test data sent successfully!${NC}"
echo ""
echo -e "${BLUE}📈 Next steps:${NC}"
echo "  1. Check AI analysis results:"
echo "     curl ${AI_SERVICE_URL}/api/v1/analysis/latest"
echo ""
echo "  2. View in Grafana: http://localhost:3000"
echo "     Username: admin"
echo "     Password: kam_password"
echo ""
echo "  3. Check Prometheus metrics: http://localhost:9090"
echo ""
echo "  4. Query database:"
echo "     docker exec -it enodai-postgresql-1 psql -U enod_user -d enod_alerts"
echo ""
echo "  5. Monitor logs:"
echo "     docker-compose logs -f ai-service"
echo ""
echo -e "${YELLOW}⏳ Note: AI analysis may take a few seconds to complete${NC}"
