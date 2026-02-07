#!/bin/bash

# EnodAI Setup Script
# This script sets up the complete EnodAI environment

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  EnodAI Setup Script${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"
echo ""

# Check Docker daemon
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "Please start Docker daemon"
    exit 1
fi

echo -e "${GREEN}✅ Docker daemon is running${NC}"
echo ""

# Create .env file if not exists
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cat > .env <<EOF
# Database
POSTGRES_USER=kam_user
POSTGRES_PASSWORD=kam_password
POSTGRES_DB=kam_alerts

# Redis
REDIS_ADDR=redis:6379
REDIS_URL=redis://redis:6379

# Ollama
OLLAMA_URL=http://ollama:11434

# Grafana
GRAFANA_ADMIN_PASSWORD=kam_password

# JWT Secret (change in production!)
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists, skipping...${NC}"
fi
echo ""

# Build Docker images
echo -e "${BLUE}Building Docker images...${NC}"
docker-compose build
echo -e "${GREEN}✅ Docker images built${NC}"
echo ""

# Start services
echo -e "${BLUE}Starting services...${NC}"
docker-compose up -d
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Wait for services to be healthy
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 10

# Check service health
echo -e "${BLUE}Checking service health...${NC}"
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Collector service is ready${NC}"
        break
    fi
    retry_count=$((retry_count + 1))
    echo -e "${YELLOW}⏳ Waiting for collector... ($retry_count/$max_retries)${NC}"
    sleep 2
done

retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:8082/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ AI service is ready${NC}"
        break
    fi
    retry_count=$((retry_count + 1))
    echo -e "${YELLOW}⏳ Waiting for AI service... ($retry_count/$max_retries)${NC}"
    sleep 2
done

# Download Ollama models
echo ""
echo -e "${BLUE}Downloading Ollama models...${NC}"
docker exec enodai-ollama-1 ollama pull llama2
echo -e "${GREEN}✅ Ollama models downloaded${NC}"

# Create initial database tables
echo ""
echo -e "${BLUE}Database tables are automatically created via init.sql${NC}"
echo -e "${GREEN}✅ Database initialized${NC}"

# Summary
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Setup Complete! 🎉${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "Access points:"
echo -e "  • Collector:   ${BLUE}http://localhost:8080${NC}"
echo -e "  • AI Service:  ${BLUE}http://localhost:8082${NC}"
echo -e "  • API Docs:    ${BLUE}http://localhost:8082/docs${NC}"
echo -e "  • Grafana:     ${BLUE}http://localhost:3000${NC} (admin/kam_password)"
echo -e "  • Prometheus:  ${BLUE}http://localhost:9090${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Send test data:    ${YELLOW}./test_data.sh${NC}"
echo -e "  2. View logs:         ${YELLOW}docker-compose logs -f${NC}"
echo -e "  3. Run tests:         ${YELLOW}make test${NC}"
echo ""
echo -e "For more commands:     ${YELLOW}make help${NC}"
echo ""
