#!/bin/bash

# EnodAI Monitoring Script
# Continuously monitors service health and logs

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

clear

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  EnodAI Service Monitor${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

check_service() {
    local service_name=$1
    local url=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)

    if [ "$response" == "200" ]; then
        echo -e "  ${GREEN}✓${NC} $service_name"
        return 0
    else
        echo -e "  ${RED}✗${NC} $service_name (HTTP $response)"
        return 1
    fi
}

while true; do
    tput cup 4 0

    echo -e "${BLUE}Service Status:${NC}"
    check_service "Collector   " "http://localhost:8080/health"
    check_service "AI Service  " "http://localhost:8082/health"
    check_service "Prometheus  " "http://localhost:9090/-/healthy"
    check_service "Grafana     " "http://localhost:3000/api/health"

    echo ""
    echo -e "${BLUE}Container Status:${NC}"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}" | tail -n +2 | while read line; do
        if [[ $line == *"Up"* ]]; then
            echo -e "  ${GREEN}✓${NC} $line"
        else
            echo -e "  ${RED}✗${NC} $line"
        fi
    done

    echo ""
    echo -e "${BLUE}Recent Metrics:${NC}"
    curl -s http://localhost:8080/metrics 2>/dev/null | grep "sensus_" | tail -5

    echo ""
    echo -e "${YELLOW}Press Ctrl+C to exit${NC}"

    sleep 5
done
