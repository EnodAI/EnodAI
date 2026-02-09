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
