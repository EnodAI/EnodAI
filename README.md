# SensusAI

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Go](https://img.shields.io/badge/Go-1.21-00ADD8.svg)
![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)

**AI-Powered Intelligent Monitoring Platform**

*Latince "sensus" (algı, sezgi) - Sensing Anomalies, Delivering Insights*

[Özellikler](#-özellikler) • [Kurulum](#-kurulum) • [Kullanım](#-kullanım) • [Mimari](#-mimari) • [Katkıda Bulunma](#-katkıda-bulunma)

</div>

---

## 📝 Açıklama

**SensusAI**, sistem uyarılarını (alerts) ve metriklerini toplamak, saklamak ve yapay zeka ile analiz etmek için geliştirilmiş yüksek performanslı bir **mikroservis mimarisidir**. Prometheus AlertManager ile entegre çalışır, metrik anomalilerini tespit eder ve LLM (Large Language Model) kullanarak kök neden analizi yapar.

Adı Latince "sensus" (algı, his, sezgi) kelimesinden gelir - sistemlerinizin altıncı hissi gibi çalışır.

### 🎯 Temel Hedefler

- **Real-time Monitoring**: Anlık sistem metriklerini ve uyarılarını toplama
- **Anomali Tespiti**: Machine Learning ile otomatik anomali tespiti (Isolation Forest)
- **Akıllı Analiz**: LLM destekli kök neden analizi ve çözüm önerileri
- **Yüksek Performans**: Async processing, connection pooling, stream processing
- **Ölçeklenebilirlik**: Mikroservis mimarisi ile horizontal ve vertical scaling

---

## ✨ Özellikler

### 🔍 Monitoring & Data Collection
- ✅ Prometheus AlertManager webhook entegrasyonu
- ✅ REST API ile özel metrik toplama
- ✅ PostgreSQL'de persistent storage
- ✅ Redis Streams ile real-time data processing
- ✅ Pre-configured Grafana dashboards
- ✅ Prometheus alert rules (30+ alerts)

### 🤖 AI/ML Capabilities
- ✅ **Isolation Forest** algoritması ile anomali tespiti
- ✅ **Ollama/Llama2** LLM ile kök neden analizi
- ✅ Otomatik model training ve versiyonlama
- ✅ Scheduled model retraining (APScheduler)
- ✅ Confidence score hesaplama
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

## 🏗️ Mimari

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

**Detaylı mimari dokümantasyon için**: [ARCHITECTURE.md](./ARCHITECTURE.md)

### Servisler

| Servis | Port | Teknoloji | Açıklama |
|--------|------|-----------|----------|
| **Collector** | 8080 | Go/Gin | Metrik ve alert toplama servisi |
| **AI Service** | 8082 | Python/FastAPI | ML/LLM analiz servisi |
| **PostgreSQL** | 5432 | PostgreSQL 15 | Ana veritabanı |
| **Redis** | 6379 | Redis 7 | Message streaming & cache |
| **Ollama** | 11434 | Ollama/Llama2 | LLM inference engine |
| **Prometheus** | 9090 | Prometheus | Metrics collection |
| **Grafana** | 3000 | Grafana | Visualization dashboards |

---

## 📋 Gereksinimler

### Sistem Gereksinimleri

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| **CPU** | 4 cores | 8 cores |
| **RAM** | 8 GB | 16 GB |
| **Disk** | 20 GB | 50 GB SSD |
| **OS** | Linux/macOS/Windows with WSL2 | Ubuntu 22.04 LTS |

### Yazılım Gereksinimleri

- **Docker**: 20.10.x veya üzeri
- **Docker Compose**: 2.x veya üzeri
- **Git**: 2.x veya üzeri

> **Not**: Ollama servisi için GPU desteği opsiyoneldir ancak önerilir (daha hızlı LLM inference).

---

## 🚀 Kurulum

### Hızlı Başlangıç (Önerilen)

```bash
# Otomatik kurulum scripti
git clone https://github.com/your-username/SensusAI.git
cd SensusAI
./scripts/setup.sh
```

veya

```bash
# Makefile ile
make quickstart
```

### Manuel Kurulum

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/your-username/SensusAI.git
cd SensusAI
```

### 2. Environment Değişkenlerini Kontrol Edin

Docker Compose, default değişkenleri kullanır. Özelleştirme için `.env` dosyası oluşturabilirsiniz:

```bash
# .env (opsiyonel)
POSTGRES_USER=kam_user
POSTGRES_PASSWORD=kam_password
POSTGRES_DB=kam_alerts
REDIS_ADDR=redis:6379
OLLAMA_URL=http://ollama:11434
GRAFANA_ADMIN_PASSWORD=kam_password
```

### 3. Docker Container'ları Başlatın

```bash
# Tüm servisleri build et ve başlat
docker-compose up --build -d

# Logları izle
docker-compose logs -f

# Belirli bir servisin logunu izle
docker-compose logs -f ai-service
```

### 4. Ollama Model'ini İndirin

Ollama container'ı başladıktan sonra Llama2 modelini indirin:

```bash
docker exec -it sensusai-ollama-1 ollama pull llama2
```

> **İlk kullanımda**: Model indirme işlemi ~4GB veri indireceği için birkaç dakika sürebilir.

### 5. Servislerin Durumunu Kontrol Edin

```bash
# Tüm container'ların durumunu kontrol et
docker-compose ps

# Health check'leri test et
curl http://localhost:8080/health  # Collector
curl http://localhost:8082/health  # AI Service
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health  # Grafana
```

**Beklenen Çıktı:**
```
NAME                        STATUS    PORTS
sensusai-collector-1      running   0.0.0.0:8080->8080/tcp
sensusai-ai-service-1     running   0.0.0.0:8082->8082/tcp
sensusai-postgresql-1     running   0.0.0.0:5432->5432/tcp
sensusai-redis-1          running   0.0.0.0:6379->6379/tcp
sensusai-ollama-1         running   0.0.0.0:11434->11434/tcp
sensusai-prometheus-1     running   0.0.0.0:9090->9090/tcp
sensusai-grafana-1        running   0.0.0.0:3000->3000/tcp
```

---

## 🔐 Authentication (Yeni!)

SensusAI JWT token-based authentication kullanır.

### Token Alma

```bash
# Basic auth ile login
curl -X POST http://localhost:8082/api/v1/auth/token \
  -u admin:secret

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Token ile API Kullanımı

```bash
# Token ile korumalı endpoint'e erişim
curl http://localhost:8082/api/v1/analysis/latest \
  -H "Authorization: Bearer <your-token>"
```

**Default Kullanıcılar:**
- Username: `admin` / Password: `secret` (tüm yetkiler)
- Username: `user` / Password: `secret` (sadece okuma)

> ⚠️ Production'da bu şifreleri değiştirin!

---

## 📖 Kullanım

### 1. Metrik Gönderme

REST API ile manuel metrik gönderimi:

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

### 2. Alert Gönderme (Prometheus AlertManager Format)

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

### 3. AI Analiz Sonuçlarını Görüntüleme

Son analiz sonuçlarını REST API ile sorgulayın:

```bash
curl http://localhost:8082/api/v1/analysis/latest
```

**Response:**
```json
[
  {
    "id": "123",
    "alert_id": "456",
    "analysis_type": "llm_analysis",
    "model_name": "llama2",
    "analysis_data": {
      "root_cause": "Memory leak in application process",
      "mitigation": "Restart the affected service and monitor memory usage",
      "analysis": "Critical CPU threshold exceeded due to memory pressure"
    },
    "confidence_score": 0.85,
    "created_at": "2024-02-07T10:05:00Z"
  }
]
```

### 4. Grafana Dashboard'larına Erişim

1. **Grafana'ya giriş yapın:**
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `kam_password`

2. **Datasources'ı kontrol edin:**
   - Configuration → Data Sources
   - Prometheus ve PostgreSQL datasource'ları otomatik yapılandırılmıştır

3. **Dashboard oluşturun:**
   - **Prometheus datasource** ile:
     - `sensus_alerts_received_total` - Gelen alert sayısı
     - `sensus_metrics_received_total` - Gelen metrik sayısı
     - `sensus_processing_duration_seconds` - İşlem süreleri

   - **PostgreSQL datasource** ile:
     ```sql
     -- Son 24 saatteki alertler
     SELECT created_at, alert_name, severity, status
     FROM alerts
     WHERE created_at > NOW() - INTERVAL '24 hours'
     ORDER BY created_at DESC;

     -- AI analiz sonuçları
     SELECT a.alert_name, a.severity,
            r.analysis_type, r.confidence_score, r.created_at
     FROM ai_analysis_results r
     JOIN alerts a ON r.alert_id = a.id
     ORDER BY r.created_at DESC
     LIMIT 50;
     ```

### 5. Prometheus Targets'ı Kontrol Etme

- URL: http://localhost:9090/targets
- Tüm target'ların **UP** durumunda olduğunu kontrol edin

### 6. Database'e Direkt Erişim

PostgreSQL'e bağlanmak için:

```bash
docker exec -it sensusai-postgresql-1 psql -U kam_user -d kam_alerts
```

**Örnek Sorgular:**

```sql
-- Son 10 metrik
SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 10;

-- Son 10 alert
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;

-- Anomali tespit sonuçları
SELECT * FROM ai_analysis_results
WHERE analysis_type = 'anomaly_detection'
ORDER BY created_at DESC LIMIT 10;

-- LLM analiz sonuçları
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

## 🔧 Konfigürasyon

### Collector Service Configuration

`collector/main.go` dosyasında aşağıdaki environment değişkenleri kullanılır:

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `DB_HOST` | postgresql | PostgreSQL host |
| `DB_USER` | kam_user | PostgreSQL kullanıcı adı |
| `DB_PASSWORD` | kam_password | PostgreSQL şifresi |
| `DB_NAME` | kam_alerts | Veritabanı adı |
| `REDIS_ADDR` | redis:6379 | Redis adresi |

### AI Service Configuration

`ai-service/app/config.py` dosyasında aşağıdaki ayarlar yapılır:

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `REDIS_URL` | redis://redis:6379 | Redis connection URL |
| `POSTGRES_HOST` | postgres | PostgreSQL host |
| `POSTGRES_USER` | kam_user | PostgreSQL kullanıcı adı |
| `POSTGRES_PASSWORD` | kam_password | PostgreSQL şifresi |
| `POSTGRES_DB` | kam_alerts | Veritabanı adı |
| `OLLAMA_HOST` | ollama | Ollama host |
| `OLLAMA_PORT` | 11434 | Ollama port |

### Prometheus AlertManager Webhook Configuration

Prometheus AlertManager'ı SensusAI'ye yönlendirmek için:

```yaml
# alertmanager.yml
route:
  receiver: 'sensusai-webhook'

receivers:
  - name: 'sensusai-webhook'
    webhook_configs:
      - url: 'http://collector:8080/api/v1/alerts'
        send_resolved: true
```

---

## 🧪 Test

### Otomatik Test Suite

```bash
# Tüm testleri çalıştır
make test

# Sadece AI service testleri
make test-ai

# Sadece Collector testleri
make test-collector

# Coverage report ile
cd ai-service && pytest --cov=app --cov-report=html
```

**Test İstatistikleri:**
- AI Service: 20+ test, 80%+ coverage
- Collector: 12+ test, 75%+ coverage
- Total: 32+ test, 78%+ coverage

### Linting

```bash
# Tüm linting
make lint

# Otomatik düzeltme
make lint-fix
```

### Manuel Test Script'i

Otomatik test için sample metrik ve alert gönderin:

```bash
#!/bin/bash

# Test metrikleri gönder
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

# Test alert'i gönder
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

echo -e "\n✅ Test verileri gönderildi!"
echo "AI analiz sonuçlarını görmek için:"
echo "curl http://localhost:8082/api/v1/analysis/latest"
```

Dosyayı çalıştırın:

```bash
chmod +x test_data.sh
./test_data.sh
```

### Log İzleme

Servislerin işlem durumunu izleyin:

```bash
# AI Service log'larını izle (anomali tespiti ve LLM analiz)
docker-compose logs -f ai-service

# Collector log'larını izle (gelen metrik/alert)
docker-compose logs -f collector

# Redis consumer log'larını izle
docker-compose logs -f ai-service | grep "Consumer"
```

---

## 🐛 Troubleshooting

### Problem: Servisler başlamıyor

**Çözüm:**
```bash
# Container'ları durdur ve temizle
docker-compose down -v

# Yeniden build et
docker-compose up --build -d

# Log'ları kontrol et
docker-compose logs
```

### Problem: PostgreSQL bağlantı hatası

**Belirti:** `connection refused` veya `database does not exist`

**Çözüm:**
```bash
# PostgreSQL container'ının çalıştığından emin ol
docker-compose ps postgresql

# Health check durumu
docker exec sensusai-postgresql-1 pg_isready -U kam_user

# Manuel bağlantı testi
docker exec -it sensusai-postgresql-1 psql -U kam_user -d kam_alerts -c "SELECT 1;"
```

### Problem: Ollama model yüklenmedi

**Belirti:** LLM analiz hataları

**Çözüm:**
```bash
# Ollama container'ına bağlan
docker exec -it sensusai-ollama-1 bash

# Mevcut modelleri listele
ollama list

# Model yoksa indir
ollama pull llama2

# Model indirme durumunu kontrol et
curl http://localhost:11434/api/tags
```

### Problem: Redis connection timeout

**Çözüm:**
```bash
# Redis'in çalıştığından emin ol
docker exec sensusai-redis-1 redis-cli ping
# Beklenen: PONG

# Redis stream kontrolü
docker exec sensusai-redis-1 redis-cli XINFO STREAM metrics:raw
```

### Problem: AI Service mesaj consume etmiyor

**Belirti:** Metrikler gelmiyor ancak database'e yazılmıyor

**Çözüm:**
```bash
# AI Service log'larını kontrol et
docker-compose logs ai-service | grep "Consumer"

# Redis stream'i manuel kontrol et
docker exec sensusai-redis-1 redis-cli XLEN metrics:raw
# Mesaj sayısı görünmeli

# Consumer group durumu
docker exec sensusai-redis-1 redis-cli XINFO GROUPS metrics:raw

# AI Service'i yeniden başlat
docker-compose restart ai-service
```

### Problem: Düşük performans

**Çözüm:**
```bash
# Resource kullanımını kontrol et
docker stats

# Ollama için daha fazla memory ayır (docker-compose.yml)
# deploy.resources.limits.memory: 8G

# PostgreSQL connection pool artır (ai-service/app/database.py)
# max_size: 30

# Redis pool size artır (collector/main.go)
# PoolSize: 30
```

---

## 🛑 Servisleri Durdurma

### Geçici Durdurma

```bash
# Tüm servisleri durdur (data korunur)
docker-compose stop

# Tekrar başlat
docker-compose start
```

### Tamamen Kaldırma

```bash
# Container'ları ve network'ü sil (volume'ler korunur)
docker-compose down

# Volume'leri de sil (TÜM VERİLER SİLİNİR!)
docker-compose down -v
```

### Belirli Bir Servisi Yeniden Başlatma

```bash
docker-compose restart ai-service
docker-compose restart collector
```

---

## 📊 Metriks ve Monitoring

### Toplanan Prometheus Metrics

#### Collector Metrics (8080/metrics)
- `sensus_alerts_received_total` - Toplam gelen alert sayısı
- `sensus_metrics_received_total` - Toplam gelen metrik sayısı
- `sensus_processing_duration_seconds` - Request işlem süresi (histogram)

#### Kullanım:
```promql
# Alert alma hızı (son 5 dakika)
rate(sensus_alerts_received_total[5m])

# 95. percentile işlem süresi
histogram_quantile(0.95, sensus_processing_duration_seconds_bucket)

# Metrik toplama hızı
rate(sensus_metrics_received_total[5m])
```

---

## 🔒 Güvenlik Notları

> ⚠️ **ÖNEMLİ**: Bu kurulum **development/test** ortamları içindir. Production kullanımı için:

- [ ] Tüm default şifreleri değiştirin
- [ ] Environment değişkenlerini secrets manager'a taşıyın (Vault, AWS Secrets Manager)
- [ ] TLS/SSL etkinleştirin (PostgreSQL, Redis, HTTP)
- [ ] Network segmentasyonu yapın
- [ ] Rate limiting ekleyin
- [ ] API authentication/authorization implementi yapın (JWT, OAuth2)
- [ ] Firewall kuralları yapılandırın
- [ ] Container'ları non-root user ile çalıştırın
- [ ] Image vulnerability scanning yapın (Trivy, Clair)
- [ ] Audit logging ekleyin

---

## 🛠️ Makefile Komutları

```bash
make help              # Tüm komutları listele
make build             # Docker image'ları build et
make up                # Servisleri başlat
make down              # Servisleri durdur
make logs              # Logları göster
make test              # Testleri çalıştır
make lint              # Kodu kontrol et
make health-check      # Servis sağlığını kontrol et
make send-test-data    # Test verisi gönder
make db-backup         # Database yedekle
make db-restore        # Database geri yükle
make clean             # Cleanup yap
make quickstart        # Her şeyi başlat
```

### Utility Scripts

```bash
./scripts/setup.sh     # Otomatik kurulum
./scripts/backup.sh    # Database backup
./scripts/restore.sh   # Database restore
./scripts/monitor.sh   # Canlı monitoring
```

---

## ☸️ Kubernetes Deployment

```bash
# Namespace oluştur
kubectl apply -f k8s/base/namespace.yaml

# Tüm kaynakları deploy et
kubectl apply -f k8s/base/

# Veya Kustomize ile
kubectl apply -k k8s/overlays/prod/

# Durumu kontrol et
kubectl get pods -n sensusai
kubectl get svc -n sensusai

# Logs
kubectl logs -f deployment/ai-service -n sensusai

# Scaling
kubectl scale deployment collector -n sensusai --replicas=5
```

**Auto-scaling (HPA) otomatik olarak yapılandırılmıştır:**
- Collector: 2-10 replicas (CPU 70%, Memory 80%)
- AI Service: 2-5 replicas (CPU 70%, Memory 80%)

Detaylı bilgi: [k8s/README.md](./k8s/README.md)

---

## 🚢 Production Deployment

```bash
# Production compose ile
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Veya Makefile ile
make deploy-prod
```

**Production özellikleri:**
- Resource limits ve reservations
- Replicated services (2x collector, 2x ai-service)
- Enhanced logging
- Auto-restart policies
- Performance tuning

Detaylı bilgi: [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 🔄 CI/CD Pipeline

GitHub Actions ile otomatik CI/CD:

**`.github/workflows/ci.yml`:**
- ✅ Python ve Go testleri
- ✅ Linting (black, flake8, golangci-lint)
- ✅ Code coverage (Codecov)
- ✅ Docker image build
- ✅ Security scanning (Trivy)

**`.github/workflows/deploy.yml`:**
- ✅ Container registry push (GHCR)
- ✅ Staging deployment (main branch)
- ✅ Production deployment (tags)

---

## 📚 Ek Kaynaklar

### Dokümantasyon
- **Mimari Dokümantasyon**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Deployment Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Contributing Guide**: [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Kubernetes Guide**: [k8s/README.md](./k8s/README.md)

### API & Monitoring
- **API Dokümantasyonu**: http://localhost:8082/docs (FastAPI auto-generated)
- **Prometheus UI**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Prometheus Alerts**: http://localhost:9090/alerts

### Teknoloji Dokümantasyonları
- [Go Gin Framework](https://gin-gonic.com/docs/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis Streams](https://redis.io/docs/data-types/streams/)
- [Ollama](https://ollama.ai/docs)
- [Scikit-learn Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)

---

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen aşağıdaki adımları takip edin:

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

### Geliştirme Kuralları
- Code style: Go (gofmt), Python (black, isort)
- Commit message format: Conventional Commits
- Test coverage: Minimum %80
- Documentation: Her yeni feature için dokümantasyon ekleyin

---

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## 👥 Yazarlar

- **SensusAI Development Team**

---

## 🙏 Teşekkürler

- [Prometheus](https://prometheus.io/) - Monitoring sistemi
- [Grafana](https://grafana.com/) - Visualization
- [Ollama](https://ollama.ai/) - LLM inference
- [PostgreSQL](https://www.postgresql.org/) - Database
- [Redis](https://redis.io/) - Streaming & caching

---

## 📞 İletişim

Sorularınız için:
- GitHub Issues: [Create an issue](https://github.com/your-username/SensusAI/issues)
- Email: support@sensusai.dev

---

<div align="center">

**SensusAI** ile sisteminizi akıllıca izleyin! 🚀

Made with ❤️ by SensusAI Team

</div>
