# Deployment Guide

Complete guide for deploying EnodAI to various environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Docker Compose Deployment](#docker-compose-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Cloud Deployments](#cloud-deployments)
5. [Security Hardening](#security-hardening)
6. [Monitoring & Observability](#monitoring--observability)

---

## Prerequisites

### Required
- Docker 20.10+
- Docker Compose 2.x
- 8GB RAM minimum (16GB recommended)
- 20GB disk space

### Optional
- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3.x

---

## Docker Compose Deployment

### Development

```bash
# Quick start
make quickstart

# Or manually
docker-compose up -d
docker exec enodai-ollama-1 ollama pull llama2
```

### Production

```bash
# Create environment file
cp .env.example .env
# Edit .env with production values

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify
make health-check
```

### Configuration

Edit `.env`:
```bash
# Strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Resource limits
OLLAMA_MEMORY_LIMIT=8G
POSTGRES_MAX_CONNECTIONS=100
```

---

## Kubernetes Deployment

### Quick Deploy

```bash
# Apply manifests
kubectl apply -f k8s/base/

# Check status
kubectl get pods -n enodai
kubectl get svc -n enodai
```

### Production Deploy

1. **Create secrets**:
```bash
kubectl create secret generic enodai-secrets \
  --from-literal=POSTGRES_PASSWORD=$(openssl rand -base64 32) \
  --from-literal=JWT_SECRET_KEY=$(openssl rand -hex 32) \
  -n enodai
```

2. **Apply resources**:
```bash
kubectl apply -k k8s/overlays/prod/
```

3. **Configure ingress**:
```bash
# Edit k8s/base/ingress.yaml with your domain
kubectl apply -f k8s/base/ingress.yaml
```

### Scaling

```bash
# Manual
kubectl scale deployment collector -n enodai --replicas=5

# Auto-scaling (already configured via HPA)
kubectl get hpa -n enodai
```

---

## Cloud Deployments

### AWS ECS

```bash
# Create task definitions
aws ecs register-task-definition --cli-input-json file://ecs/collector-task.json
aws ecs register-task-definition --cli-input-json file://ecs/ai-service-task.json

# Create service
aws ecs create-service --cluster enodai --service-name collector --task-definition collector:1
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT/collector
gcloud builds submit --tag gcr.io/PROJECT/ai-service

# Deploy
gcloud run deploy collector --image gcr.io/PROJECT/collector --region us-central1
gcloud run deploy ai-service --image gcr.io/PROJECT/ai-service --region us-central1
```

### Azure Container Instances

```bash
az container create \
  --resource-group enodai-rg \
  --name collector \
  --image enodai/collector:latest \
  --ports 8080 \
  --environment-variables DB_HOST=... DB_USER=...
```

---

## Security Hardening

### 1. Network Security

```bash
# Firewall rules (example)
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 5432/tcp  # PostgreSQL (internal only)
ufw deny 6379/tcp  # Redis (internal only)
```

### 2. TLS/SSL

```yaml
# docker-compose with TLS
services:
  collector:
    environment:
      - TLS_CERT_FILE=/certs/cert.pem
      - TLS_KEY_FILE=/certs/key.pem
    volumes:
      - ./certs:/certs:ro
```

### 3. Secrets Management

**HashiCorp Vault**:
```bash
vault kv put secret/enodai \
  postgres_password=$POSTGRES_PASSWORD \
  jwt_secret=$JWT_SECRET_KEY
```

**AWS Secrets Manager**:
```bash
aws secretsmanager create-secret \
  --name enodai/postgres \
  --secret-string '{"password":"..."}'
```

### 4. Database Security

```sql
-- Create read-only user
CREATE USER readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE kam_alerts TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

-- Enable SSL
ALTER SYSTEM SET ssl = on;
```

---

## Monitoring & Observability

### Prometheus

```yaml
# Add custom alert rules
groups:
  - name: custom_alerts
    rules:
      - alert: CustomHighLatency
        expr: http_request_duration_seconds > 1
        for: 5m
```

### Grafana Dashboards

```bash
# Import pre-built dashboard
curl -X POST http://admin:kam_password@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @grafana/provisioning/dashboards/enod-overview.json
```

### Logging

**Centralized logging with ELK**:
```yaml
services:
  collector:
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://logstash:5000"
        tag: "collector"
```

### Distributed Tracing

**Jaeger integration**:
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
```

---

## Backup & Recovery

### Automated Backups

```bash
# Daily cron job
0 2 * * * /path/to/scripts/backup.sh

# S3 backup
aws s3 cp backups/backup_latest.sql.gz s3://enodai-backups/
```

### Disaster Recovery

```bash
# Restore from backup
./scripts/restore.sh backups/backup_20240207_020000.sql.gz

# Verify
psql -U kam_user -d kam_alerts -c "SELECT COUNT(*) FROM alerts;"
```

---

## Performance Tuning

### Database

```sql
-- Increase connection pool
ALTER SYSTEM SET max_connections = 200;

-- Optimize queries
ANALYZE;
VACUUM FULL;

-- Add indexes
CREATE INDEX CONCURRENTLY idx_custom ON table_name(column);
```

### Redis

```bash
# Increase memory limit
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Application

```python
# Increase worker processes
uvicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

---

## Troubleshooting

### Common Issues

**Database connection timeout**:
```bash
# Check connectivity
docker exec enodai-postgresql-1 pg_isready -U kam_user

# Check logs
docker logs enodai-postgresql-1
```

**High memory usage**:
```bash
# Check resource usage
docker stats

# Adjust limits in docker-compose.prod.yml
```

**Slow API responses**:
```bash
# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=http_request_duration_seconds

# Profile Python code
python -m cProfile -o output.pstats main.py
```

---

## Health Checks

```bash
# Automated health monitoring
./scripts/monitor.sh

# API health checks
curl http://localhost:8080/health
curl http://localhost:8082/health
curl http://localhost:9090/-/healthy
```

---

## Rollback Procedures

```bash
# Docker Compose
docker-compose down
git checkout previous-version
docker-compose up -d

# Kubernetes
kubectl rollout undo deployment/collector -n enodai
kubectl rollout status deployment/collector -n enodai
```

---

## Support

- **Documentation**: [README.md](./README.md), [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Issues**: https://github.com/your-repo/issues
- **Community**: Discord/Slack channel

---

**Last Updated**: 2024-02-07
