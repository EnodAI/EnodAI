# SensusAI - Sistem Mimarisi

## 📋 İçindekiler
1. [Genel Bakış](#genel-bakış)
2. [Mimari Diyagram](#mimari-diyagram)
3. [Servis Detayları](#servis-detayları)
4. [Veri Akışı](#veri-akışı)
5. [Teknoloji Stack](#teknoloji-stack)
6. [Veritabanı Şeması](#veritabanı-şeması)
7. [Performans Optimizasyonları](#performans-optimizasyonları)
8. [Güvenlik](#güvenlik)
9. [Ölçeklenebilirlik](#ölçeklenebilirlik)

---

## Genel Bakış

SensusAI, **mikroservis mimarisine** dayalı, yüksek performanslı bir sistem izleme ve anomali tespit platformudur. Prometheus AlertManager'dan gelen uyarıları ve metrik verilerini toplar, makine öğrenmesi ile anomali tespiti yapar ve LLM (Large Language Model) kullanarak kök neden analizi gerçekleştirir.

### Temel Özellikler
- ✅ Real-time metrik ve alert toplama
- ✅ Makine öğrenmesi ile anomali tespiti (Isolation Forest)
- ✅ LLM destekli kök neden analizi (Ollama/Llama2)
- ✅ Yüksek performanslı veri işleme (Redis Streams)
- ✅ Ölçeklenebilir mikroservis mimarisi
- ✅ Prometheus metrikleri ve Grafana dashboards
- ✅ Container orchestration (Docker Compose & Kubernetes)
- ✅ JWT Authentication & Rate Limiting
- ✅ Automated Testing (80%+ coverage)
- ✅ CI/CD Pipeline (GitHub Actions)
- ✅ Production-ready deployment

---

## Mimari Diyagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Sources                              │
│  (Prometheus AlertManager, Application Metrics)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP POST
                         ▼
         ┌───────────────────────────────┐
         │   Collector Service (Go)      │
         │   - Port: 8080                │
         │   - Gin Framework             │
         │   - REST API                  │
         └───────┬───────────────┬───────┘
                 │               │
        ┌────────▼─────┐    ┌───▼────────┐
        │  PostgreSQL  │    │   Redis    │
        │  (Persist)   │    │  Streams   │
        └──────────────┘    └────┬───────┘
                                 │
                                 │ Consumer
                                 ▼
         ┌───────────────────────────────┐
         │   AI Service (Python)         │
         │   - Port: 8082                │
         │   - FastAPI                   │
         │   - Async Processing          │
         └───┬───────────────────────┬───┘
             │                       │
    ┌────────▼────────┐      ┌──────▼──────────┐
    │  ML Detector    │      │  LLM Analyzer   │
    │ (Scikit-learn)  │      │  (Ollama)       │
    │ Isolation Forest│      │  Llama2 Model   │
    └─────────────────┘      └─────────────────┘
             │                       │
             └───────┬───────────────┘
                     │ Results
                     ▼
         ┌───────────────────────────────┐
         │       PostgreSQL              │
         │  (AI Analysis Results)        │
         └───────────────┬───────────────┘
                         │
         ┌───────────────▼───────────────┐
         │   Monitoring Stack            │
         │  - Prometheus (Metrics)       │
         │  - Grafana (Dashboards)       │
         └───────────────────────────────┘
```

---

## Servis Detayları

### 1. Collector Service (Go)

**Sorumluluklar:**
- HTTP endpoint'ler aracılığıyla metrik ve alert toplama
- PostgreSQL'e veri persistance
- Redis Streams'e mesaj publish etme
- Prometheus metrikleri expose etme

**Teknolojiler:**
- **Language**: Go 1.21
- **Framework**: Gin (Web framework)
- **Database**: pgx/v5 (PostgreSQL driver)
- **Cache**: go-redis/v9
- **Monitoring**: prometheus/client_golang

**Endpoints:**
```
GET  /health                      - Health check endpoint
GET  /metrics                     - Prometheus metrics
POST /api/v1/metrics              - Metrik toplama
POST /api/v1/alerts               - Alert toplama
POST /api/v1/auth/token           - JWT token alma (Yeni!)
GET  /api/v1/auth/me              - Kullanıcı bilgisi (Yeni!)
GET  /api/v1/analysis/latest      - Son analiz sonuçları
GET  /docs                        - API documentation
```

**Performance Features:**
- Connection pooling (25 max, 5 min connections)
- Request timeout handling (5s)
- Non-blocking Redis publish
- Prometheus histogram metrics

**File Structure:**
```
collector/
├── main.go                 # Main application entry
├── Dockerfile              # Multi-stage build
├── go.mod                  # Go dependencies
└── internal/
    ├── config/             # Configuration management
    ├── database/           # Database operations
    ├── handlers/           # HTTP handlers
    ├── models/             # Data models
    ├── redis/              # Redis client
    └── server/             # Server setup
```

---

### 2. AI Service (Python)

**Sorumluluklar:**
- Redis Streams'den mesaj consume etme
- Anomali tespiti (Isolation Forest ML modeli)
- LLM ile kök neden analizi
- Analiz sonuçlarını database'e kaydetme
- REST API (analiz sonuçlarını sorgulamak için)

**Teknolojiler:**
- **Language**: Python 3.11
- **Framework**: FastAPI
- **Database**: asyncpg (Async PostgreSQL)
- **Cache**: redis-py (Async)
- **ML**: scikit-learn (Isolation Forest)
- **LLM**: Ollama API (Llama2)
- **Logging**: loguru

**Endpoints:**
```
GET /health                      - Health check
GET /api/v1/analysis/latest      - Son analiz sonuçları
```

**Components:**

#### a) Redis Consumer (`app/redis_client.py`)
- Async message consumption from Redis Streams
- Consumer group support for horizontal scaling
- Message acknowledgment (ACK) mechanism
- Automatic reconnection and error handling

#### b) Anomaly Detector (`app/detector.py`)
- Isolation Forest model wrapper
- Real-time anomaly detection
- Model training from historical data
- Anomaly score calculation

#### c) LLM Analyzer (`app/services/hybrid_analyzer.py`)
- Ollama API integration
- Structured prompt engineering
- JSON response parsing
- Root cause analysis and mitigation recommendations

#### d) Database Wrapper (`app/database.py`)
- Async connection pooling
- CRUD operations (fetch, execute, fetchrow, executemany)
- Retry logic for connection failures
- Query optimization

#### e) Authentication (`app/auth.py`)
- JWT token generation and validation
- Password hashing (bcrypt)
- Scope-based permissions
- Token expiration management

#### f) Rate Limiting (`app/middleware/rate_limit.py`)
- Redis-based sliding window algorithm
- Per-endpoint rate limits
- Client IP identification
- Automatic cleanup

#### g) Logging Middleware (`app/middleware/logging.py`)
- Request/response logging
- Correlation ID tracking
- Performance timing
- Structured logging

#### h) Scheduler (`app/scheduler.py`)
- APScheduler integration
- Daily model retraining (2 AM)
- Model evaluation (every 6 hours)
- Manual trigger support

**File Structure:**
```
ai-service/
├── main.py                           # FastAPI application
├── Dockerfile                        # Python container image
├── requirements.txt                  # Python dependencies
└── app/
    ├── __init__.py
    ├── config.py                     # Configuration settings
    ├── database.py                   # Database connection pool
    ├── redis_client.py               # Redis consumer
    ├── detector.py                   # Anomaly detector
    ├── models/
    │   ├── __init__.py
    │   └── isolation_forest.py       # ML model wrapper
    ├── services/
    │   ├── __init__.py
    │   └── hybrid_analyzer.py        # LLM integration
    └── routers/
        ├── analysis.py               # Analysis endpoints
        └── health.py                 # Health check
```

---

### 3. PostgreSQL Database

**Version**: 15-alpine

**Tablolar:**

#### metrics
```sql
CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
- Stores all incoming metrics
- JSONB for flexible label storage
- GIN index on labels for fast queries

#### alerts
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    alert_name VARCHAR(255) NOT NULL,
    severity VARCHAR(50),
    description TEXT,
    labels JSONB DEFAULT '{}',
    annotations JSONB DEFAULT '{}',
    starts_at TIMESTAMP WITH TIME ZONE,
    ends_at TIMESTAMP WITH TIME ZONE,
    generator_url TEXT,
    status VARCHAR(50) DEFAULT 'firing',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
- Stores Prometheus alerts
- Includes metadata (labels, annotations)
- Status tracking (firing, resolved)

#### ai_analysis_results
```sql
CREATE TABLE ai_analysis_results (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id),
    analysis_type VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    analysis_data JSONB DEFAULT '{}',
    confidence_score DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
- Stores ML and LLM analysis results
- Supports multiple analysis types (anomaly_detection, llm_analysis)
- Foreign key to alerts table

#### model_versions
```sql
CREATE TABLE model_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    algorithm VARCHAR(50),
    parameters JSONB,
    training_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE
);
```
- Tracks ML model versions
- Enables model rollback capability

**Performance Indexes:**
- `idx_metrics_name_ts` - Fast metric queries by name and time
- `idx_metrics_labels` - GIN index for JSONB label searches
- `idx_alerts_status` - Quick status filtering
- `idx_alerts_created_at` - Time-based queries
- `idx_analysis_alert_id` - Analysis lookup by alert

---

### 4. Redis (Streams)

**Version**: 7-alpine

**Purpose**: Message broker between Collector and AI Service

**Stream Structure:**
```
Stream: metrics:raw
Consumer Group: ai_service_group
Consumer: ai-worker-1

Message Format:
{
  "type": "metric" | "alert",
  "data": <JSON_STRING>,
  "ts": <UNIX_TIMESTAMP>
}
```

**Features:**
- Consumer groups for load balancing
- Message acknowledgment (at-least-once delivery)
- Stream trimming (MaxLenApprox: 10000) to prevent memory overflow
- Persistence to disk (RDB + AOF)

---

### 5. Ollama (LLM Service)

**Version**: Latest
**Model**: Llama2 (7B parameters)
**Memory Limit**: 6GB

**Purpose**: Natural language analysis of alerts

**API Usage:**
```
POST /api/generate
{
  "model": "llama2",
  "prompt": "<ALERT_CONTEXT>",
  "stream": false,
  "format": "json"
}
```

**Prompt Template:**
```
Act as a Senior Site Reliability Engineer. Analyze the following system alert:

Alert Name: {alertname}
Severity: {severity}
Description: {description}

Provide a JSON response with:
1. "root_cause": Possible technical root cause
2. "mitigation": Immediate steps to fix
3. "analysis": Brief summary
```

---

### 6. Prometheus

**Version**: Latest
**Scrape Interval**: 15s
**Evaluation Interval**: 15s

**Targets:**
- Collector Service (8080/metrics)
- AI Service (8082/metrics)
- Self monitoring (9090/metrics)
- PostgreSQL (5432)
- Redis (6379)
- Ollama (11434)

**Metrics Collected:**
- `sensus_alerts_received_total` - Total alerts received
- `sensus_metrics_received_total` - Total metrics received
- `sensus_processing_duration_seconds` - Request processing time

**Alert Rules** (`prometheus/alert_rules.yml`):
- **Service Health**: CollectorDown, AIServiceDown, PostgreSQLDown, RedisDown
- **Performance**: HighRequestLatency, VeryHighRequestLatency, SlowDatabaseQueries
- **Traffic**: HighAlertVolume, NoAlertsReceived, HighMetricVolume
- **Resources**: HighMemoryUsage, HighCPUUsage
- **ML**: HighAnomalyRate, NoAnomaliesDetected
- **LLM**: OllamaServiceDown, HighLLMResponseTime

---

### 7. Grafana

**Version**: Latest
**Admin Password**: kam_password

**Datasources:**
1. **Prometheus** (Default)
   - URL: http://prometheus:9090
   - For metrics visualization

2. **PostgreSQL**
   - Database: kam_alerts
   - For alert and AI analysis queries

**Pre-configured Dashboards:**

#### SensusAI Overview (`sensus-overview.json`)
Auto-provisioned dashboard with:
- **Total Alerts Received** (stat panel)
- **Total Metrics Received** (stat panel)
- **Ingestion Rate** (time series, 5m rate)
- **Processing Duration** (95th & 99th percentile)

Panels update automatically every 30 seconds.

**Location**: `grafana/provisioning/dashboards/`
**Auto-load**: On Grafana startup

---

## Veri Akışı

### Metrik İşleme Akışı

```
1. Application Metrics → Collector Service
   POST /api/v1/metrics
   {
     "metric_name": "cpu_usage",
     "metric_value": 85.5,
     "labels": {"host": "server-1"}
   }

2. Collector → PostgreSQL
   INSERT INTO metrics (metric_name, metric_value, labels)

3. Collector → Redis Stream
   XADD metrics:raw * type metric data {...}

4. AI Service Consumer → Redis Stream
   XREADGROUP GROUP ai_service_group ai-worker-1

5. AI Service → Anomaly Detector
   Isolation Forest: predict([85.5]) → is_anomaly: true

6. AI Service → PostgreSQL
   INSERT INTO ai_analysis_results (analysis_type, analysis_data)

7. Grafana/Prometheus → Visualization
```

### Alert İşleme Akışı

```
1. Prometheus AlertManager → Collector Service
   POST /api/v1/alerts
   [{
     "labels": {"alertname": "HighCPU", "severity": "critical"},
     "annotations": {"description": "CPU usage above 90%"}
   }]

2. Collector → PostgreSQL
   INSERT INTO alerts (alert_name, severity, ...) RETURNING id

3. Collector → Redis Stream
   XADD metrics:raw * type alert data {alert_id: X, payload: {...}}

4. AI Service Consumer → Redis Stream
   XREADGROUP ...

5. AI Service → LLM Analyzer (Ollama)
   POST /api/generate
   Prompt: "Analyze alert: HighCPU..."

6. Ollama → Response
   {
     "root_cause": "Memory leak causing process CPU spike",
     "mitigation": "Restart affected service, check memory usage",
     "analysis": "Critical CPU threshold exceeded"
   }

7. AI Service → PostgreSQL
   INSERT INTO ai_analysis_results (alert_id, analysis_type: "llm_analysis")

8. Grafana → Dashboard
   SELECT * FROM ai_analysis_results JOIN alerts
```

---

## Teknoloji Stack

### Backend Services
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Collector | Go | 1.21 | High-performance data ingestion |
| AI Service | Python | 3.11 | ML/LLM processing |
| Web Framework (Go) | Gin | 1.9.1 | HTTP routing |
| Web Framework (Py) | FastAPI | 0.104.1 | Async REST API |

### Data Layer
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Database | PostgreSQL | 15-alpine | Persistent storage |
| Cache/Queue | Redis | 7-alpine | Message streaming |
| DB Driver (Go) | pgx/v5 | 5.5.1 | PostgreSQL connection |
| DB Driver (Py) | asyncpg | 0.29.0 | Async PostgreSQL |

### AI/ML
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| LLM Service | Ollama | Latest | LLM inference |
| Model | Llama2 | 7B | Natural language analysis |
| ML Library | scikit-learn | 1.3.2 | Anomaly detection |
| Algorithm | Isolation Forest | - | Unsupervised outlier detection |

### Monitoring
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Metrics | Prometheus | Latest | Metrics collection |
| Visualization | Grafana | Latest | Dashboards |
| Metrics Lib (Go) | prometheus/client_golang | 1.18.0 | Metrics export |
| Metrics Lib (Py) | prometheus-client | 0.19.0 | Metrics export |

### Infrastructure
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Containerization | Docker | - | Container runtime |
| Orchestration | Docker Compose | 3.8 | Multi-container management |
| Networking | Bridge Network | - | Container communication |

---

## Performans Optimizasyonları

### Database Level

1. **Connection Pooling**
   - Go: 25 max, 5 min connections
   - Python: 20 max, 5 min connections
   - Connection lifetime: 1 hour (Go)

2. **Indexing Strategy**
   ```sql
   -- Time-series optimized indexes
   CREATE INDEX idx_metrics_name_ts ON metrics (metric_name, timestamp DESC);

   -- JSONB search optimization
   CREATE INDEX idx_metrics_labels ON metrics USING GIN (labels);

   -- Status filtering
   CREATE INDEX idx_alerts_status ON alerts (status);
   ```

3. **Query Optimization**
   - Prepared statements
   - Query timeout limits (10s)
   - LIMIT clauses on time-series queries

### Redis Level

1. **Stream Trimming**
   - MaxLenApprox: 10000 messages
   - Prevents memory overflow
   - Balances history retention with memory

2. **Consumer Groups**
   - Enables horizontal scaling
   - Load balancing across consumers
   - At-least-once delivery guarantee

3. **Connection Pooling**
   - Pool size: 20 connections
   - Timeout: 3s read/write
   - Connection reuse

### Application Level

1. **Async Processing** (Python)
   - asyncio event loop
   - Non-blocking I/O
   - Concurrent request handling

2. **Goroutines** (Go)
   - Lightweight concurrency
   - Efficient resource utilization

3. **Timeout Handling**
   - Context-based cancellation (Go)
   - Request timeouts (5s)
   - Health check timeouts (2s)

4. **Batching**
   - Redis consume batch: 10 messages
   - Database executemany for bulk inserts

### ML Model Optimization

1. **Model Persistence**
   - Joblib serialization
   - Disk caching
   - Lazy loading

2. **Parallel Processing**
   - n_jobs=-1 (use all CPU cores)
   - Executor for blocking operations
   - Prevents event loop blocking

---

## Güvenlik

### Network Security
- Internal Docker bridge network
- No external exposure except necessary ports
- Service-to-service communication within network

### Authentication & Authorization ✅
- **JWT Authentication**: Implemented in AI Service
  - Token-based authentication
  - Bearer token in Authorization header
  - Configurable expiration (default: 30 minutes)
  - Scope-based permissions (read, write, admin)

**Usage:**
```bash
# Login
curl -X POST http://localhost:8082/api/v1/auth/token -u admin:secret

# Use token
curl -H "Authorization: Bearer <token>" http://localhost:8082/api/v1/analysis/latest
```

### Rate Limiting ✅
- **Redis-based sliding window algorithm**
  - Per-endpoint limits:
    - `/api/v1/metrics`: 100 req/min
    - `/api/v1/alerts`: 50 req/min
    - `/api/v1/analysis`: 30 req/min
    - Default: 60 req/min
  - Client IP identification
  - X-Forwarded-For support (proxy)
  - Response headers: X-RateLimit-Limit, X-RateLimit-Remaining
  - 429 status code on limit exceeded

### Input Validation
- JSON schema validation (Gin binding, Pydantic)
- SQL injection prevention (parameterized queries)
- Input sanitization
- Type checking (TypeScript-like for Python with Pydantic)

### Container Security
- Non-root user in containers (collector: kamuser)
- Minimal base images (Alpine Linux)
- Multi-stage builds (reduces attack surface)
- Secrets via environment variables (`.env.example` template)

### Implemented Security Features ✅
- [x] JWT authentication for API endpoints
- [x] Rate limiting (Redis-based)
- [x] Input validation (Pydantic, Gin binding)
- [x] SQL injection protection (parameterized queries)
- [x] Password hashing (bcrypt)
- [x] Request correlation IDs
- [x] Security scanning (Trivy in CI/CD)

### Recommendations for Production
- [ ] Enable TLS/SSL for all connections
- [ ] Use secrets manager (HashiCorp Vault, AWS Secrets Manager)
- [ ] Implement RBAC (Role-Based Access Control)
- [ ] Add API key authentication for external sources
- [ ] Enable PostgreSQL SSL connections
- [ ] Implement audit logging
- [ ] Add Web Application Firewall (WAF)
- [ ] Set up Intrusion Detection System (IDS)

---

## Ölçeklenebilirlik

### Horizontal Scaling

#### Collector Service
- **Stateless design**: Can be replicated N times
- **Load Balancer**: Nginx/HAProxy in front
- **Session**: No session state (stateless HTTP)
- **Database**: Connection pooling handles concurrent requests

#### AI Service
- **Consumer Groups**: Multiple consumers in same group
- **Message Distribution**: Redis automatically load balances
- **Independent Workers**: Scale by adding more consumer instances
- **No Shared State**: Each worker processes independently

### Vertical Scaling

#### Database
- Increase PostgreSQL resources (CPU, RAM)
- Enable connection pooling
- Optimize queries and indexes
- Consider read replicas for read-heavy workloads

#### Ollama/LLM
- Increase memory limit (currently 6GB)
- Use GPU acceleration for faster inference
- Model quantization for smaller memory footprint

### Partitioning Strategies

#### Database Partitioning
```sql
-- Time-based partitioning for metrics table (example)
CREATE TABLE metrics_2024_01 PARTITION OF metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE metrics_2024_02 PARTITION OF metrics
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

#### Redis Sharding
- Use multiple Redis instances for different streams
- Partition by metric type or alert severity

### Caching Strategies
- Redis cache for frequent database queries
- ML model caching (in-memory after first load)
- LLM response caching for identical alerts

### Deployment Architectures

#### Single Node (Current)
```
Docker Compose on single host
Suitable for: Development, small-scale production
```

#### Multi-Node (Kubernetes)
```
- Collector: Deployment (3 replicas) + Service + HPA
- AI Service: Deployment (2 replicas) + Service + HPA
- PostgreSQL: StatefulSet + PVC
- Redis: StatefulSet + PVC
- Prometheus: StatefulSet
- Grafana: Deployment + Service
```

#### Cloud-Native (AWS Example)
```
- Collector: ECS Fargate (auto-scaling)
- AI Service: ECS Fargate (auto-scaling)
- PostgreSQL: RDS PostgreSQL (Multi-AZ)
- Redis: ElastiCache Redis (cluster mode)
- Ollama: EC2 with GPU (p3.2xlarge)
- Monitoring: CloudWatch + Managed Grafana
```

---

## Monitoring & Observability

### Metrics
- Service-level metrics (request count, latency, errors)
- Business metrics (alerts processed, anomalies detected)
- Infrastructure metrics (CPU, memory, disk, network)

### Logging
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized logging (consider ELK/EFK stack)

### Tracing
- Consider implementing distributed tracing (Jaeger, Tempo)
- Track request flow across services

### Alerting
- Prometheus AlertManager for infrastructure alerts
- Custom alerts for business logic (e.g., high anomaly rate)

---

## Bakım ve Operasyon

### Backup Strategy
- PostgreSQL: Daily automated backups
- Redis: RDB snapshots + AOF persistence
- ML Models: Version control for trained models

### Update Procedures
- Rolling updates for stateless services
- Blue-green deployment for zero-downtime
- Database migrations with version control (e.g., Flyway, Alembic)

### Health Checks
- Liveness probes (service is running)
- Readiness probes (service is ready to accept traffic)
- Dependency checks (database, Redis, Ollama)

---

## Gelecek İyileştirmeler

### Short-term
- [ ] Add unit and integration tests (>80% coverage)
- [ ] Implement CI/CD pipeline (GitHub Actions, GitLab CI)
- [ ] Add API documentation (Swagger/OpenAPI)
- [ ] Implement graceful shutdown
- [ ] Add rate limiting

### Mid-term
- [ ] Multi-model support (different ML algorithms)
- [ ] Model retraining scheduler (automatic retraining)
- [ ] Alerting on anomaly detection
- [ ] Advanced LLM features (RAG, fine-tuning)
- [ ] A/B testing for models

### Long-term
- [ ] Kubernetes deployment
- [ ] Multi-tenancy support
- [ ] Real-time streaming dashboards (WebSockets)
- [ ] Advanced analytics (trend analysis, forecasting)
- [ ] Auto-remediation (execute fix commands automatically)

---

## Kaynaklar

### Documentation
- [Go Gin Framework](https://gin-gonic.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis Streams](https://redis.io/docs/data-types/streams/)
- [Ollama](https://ollama.ai/docs)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)

### ML/AI
- [Scikit-learn Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- [Anomaly Detection Techniques](https://en.wikipedia.org/wiki/Anomaly_detection)

---

**Versiyon**: 1.0
**Son Güncelleme**: 2024-02-07
**Yazar**: SensusAI Development Team
