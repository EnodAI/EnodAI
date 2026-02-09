-- Migration: Add deduplication columns to alerts table
-- Enables smart deduplication: track duplicates and reference original analysis

ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS reference_alert_id UUID REFERENCES alerts(id) ON DELETE SET NULL;

-- Index for querying non-duplicate alerts (most common query)
CREATE INDEX IF NOT EXISTS idx_alerts_is_duplicate
ON alerts(is_duplicate) WHERE is_duplicate = FALSE;

-- Index for deduplication lookup (alert_name + instance + severity)
CREATE INDEX IF NOT EXISTS idx_alerts_dedup_lookup
ON alerts(alert_name, ((labels->>'instance')), severity, created_at DESC);

-- Comments
COMMENT ON COLUMN alerts.is_duplicate IS 'True if this alert is a duplicate of another analyzed alert';
COMMENT ON COLUMN alerts.reference_alert_id IS 'References the original alert that was analyzed (for duplicates)';
