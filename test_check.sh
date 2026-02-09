#!/bin/bash
# QUICK CHECK: Sistemin durumunu hızlıca kontrol et

echo "🔍 QUICK SYSTEM CHECK"
echo "===================="
echo ""

# Database stats
echo "📊 DATABASE STATS:"
docker compose exec -T postgresql psql -U enod_user -d enod_monitoring -c "
SELECT
  '🚨 Active Alerts' as metric,
  COUNT(*) as value
FROM alerts
WHERE status = 'firing'
UNION ALL
SELECT
  '📦 Total Alerts',
  COUNT(*)
FROM alerts
UNION ALL
SELECT
  '✅ Unique Alerts',
  COUNT(DISTINCT CASE WHEN is_duplicate = FALSE THEN id END)
FROM alerts
UNION ALL
SELECT
  '🔄 Duplicates',
  COUNT(CASE WHEN is_duplicate = TRUE THEN 1 END)
FROM alerts
UNION ALL
SELECT
  '🧠 LLM Analyses',
  COUNT(*)
FROM ai_analysis_results
WHERE analysis_type = 'llm_analysis'
UNION ALL
SELECT
  '🤖 AI Anomalies',
  COUNT(*)
FROM metrics
WHERE is_anomaly = TRUE
UNION ALL
SELECT
  '📊 Total Metrics',
  COUNT(*)
FROM metrics;
" 2>/dev/null

echo ""
echo "📈 DEDUPLICATION RATE:"
docker compose exec -T postgresql psql -U enod_user -d enod_monitoring -c "
SELECT
  ROUND(
    (COUNT(CASE WHEN is_duplicate = TRUE THEN 1 END)::numeric /
     NULLIF(COUNT(*)::numeric, 0)) * 100,
    2
  ) as dedup_percentage
FROM alerts;
" 2>/dev/null | tail -3

echo ""
echo "🔥 ANALYSIS BREAKDOWN:"
docker compose exec -T postgresql psql -U enod_user -d enod_monitoring -c "
SELECT
  metadata->>'analysis_reason' as reason,
  COUNT(*) as count
FROM ai_analysis_results
WHERE analysis_type = 'llm_analysis'
GROUP BY metadata->>'analysis_reason'
ORDER BY count DESC;
" 2>/dev/null

echo ""
echo "🌐 SERVICES:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | grep -E "grafana|collector|ai-service|ollama"

echo ""
echo "📍 QUICK LINKS:"
echo "  - Dashboard: http://localhost:3000 (admin/enod_password)"
echo "  - Collector: http://localhost:8080/health"
echo ""
