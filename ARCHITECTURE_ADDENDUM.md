# Architecture Addendum - New Features

This document details the newly added features and components.

## 🧪 Testing Strategy

### Test Coverage
- **AI Service**: 80%+ coverage (20+ tests)
- **Collector**: 75%+ coverage (12+ tests)
- **Total**: 78%+ coverage (32+ tests)

### Test Types

#### Unit Tests
- **AI Service** (`ai-service/tests/`):
  - `test_detector.py`: Anomaly detection logic
  - `test_database.py`: Database operations
  - `test_redis_client.py`: Redis consumer
  - `test_api.py`: API endpoints
  - `conftest.py`: Test fixtures

- **Collector** (`collector/main_test.go`):
  - HTTP handler tests
  - Request validation tests
  - Benchmark tests

#### Test Configuration
- `pytest.ini`: Pytest configuration
  - Coverage settings (80% minimum)
  - Test discovery
  - Async test support
  - HTML coverage reports

### Running Tests
```bash
# All tests
make test

# Specific service
make test-ai
make test-collector

# With coverage
cd ai-service && pytest --cov=app --cov-report=html
```

---

## 🔐 Authentication & Authorization

### JWT Implementation

**Location**: `ai-service/app/auth.py`

**Features**:
- Token generation with configurable expiration
- HS256 algorithm
- Scope-based permissions
- Password hashing (bcrypt)

**Flow**:
```
1. Client → POST /api/v1/auth/token (Basic Auth)
2. Server validates credentials
3. Server generates JWT with user scopes
4. Client stores token
5. Client → API requests with Bearer token
6. Server validates token on each request
```

**Token Structure**:
```json
{
  "sub": "username",
  "scopes": ["read:analysis", "write:analysis", "admin"],
  "exp": 1234567890
}
```

### Endpoints

**`POST /api/v1/auth/token`**
- Input: Basic Auth (username:password)
- Output: JWT token
- No rate limiting (login endpoint)

**`GET /api/v1/auth/me`**
- Input: Bearer token
- Output: User info and scopes
- Protected endpoint

### Default Users
```python
"admin": {
    "password": "secret",  # bcrypt hashed
    "scopes": ["read:analysis", "write:analysis", "admin"]
}
"user": {
    "password": "secret",
    "scopes": ["read:analysis"]
}
```

---

## 🚦 Rate Limiting

### Implementation

**Location**: `ai-service/app/middleware/rate_limit.py`

**Algorithm**: Sliding Window (Redis sorted sets)
- Uses ZSET for timestamp tracking
- ZREMRANGEBYSCORE for old entry cleanup
- ZADD for new requests
- ZCARD for count

**Configuration**:
```python
rate_limits = {
    "/api/v1/metrics": {"requests": 100, "window": 60},
    "/api/v1/alerts": {"requests": 50, "window": 60},
    "/api/v1/analysis": {"requests": 30, "window": 60},
    "default": {"requests": 60, "window": 60}
}
```

**Response Headers**:
- `X-RateLimit-Limit`: Maximum requests
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Window`: Time window (seconds)
- `Retry-After`: Seconds to wait (on 429)

**Behavior**:
- Returns 429 Too Many Requests on limit exceeded
- Fails open on Redis errors (allows requests)
- Skips health checks and docs

---

## 📅 Model Retraining Scheduler

### Implementation

**Location**: `ai-service/app/scheduler.py`

**Technology**: APScheduler (AsyncIOScheduler)

**Jobs**:

1. **Model Retraining** (Daily @ 2 AM)
   - Fetches last 10,000 data points
   - Trains Isolation Forest model
   - Saves new model to disk
   - Job ID: `model_retraining`

2. **Model Evaluation** (Every 6 hours)
   - Evaluates model performance
   - Calculates metrics (TODO)
   - Compares with baseline
   - Job ID: `model_evaluation`

**Usage**:
```python
# Automatic (on startup)
await scheduler.start()

# Manual trigger
scheduler.trigger_retrain()
```

**Configuration**:
```python
# Daily at 2 AM
CronTrigger(hour=2, minute=0)

# Every 6 hours
CronTrigger(hour='*/6')
```

---

## 📊 Monitoring Enhancements

### Grafana Dashboards

**Auto-provisioned dashboard**: `enod-overview.json`

**Panels**:
1. Total Alerts Received (Stat)
   - Query: `enod_alerts_received_total`

2. Total Metrics Received (Stat)
   - Query: `enod_metrics_received_total`

3. Ingestion Rate (Time Series)
   - Query: `rate(enod_alerts_received_total[5m])`
   - Query: `rate(enod_metrics_received_total[5m])`

4. Processing Duration (Time Series)
   - Query: `histogram_quantile(0.95, rate(enod_processing_duration_seconds_bucket[5m]))`
   - Query: `histogram_quantile(0.99, rate(enod_processing_duration_seconds_bucket[5m]))`

**Provisioning**:
- Location: `grafana/provisioning/dashboards/`
- Config: `dashboard.yml`
- Auto-load on Grafana startup

### Prometheus Alert Rules

**File**: `prometheus/alert_rules.yml`

**Alert Groups**:

1. **enodai_alerts**
   - Service health (Down alerts)
   - Performance (Latency)
   - Traffic (Volume, No data)

2. **database_alerts**
   - PostgreSQL/Redis down
   - Slow queries

3. **anomaly_detection_alerts**
   - High anomaly rate
   - No anomalies detected

4. **llm_analysis_alerts**
   - Ollama service down
   - High LLM response time

**Total**: 15+ alert rules

---

## 🚀 CI/CD Pipeline

### GitHub Actions Workflows

#### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Triggers**: Push to main/develop, Pull requests

**Jobs**:

1. **test-ai-service**
   - Python 3.11
   - PostgreSQL & Redis services
   - Run pytest with coverage
   - Upload to Codecov

2. **test-collector**
   - Go 1.21
   - Run go test with race detector
   - Upload coverage

3. **lint-python**
   - Black (code formatting)
   - isort (import sorting)
   - flake8 (linting)

4. **lint-go**
   - golangci-lint

5. **build-images**
   - Docker Buildx
   - Build both services
   - Cache layers (GitHub Actions cache)

6. **security-scan**
   - Trivy vulnerability scanner
   - SARIF output to GitHub Security tab

#### 2. Deploy Pipeline (`.github/workflows/deploy.yml`)

**Triggers**: Push to main, Git tags (v*)

**Jobs**:

1. **build-and-push**
   - Build Docker images
   - Push to GHCR (GitHub Container Registry)
   - Multi-arch support (optional)

2. **deploy-staging** (main branch)
   - Deploy to staging environment
   - Environment: staging

3. **deploy-production** (tags)
   - Deploy to production
   - Environment: production
   - Requires manual approval

---

## ☸️ Kubernetes Deployment

### Resources

**Location**: `k8s/base/`

**Manifests**:
1. `namespace.yaml` - enodai namespace
2. `configmap.yaml` - Configuration
3. `secret.yaml` - Sensitive data
4. `collector-deployment.yaml` - Collector + Service + HPA
5. `ai-service-deployment.yaml` - AI Service + Service + HPA
6. `postgresql-statefulset.yaml` - PostgreSQL StatefulSet
7. `ingress.yaml` - Ingress with TLS

### Features

**Auto-scaling (HPA)**:
- Collector: 2-10 replicas (CPU 70%, Memory 80%)
- AI Service: 2-5 replicas (CPU 70%, Memory 80%)

**Health Checks**:
- Liveness probes (10s interval)
- Readiness probes (5s interval)

**Resource Limits**:
- Collector: 256Mi-512Mi RAM, 250m-500m CPU
- AI Service: 1Gi-2Gi RAM, 500m-1000m CPU
- PostgreSQL: 1Gi-2Gi RAM, 500m-1000m CPU

**Storage**:
- PostgreSQL: 10Gi PVC per instance
- StatefulSet for persistence

**Networking**:
- ClusterIP services (internal)
- Ingress for external access
- TLS termination (cert-manager)

---

## 🛠️ DevOps Tools

### Makefile

**30+ commands** organized by category:

**Development**:
- `make build`, `make up`, `make down`, `make restart`
- `make logs`, `make logs-ai`, `make logs-collector`

**Testing**:
- `make test`, `make test-ai`, `make test-collector`
- `make lint`, `make lint-fix`

**Database**:
- `make db-shell`, `make db-backup`, `make db-restore`

**Deployment**:
- `make deploy-dev`, `make deploy-prod`

**Utilities**:
- `make health-check`, `make send-test-data`
- `make clean`, `make clean-all`

**Quick start**:
- `make quickstart` - Everything in one command

### Utility Scripts

**Location**: `scripts/`

1. **setup.sh**
   - Automated project setup
   - Prerequisite checks
   - Environment file creation
   - Service startup
   - Ollama model download

2. **backup.sh**
   - PostgreSQL backup
   - Gzip compression
   - Automatic cleanup (7 days)
   - Size reporting

3. **restore.sh**
   - Database restore
   - Interactive backup selection
   - Connection termination
   - Database recreation

4. **monitor.sh**
   - Live service monitoring
   - Health check loop
   - Container status
   - Recent metrics

---

## 📝 Logging & Observability

### Logging Middleware

**Location**: `ai-service/app/middleware/logging.py`

**Features**:
- Request/response logging
- Correlation ID generation/tracking
- Performance timing
- Structured logging (loguru)
- User agent tracking
- Error logging with stack traces

**Log Format**:
```
→ POST /api/v1/analysis/latest
  correlation_id: 550e8400-e29b-41d4-a716-446655440000
  method: POST
  path: /api/v1/analysis/latest
  duration: 0.123s

← POST /api/v1/analysis/latest 200 (0.123s)
```

**Response Headers**:
- `X-Correlation-ID`: Request tracking
- `X-Process-Time`: Processing duration

---

## 📦 Production Configuration

### Docker Compose Production

**File**: `docker-compose.prod.yml`

**Features**:
- Resource limits & reservations
- Replicated services (2x)
- Enhanced logging (50MB/5 files)
- Auto-restart policies
- Performance tuning (Redis AOF, Prometheus retention)
- Environment-based secrets

**Usage**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Template

**File**: `.env.example`

**Variables**:
- Database credentials
- Redis configuration
- JWT secret key
- Feature flags
- Performance tuning

---

## 🔄 Summary of New Components

| Component | Files | Status |
|-----------|-------|--------|
| Unit Tests | tests/* | ✅ 32+ tests |
| JWT Auth | app/auth.py, app/routers/auth.py | ✅ Implemented |
| Rate Limiting | app/middleware/rate_limit.py | ✅ Implemented |
| Scheduler | app/scheduler.py | ✅ Implemented |
| Grafana Dashboards | grafana/provisioning/dashboards/* | ✅ Auto-provisioned |
| Prometheus Alerts | prometheus/alert_rules.yml | ✅ 15+ rules |
| CI/CD | .github/workflows/* | ✅ 2 workflows |
| Kubernetes | k8s/base/* | ✅ 7 manifests |
| Makefile | Makefile | ✅ 30+ commands |
| Scripts | scripts/* | ✅ 4 utilities |
| Logging | app/middleware/logging.py | ✅ Implemented |
| Production Config | docker-compose.prod.yml | ✅ Implemented |

**Total New Files**: 40+
**Total Lines of Code Added**: 5000+

---

**Version**: 1.0.0
**Last Updated**: 2024-02-07
