-- EnodAI Database Schema
-- Production-ready schema with UUID support and comprehensive tracking

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Metrics table for raw data points (Used for ML Training)
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_anomaly BOOLEAN DEFAULT FALSE
);

-- Performance indexes for metrics
CREATE INDEX IF NOT EXISTS idx_metrics_name_ts ON metrics(metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_labels ON metrics USING GIN (labels);
CREATE INDEX IF NOT EXISTS idx_metrics_anomaly ON metrics(is_anomaly) WHERE is_anomaly = TRUE;

-- Alerts table with UUID for distributed scalability
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255),
    source VARCHAR(100) NOT NULL DEFAULT 'prometheus',
    alert_name VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    title VARCHAR(500),
    description TEXT,
    labels JSONB DEFAULT '{}',
    annotations JSONB DEFAULT '{}',
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ends_at TIMESTAMP WITH TIME ZONE,
    generator_url TEXT,
    status VARCHAR(50) DEFAULT 'firing',
    raw_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for alerts
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_external_id ON alerts(external_id);

-- AI Analysis Results with comprehensive fields
CREATE TABLE IF NOT EXISTS ai_analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id UUID REFERENCES alerts(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    analysis_data JSONB NOT NULL DEFAULT '{}',
    analysis_text TEXT,
    root_cause TEXT,
    mitigation_steps TEXT,
    confidence_score DECIMAL(5,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for AI analysis
CREATE INDEX IF NOT EXISTS idx_analysis_alert_id ON ai_analysis_results(alert_id);
CREATE INDEX IF NOT EXISTS idx_analysis_type ON ai_analysis_results(analysis_type);

-- Model Versions Tracking
CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    model_type VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    algorithm VARCHAR(50),
    file_path VARCHAR(255) NOT NULL,
    parameters JSONB,
    metrics JSONB,
    is_active BOOLEAN DEFAULT FALSE,
    trained_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(model_type, version)
);

-- Index for active models
CREATE INDEX IF NOT EXISTS idx_model_active ON model_versions(model_type, is_active) WHERE is_active = TRUE;

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for alerts table
CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE metrics IS 'Raw metric data points for ML training and anomaly detection';
COMMENT ON TABLE alerts IS 'Alert records from monitoring systems';
COMMENT ON TABLE ai_analysis_results IS 'AI-generated analysis results with root cause and mitigation steps';
COMMENT ON TABLE model_versions IS 'ML model version tracking with parameters and performance metrics';
-- Migration: Add metadata for analysis tracking
-- This allows us to track WHY an alert was analyzed (first_occurrence, escalation, recovery)

ALTER TABLE ai_analysis_results
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Index for querying by analysis reason
CREATE INDEX IF NOT EXISTS idx_ai_analysis_metadata
ON ai_analysis_results USING gin(metadata);

-- Example queries:
-- Find all recovery analyses: SELECT * FROM ai_analysis_results WHERE metadata->>'analysis_reason' = 'recovery';
-- Find all escalation analyses: SELECT * FROM ai_analysis_results WHERE metadata->>'analysis_reason' = 'escalation';
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

-- Add reference_analysis_id to ai_analysis_results (for deduplication)
ALTER TABLE ai_analysis_results 
ADD COLUMN IF NOT EXISTS reference_analysis_id UUID REFERENCES ai_analysis_results(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_ai_analysis_reference 
ON ai_analysis_results(reference_analysis_id);

COMMENT ON COLUMN ai_analysis_results.reference_analysis_id IS 'References another analysis (for duplicate alerts)';
