#!/bin/bash
set -e

echo "Waiting for Grafana to be ready..."
until curl -s -f -o /dev/null http://grafana:3000/api/health; do
  echo "Grafana is not ready yet. Waiting..."
  sleep 5
done

echo "Grafana is ready. Provisioning dashboard..."

# Create the dashboard via Grafana API
# The dashboard.json already has the correct structure with "dashboard" and "overwrite" fields
HTTP_CODE=$(curl -s -o /tmp/response.json -w "%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d @/dashboard.json \
  -u admin:enod_password \
  http://grafana:3000/api/dashboards/db)

if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
  echo "Dashboard provisioned successfully! (HTTP $HTTP_CODE)"
  cat /tmp/response.json
else
  echo "Failed to provision dashboard. HTTP code: $HTTP_CODE"
  cat /tmp/response.json
  exit 1
fi
