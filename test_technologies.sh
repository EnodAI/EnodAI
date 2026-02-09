#!/bin/bash
# TECHNOLOGY TEST: Farklı teknolojilerin alert'lerini test et
# LLM'in teknoloji-spesifik terimleri doğru kullanıp kullanmadığını kontrol et

COLLECTOR_URL="http://localhost:8080/api/v1/alerts"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "🔧 TECHNOLOGY TEST: Farklı Stack Alertleri"
echo "=========================================="
echo ""

# ==================== 1. REDIS ====================
echo "📍 TEST 1: Redis Memory Eviction"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "RedisMemoryPressure",
      "severity": "critical",
      "instance": "redis-cache-1:6379",
      "job": "redis"
    },
    "annotations": {
      "description": "Redis memory usage CRITICAL on redis-cache-1! Used memory: 15.8GB/16GB (98.7%). Eviction policy: allkeys-lru. Evicted keys last minute: 12,450 keys. Hit rate dropped from 95% to 67%. Client connections: 850/1000. Blocked clients: 25. Keyspace: 8.2M keys. Fragmentation ratio: 1.45."
    },
    "startsAt": "'$TIMESTAMP'"
  }]'
echo "✅ Redis alert sent (LLM should mention: eviction, allkeys-lru, fragmentation)"
echo ""
sleep 3

# ==================== 2. NGINX ====================
echo "📍 TEST 2: Nginx 502 Bad Gateway"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "NginxBackendFailure",
      "severity": "critical",
      "instance": "nginx-lb-1:80",
      "job": "nginx"
    },
    "annotations": {
      "description": "CRITICAL: Nginx returning 502 errors on nginx-lb-1! Error rate: 45% (2,450 errors/min). Upstream: backend-app-pool. Failed backends: app-3 (connection refused), app-5 (timeout). Active connections: 1,200. Waiting: 450. Writing: 320. Client errors: connection timeout after 60s."
    },
    "startsAt": "'$TIMESTAMP'"
  }]'
echo "✅ Nginx alert sent (LLM should mention: upstream, backend pool, 502)"
echo ""
sleep 3

# ==================== 3. KAFKA ====================
echo "📍 TEST 3: Kafka Consumer Lag"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "KafkaConsumerLag",
      "severity": "warning",
      "instance": "kafka-broker-2:9092",
      "job": "kafka"
    },
    "annotations": {
      "description": "Kafka consumer lag increasing on kafka-broker-2. Topic: user-events. Partition: 5. Consumer group: analytics-processor. Current offset: 1,245,000. Log end offset: 1,820,000. Lag: 575,000 messages (growing at 5,000 msg/sec). Consumer throughput: 2,000 msg/sec. ETA to catch up: 115 seconds IF no new messages."
    },
    "startsAt": "'$TIMESTAMP'"
  }]'
echo "✅ Kafka alert sent (LLM should mention: consumer lag, partition, offset)"
echo ""
sleep 3

# ==================== 4. ELASTICSEARCH ====================
echo "📍 TEST 4: Elasticsearch Cluster Yellow"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "ElasticsearchClusterYellow",
      "severity": "warning",
      "instance": "es-master-1:9200",
      "job": "elasticsearch"
    },
    "annotations": {
      "description": "Elasticsearch cluster status YELLOW on es-master-1. Cluster: production-logs. Unassigned shards: 45 (all replicas). Active shards: 1,250. Relocating: 0. Initializing: 12. Missing nodes: es-data-3 (lost connection 5 min ago). Heap usage: 85% on es-data-2. JVM GC time: 8 seconds in last minute."
    },
    "startsAt": "'$TIMESTAMP'"
  }]'
echo "✅ Elasticsearch alert sent (LLM should mention: shards, replicas, heap)"
echo ""
sleep 3

# ==================== 5. RABBITMQ ====================
echo "📍 TEST 5: RabbitMQ Queue Buildup"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "RabbitMQQueueBuildup",
      "severity": "critical",
      "instance": "rabbitmq-1:5672",
      "job": "rabbitmq"
    },
    "annotations": {
      "description": "CRITICAL: RabbitMQ queue buildup on rabbitmq-1! Queue: email-notifications. Messages: 125,000 (growing at 500 msg/sec). Consumers: 3 (should be 10). Consumer utilization: 45%. Publish rate: 650 msg/sec. Consume rate: 150 msg/sec. Memory usage: 3.2GB/4GB. Disk free space: 12GB (alarm threshold: 10GB)."
    },
    "startsAt": "'$TIMESTAMP'"
  }]'
echo "✅ RabbitMQ alert sent (LLM should mention: queue, consumer, publish/consume rate)"
echo ""
sleep 3

# ==================== 6. CASSANDRA ====================
echo "📍 TEST 6: Cassandra Read Latency"
curl -X POST $COLLECTOR_URL \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "CassandraHighLatency",
      "severity": "warning",
      "instance": "cassandra-node-2:9042",
      "job": "cassandra"
    },
    "annotations": {
      "description": "Cassandra read latency high on cassandra-node-2. Keyspace: user_profiles. Table: user_data. P99 read latency: 850ms (was 45ms). Pending compactions: 125. SSTable count: 450 (recommended: <100). Bloom filter false positive rate: 12%. Heap usage: 28GB/31GB. GC pause time: 3.5s in last minute."
    },
    "startsAt": "'$TIMESTAMP'"
  }]'
echo "✅ Cassandra alert sent (LLM should mention: compaction, SSTable, bloom filter)"
echo ""
sleep 3

# ==================== SUMMARY ====================
echo ""
echo "=========================================="
echo "📊 TECHNOLOGY TEST SUMMARY"
echo "=========================================="
echo ""
echo "Technologies Tested:"
echo "  ✓ Redis (eviction, memory, fragmentation)"
echo "  ✓ Nginx (502, upstream, backend)"
echo "  ✓ Kafka (consumer lag, partition, offset)"
echo "  ✓ Elasticsearch (shards, replicas, heap)"
echo "  ✓ RabbitMQ (queue, consumer, publish rate)"
echo "  ✓ Cassandra (compaction, SSTable, bloom filter)"
echo ""
echo "Total Alerts: 6"
echo "Expected LLM Analyses: 6"
echo ""
echo "⏳ Wait 3-5 minutes for Ollama to process..."
echo ""
echo "🧪 TEST SUCCESS CRITERIA:"
echo "  - LLM should use CORRECT technology-specific terms"
echo "  - Redis: Should NOT mention MongoDB WiredTiger!"
echo "  - Nginx: Should NOT mention database connections!"
echo "  - Each analysis should be contextually appropriate"
echo ""
echo "Check Dashboard: http://localhost:3000"
echo ""
