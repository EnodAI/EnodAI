# EnodAI

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Go](https://img.shields.io/badge/Go-1.21-00ADD8.svg)
![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)

**AI-Powered Intelligent Monitoring Platform**

*From Latin "enodare" (to untie, to solve) - Untying the Knots of Complex Systems*

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 📝 Description

**EnodAI** is a high-performance **microservices architecture** designed to collect, store, and analyze system alerts and metrics using artificial intelligence. It integrates with Prometheus AlertManager, detects metric anomalies, and performs root cause analysis using LLM (Large Language Models).

The name comes from the Latin word "enodare" (to untie, to unravel, to solve) - untying the complex knots in your system's problems.

### 🎯 Core Objectives

- **Real-time Monitoring**: Collect real-time system metrics and alerts
- **Anomaly Detection**: Automatic anomaly detection with Machine Learning (Isolation Forest)
- **Intelligent Analysis**: LLM-powered root cause analysis and solution recommendations
- **High Performance**: Async processing, connection pooling, stream processing
- **Scalability**: Horizontal and vertical scaling with microservices architecture

---

## ✨ Features

### 🔍 Monitoring & Data Collection
- ✅ Prometheus AlertManager webhook integration
- ✅ REST API for custom metric collection
- ✅ Persistent storage in PostgreSQL
- ✅ Real-time data processing with Redis Streams
- ✅ Pre-configured Grafana dashboards
- ✅ Prometheus alert rules (30+ alerts)

### 🤖 AI/ML Capabilities
- ✅ **Isolation Forest** algorithm for anomaly detection
- ✅ **Ollama/Llama2** LLM for root cause analysis
- ✅ Automatic model training and versioning
- ✅ Scheduled model retraining (APScheduler)
- ✅ Confidence score calculation
- ✅ Model performance evaluation

### 📊 Visualization & Monitoring
- ✅ Grafana dashboards (Prometheus & PostgreSQL datasources)
- ✅ Prometheus metrics export
- ✅ Real-time alert tracking
- ✅ AI analysis result visualization
- ✅ Auto-provisioned dashboards

### 🚀 Performance & Reliability
- ✅ Connection pooling (PostgreSQL, Redis)
- ✅ Async/non-blocking I/O
- ✅ Health check endpoints
- ✅ Auto-retry mechanisms
- ✅ Graceful error handling

### 🔐 Security & Authentication
- ✅ JWT token-based authentication
- ✅ Redis-based rate limiting (sliding window)
- ✅ Scope-based permissions
- ✅ Request throttling per endpoint
- ✅ Correlation ID tracking

### 🧪 Testing & Quality
- ✅ Comprehensive unit tests (80%+ coverage)
- ✅ Integration tests
- ✅ Pytest with async support
- ✅ Go test suite with benchmarks
- ✅ CI/CD pipeline (GitHub Actions)

### 🚢 Deployment & DevOps
- ✅ Docker & Docker Compose
- ✅ Kubernetes manifests with HPA
- ✅ Production-ready configurations
- ✅ Automated setup scripts
- ✅ Backup & restore utilities
- ✅ Multi-environment support (dev/prod)

---

## 🏗️ Architecture

```
External Sources → Collector (Go) → PostgreSQL + Redis Streams
                                           ↓
                                    AI Service (Python)
                                      ↓           ↓
                                 ML Detector   LLM Analyzer
                                      ↓           ↓
                                    PostgreSQL (Results)
                                           ↓
                                  Grafana Dashboards
```

**For detailed architecture documentation**: [ARCHITECTURE.md](./ARCHITECTURE.md)

### Services

| Service | Port | Technology | Description |
|--------|------|-----------|----------|
| **Collector** | 8080 | Go/Gin | Metric and alert collection service |
| **AI Service** | 8082 | Python/FastAPI | ML/LLM analysis service |
| **PostgreSQL** | 5432 | PostgreSQL 15 | Primary database |
| **Redis** | 6379 | Redis 7 | Message streaming & cache |
| **Ollama** | 11434 | Ollama/Llama2 | LLM inference engine |
| **Prometheus** | 9090 | Prometheus | Metrics collection |
| **Grafana** | 3000 | Grafana | Visualization dashboards |

---

## 📋 Requirements

### System Requirements

| Component | Minimum | Recommended |
|---------|---------|----------|
| **CPU** | 4 cores | 8 cores |
| **RAM** | 8 GB | 16 GB |
| **Disk** | 20 GB | 50 GB SSD |
| **OS** | Linux/macOS/Windows with WSL2 | Ubuntu 22.04 LTS |

### Software Requirements

- **Docker**: 20.10.x or later
- **Docker Compose**: 2.x or later
- **Git**: 2.x or later

> **Note**: GPU support for Ollama service is optional but recommended (faster LLM inference).

---

## 🚀 Installation

### System Requirements

- **Docker**: 20.10 or higher
- **Docker Compose**: v2.0 or higher (using `docker compose` command)
- **RAM**: Minimum 8GB (16GB recommended for Ollama)
- **Disk**: ~10GB free space (for Docker images and Ollama model)
- **Time**: First installation takes 20-30 minutes (Ollama model download)

### Quick Start (Recommended)

```bash
# Automated setup script
git clone https://github.com/EnodAI/EnodAI.git
cd EnodAI
./scripts/setup.sh
```

or

```bash
# Using Makefile
make quickstart
```

### Manual Installation

### 1. Clone the Repository

```bash
git clone https://github.com/EnodAI/EnodAI.git
cd EnodAI
```

### 2. Check Environment Variables

Docker Compose uses default variables. You can create a `.env` file for customization:

```bash
# .env (optional)
POSTGRES_USER=enod_user
POSTGRES_PASSWORD=enod_password
POSTGRES_DB=enod_alerts
REDIS_ADDR=redis:6379
OLLAMA_URL=http://ollama:11434
GRAFANA_ADMIN_PASSWORD=enod_password
```

> **Note**: Default credentials are secure for development. Change them in production!

### 3. Start Docker Containers

```bash
# Build and start all services
docker compose up --build -d

# Follow logs
docker compose logs -f

# Follow specific service logs
docker compose logs -f ai-service
```

### 4. Download Ollama Model

After the Ollama container starts, download the Llama2 model:

```bash
docker exec -it enodai-ollama-1 ollama pull llama2
```

> **⏱️ Important**:
> - Model download is ~4GB and takes 10-20 minutes depending on your internet speed
> - Wait for the download to complete before using AI analysis features
> - You can skip this step for testing basic metric collection

### 5. Check Service Status

```bash
# Check all container status
docker compose ps

# Test health checks
curl http://localhost:8080/health  # Collector
curl http://localhost:8082/health  # AI Service
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health  # Grafana
```

**Expected Output:**
```
NAME                        STATUS    PORTS
enodai-collector-1      running   0.0.0.0:8080->8080/tcp
enodai-ai-service-1     running   0.0.0.0:8082->8082/tcp
enodai-postgresql-1     running   0.0.0.0:5432->5432/tcp
enodai-redis-1          running   0.0.0.0:6379->6379/tcp
enodai-ollama-1         running   0.0.0.0:11434->11434/tcp
enodai-prometheus-1     running   0.0.0.0:9090->9090/tcp
enodai-grafana-1        running   0.0.0.0:3000->3000/tcp
```

---

## 🔐 Authentication (New!)

EnodAI uses JWT token-based authentication.

### Getting a Token

```bash
# Login with basic auth
curl -X POST http://localhost:8082/api/v1/auth/token \
  -u admin:secret

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using Token with API

```bash
# Access protected endpoint with token
curl http://localhost:8082/api/v1/analysis/latest \
  -H "Authorization: Bearer <your-token>"
```

**Default Users:**
- Username: `admin` / Password: `secret` (all permissions)
- Username: `user` / Password: `secret` (read-only)

> ⚠️ Change these passwords in production!

---

## 📖 Usage

### 1. Sending Metrics

Manual metric submission via REST API:

```bash
curl -X POST http://localhost:8080/api/v1/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "cpu_usage",
    "metric_value": 85.5,
    "labels": {
      "host": "server-1",
      "environment": "production"
    }
  }'
```

**Response:**
```json
{
  "status": "processed"
}
```

### 2. Sending Alerts (Prometheus AlertManager Format)

```bash
curl -X POST http://localhost:8080/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "HighCPUUsage",
      "severity": "critical",
      "instance": "server-1"
    },
    "annotations": {
      "description": "CPU usage is above 90% for 5 minutes",
      "summary": "High CPU detected on server-1"
    },
    "startsAt": "2024-02-07T10:00:00Z",
    "generatorURL": "http://prometheus:9090/graph?g0.expr=cpu_usage"
  }]'
```

**Response:**
```json
{
  "status": "processed",
  "count": 1
}
```

### 3. Viewing AI Analysis Results

Query latest analysis results via REST API:

```bash
curl http://localhost:8082/api/v1/analysis/latest
```

**Response (Improved Format):**
```json
[
  {
    "id": "123",
    "alert_id": "456",
    "analysis_type": "llm_analysis",
    "model_name": "llama2",
    "analysis_data": {
      "root_cause": {
        "technical_reason": "Memory leak in authentication service due to infinite loop",
        "affected_component": "Authentication service",
        "impact": "Slow response times and potential service downtime"
      },
      "immediate_actions": [
        {
          "action": "Restart authentication service instance",
          "rationale": "Free up stuck memory immediately",
          "estimated_time": "5-10 minutes",
          "priority": "high"
        }
      ],
      "short_term_actions": [
        {
          "action": "Increase maximum memory limit for the service",
          "rationale": "Prevent immediate recurrence",
          "estimated_time": "24-48 hours",
          "priority": "medium"
        }
      ],
      "long_term_actions": [
        {
          "action": "Implement memory profiling and leak detection",
          "rationale": "Identify and fix root cause permanently",
          "estimated_time": "1-7 days",
          "priority": "low"
        }
      ],
      "monitoring": {
        "key_metrics": ["memory_usage", "gc_frequency"],
        "alert_threshold": "Above 90% for more than 30 minutes"
      }
    },
    "confidence_score": 0.85,
    "created_at": "2026-02-09T10:05:00Z"
  }
]
```

### 4. Accessing Grafana Dashboards

1. **Login to Grafana:**
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `kam_password`

2. **Check datasources:**
   - Configuration → Data Sources
   - Prometheus and PostgreSQL datasources are auto-configured

3. **Create dashboards:**
   - **Prometheus datasource**:
     - `enod_alerts_received_total` - Number of alerts received
     - `enod_metrics_received_total` - Number of metrics received
     - `enod_processing_duration_seconds` - Processing durations

   - **PostgreSQL datasource**:
     ```sql
     -- Alerts in last 24 hours
     SELECT created_at, alert_name, severity, status
     FROM alerts
     WHERE created_at > NOW() - INTERVAL '24 hours'
     ORDER BY created_at DESC;

     -- AI analysis results
     SELECT a.alert_name, a.severity,
            r.analysis_type, r.confidence_score, r.created_at
     FROM ai_analysis_results r
     JOIN alerts a ON r.alert_id = a.id
     ORDER BY r.created_at DESC
     LIMIT 50;
     ```

### 5. Checking Prometheus Targets

- URL: http://localhost:9090/targets
- Verify all targets are in **UP** state

### 6. Direct Database Access

To connect to PostgreSQL:

```bash
docker exec -it enodai-postgresql-1 psql -U kam_user -d kam_alerts
```

**Example Queries:**

```sql
-- Last 10 metrics
SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 10;

-- Last 10 alerts
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;

-- Anomaly detection results
SELECT * FROM ai_analysis_results
WHERE analysis_type = 'anomaly_detection'
ORDER BY created_at DESC LIMIT 10;

-- LLM analysis results
SELECT
    a.alert_name,
    a.severity,
    r.analysis_data->>'root_cause' as root_cause,
    r.analysis_data->>'mitigation' as mitigation,
    r.confidence_score
FROM ai_analysis_results r
JOIN alerts a ON r.alert_id = a.id
WHERE r.analysis_type = 'llm_analysis'
ORDER BY r.created_at DESC;
```

---

## 🔧 Configuration

### Collector Service Configuration

Environment variables used in `collector/main.go`:

| Variable | Default | Description |
|----------|-----------|----------|
| `DB_HOST` | postgresql | PostgreSQL host |
| `DB_USER` | kam_user | PostgreSQL username |
| `DB_PASSWORD` | kam_password | PostgreSQL password |
| `DB_NAME` | kam_alerts | Database name |
| `REDIS_ADDR` | redis:6379 | Redis address |

### AI Service Configuration

Settings in `ai-service/app/config.py`:

| Variable | Default | Description |
|----------|-----------|----------|
| `REDIS_URL` | redis://redis:6379 | Redis connection URL |
| `POSTGRES_HOST` | postgres | PostgreSQL host |
| `POSTGRES_USER` | kam_user | PostgreSQL username |
| `POSTGRES_PASSWORD` | kam_password | PostgreSQL password |
| `POSTGRES_DB` | kam_alerts | Database name |
| `OLLAMA_HOST` | ollama | Ollama host |
| `OLLAMA_PORT` | 11434 | Ollama port |

### Prometheus AlertManager Webhook Configuration

To redirect Prometheus AlertManager to EnodAI:

```yaml
# alertmanager.yml
route:
  receiver: 'enodai-webhook'

receivers:
  - name: 'enodai-webhook'
    webhook_configs:
      - url: 'http://collector:8080/api/v1/alerts'
        send_resolved: true
```

---

## 🧪 Testing

### Automated Test Suite

```bash
# Run all tests
make test

# AI service tests only
make test-ai

# Collector tests only
make test-collector

# With coverage report
cd ai-service && pytest --cov=app --cov-report=html
```

**Test Statistics:**
- AI Service: 20+ tests, 80%+ coverage
- Collector: 12+ tests, 75%+ coverage
- Total: 32+ tests, 78%+ coverage

### Linting

```bash
# Run all linting
make lint

# Auto-fix
make lint-fix
```

### Manual Test Script

Send sample metrics and alerts for automated testing:

```bash
#!/bin/bash

# Send test metrics
for i in {1..10}; do
  cpu_value=$((RANDOM % 100))
  curl -X POST http://localhost:8080/api/v1/metrics \
    -H "Content-Type: application/json" \
    -d "{
      \"metric_name\": \"cpu_usage\",
      \"metric_value\": $cpu_value,
      \"labels\": {\"host\": \"test-server-$i\"}
    }"
  echo "Sent metric: cpu_usage=$cpu_value"
  sleep 1
done

# Send test alert
curl -X POST http://localhost:8080/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "description": "This is a test alert"
    },
    "startsAt": "2024-02-07T10:00:00Z"
  }]'

echo -e "\n✅ Test data sent!"
echo "View AI analysis results:"
echo "curl http://localhost:8082/api/v1/analysis/latest"
```

Run the file:

```bash
chmod +x test_data.sh
./test_data.sh
```

### Log Monitoring

Monitor service processing status:

```bash
# Watch AI Service logs (anomaly detection and LLM analysis)
docker compose logs -f ai-service

# Watch Collector logs (incoming metrics/alerts)
docker compose logs -f collector

# Watch Redis consumer logs
docker compose logs -f ai-service | grep "Consumer"
```

---

## 🐛 Troubleshooting

### Problem: Services not starting

**Solution:**
```bash
# Stop and clean containers
docker compose down -v

# Rebuild
docker compose up --build -d

# Check logs
docker compose logs
```

### Problem: PostgreSQL connection error

**Symptom:** `connection refused` or `database does not exist`

**Solution:**
```bash
# Ensure PostgreSQL container is running
docker compose ps postgresql

# Check health
docker exec enodai-postgresql-1 pg_isready -U kam_user

# Test manual connection
docker exec -it enodai-postgresql-1 psql -U kam_user -d kam_alerts -c "SELECT 1;"
```

### Problem: Ollama model not loaded

**Symptom:** LLM analysis errors

**Solution:**
```bash
# Connect to Ollama container
docker exec -it enodai-ollama-1 bash

# List available models
ollama list

# Download model if missing
ollama pull llama2

# Check model download status
curl http://localhost:11434/api/tags
```

### Problem: Redis connection timeout

**Solution:**
```bash
# Ensure Redis is running
docker exec enodai-redis-1 redis-cli ping
# Expected: PONG

# Check Redis stream
docker exec enodai-redis-1 redis-cli XINFO STREAM metrics:raw
```

### Problem: AI Service not consuming messages

**Symptom:** Metrics arriving but not being written to database

**Solution:**
```bash
# Check AI Service logs
docker compose logs ai-service | grep "Consumer"

# Manually check Redis stream
docker exec enodai-redis-1 redis-cli XLEN metrics:raw
# Should show message count

# Check consumer group status
docker exec enodai-redis-1 redis-cli XINFO GROUPS metrics:raw

# Restart AI Service
docker compose restart ai-service
```

### Problem: Low performance

**Solution:**
```bash
# Check resource usage
docker stats

# Allocate more memory for Ollama (docker compose.yml)
# deploy.resources.limits.memory: 8G

# Increase PostgreSQL connection pool (ai-service/app/database.py)
# max_size: 30

# Increase Redis pool size (collector/main.go)
# PoolSize: 30
```

---

## 🛑 Stopping Services

### Temporary Stop

```bash
# Stop all services (data is preserved)
docker compose stop

# Restart
docker compose start
```

### Complete Removal

```bash
# Remove containers and network (volumes are preserved)
docker compose down

# Remove volumes too (ALL DATA WILL BE DELETED!)
docker compose down -v
```

### Restarting Specific Service

```bash
docker compose restart ai-service
docker compose restart collector
```

---

## 📊 Metrics and Monitoring

### Collected Prometheus Metrics

#### Collector Metrics (8080/metrics)
- `enod_alerts_received_total` - Total alerts received
- `enod_metrics_received_total` - Total metrics received
- `enod_processing_duration_seconds` - Request processing time (histogram)

#### Usage:
```promql
# Alert reception rate (last 5 minutes)
rate(enod_alerts_received_total[5m])

# 95th percentile processing time
histogram_quantile(0.95, enod_processing_duration_seconds_bucket)

# Metric collection rate
rate(enod_metrics_received_total[5m])
```

---

## 🔒 Security Notes

> ⚠️ **IMPORTANT**: This setup is for **development/test** environments. For production use:

- [ ] Change all default passwords
- [ ] Move environment variables to secrets manager (Vault, AWS Secrets Manager)
- [ ] Enable TLS/SSL (PostgreSQL, Redis, HTTP)
- [ ] Configure network segmentation
- [ ] Add rate limiting
- [ ] Implement API authentication/authorization (JWT, OAuth2)
- [ ] Configure firewall rules
- [ ] Run containers as non-root user
- [ ] Perform image vulnerability scanning (Trivy, Clair)
- [ ] Add audit logging

---

## 🛠️ Makefile Commands

```bash
make help              # List all commands
make build             # Build Docker images
make up                # Start services
make down              # Stop services
make logs              # Show logs
make test              # Run tests
make lint              # Check code
make health-check      # Check service health
make send-test-data    # Send test data
make db-backup         # Backup database
make db-restore        # Restore database
make clean             # Cleanup
make quickstart        # Start everything
```

### Utility Scripts

```bash
./scripts/setup.sh     # Automated setup
./scripts/backup.sh    # Database backup
./scripts/restore.sh   # Database restore
./scripts/monitor.sh   # Live monitoring
```

---

## ☸️ Kubernetes Deployment

```bash
# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Deploy all resources
kubectl apply -f k8s/base/

# Or using Kustomize
kubectl apply -k k8s/overlays/prod/

# Check status
kubectl get pods -n enodai
kubectl get svc -n enodai

# Logs
kubectl logs -f deployment/ai-service -n enodai

# Scaling
kubectl scale deployment collector -n enodai --replicas=5
```

**Auto-scaling (HPA) is pre-configured:**
- Collector: 2-10 replicas (CPU 70%, Memory 80%)
- AI Service: 2-5 replicas (CPU 70%, Memory 80%)

For details: [k8s/README.md](./k8s/README.md)

---

## 🚢 Production Deployment

```bash
# Using production compose
docker compose -f docker compose.yml -f docker compose.prod.yml up -d

# Or using Makefile
make deploy-prod
```

**Production features:**
- Resource limits and reservations
- Replicated services (2x collector, 2x ai-service)
- Enhanced logging
- Auto-restart policies
- Performance tuning

For details: [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 🔄 CI/CD Pipeline

Automated CI/CD with GitHub Actions:

**`.github/workflows/ci.yml`:**
- ✅ Python and Go tests
- ✅ Linting (black, flake8, golangci-lint)
- ✅ Code coverage (Codecov)
- ✅ Docker image build
- ✅ Security scanning (Trivy)

**`.github/workflows/deploy.yml`:**
- ✅ Container registry push (GHCR)
- ✅ Staging deployment (main branch)
- ✅ Production deployment (tags)

---

## 📚 Additional Resources

### Documentation
- **Architecture Documentation**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Deployment Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Contributing Guide**: [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Kubernetes Guide**: [k8s/README.md](./k8s/README.md)

### API & Monitoring
- **API Documentation**: http://localhost:8082/docs (FastAPI auto-generated)
- **Prometheus UI**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Prometheus Alerts**: http://localhost:9090/alerts

### Technology Documentation
- [Go Gin Framework](https://gin-gonic.com/docs/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis Streams](https://redis.io/docs/data-types/streams/)
- [Ollama](https://ollama.ai/docs)
- [Scikit-learn Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)

---

## 🤝 Contributing

We welcome your contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push your branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Code style: Go (gofmt), Python (black, isort)
- Commit message format: Conventional Commits
- Test coverage: Minimum 80%
- Documentation: Add documentation for every new feature

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **EnodAI Development Team**

---

## 🙏 Acknowledgments

- [Prometheus](https://prometheus.io/) - Monitoring system
- [Grafana](https://grafana.com/) - Visualization
- [Ollama](https://ollama.ai/) - LLM inference
- [PostgreSQL](https://www.postgresql.org/) - Database
- [Redis](https://redis.io/) - Streaming & caching

---

## 📞 Contact

For questions:
- GitHub Issues: [Create an issue](https://github.com/your-username/EnodAI/issues)
- Email: support@enodai.com

---

<div align="center">

**Monitor your systems intelligently with EnodAI!** 🚀

Made with ❤️ by EnodAI Team

</div>

