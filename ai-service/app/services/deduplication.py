"""
Resource-Aware Alert Deduplication Service
==========================================

CPU-friendly deduplication that tracks alert lifecycle:
- First occurrence
- Severity escalation (WARNING → CRITICAL)
- Severity recovery (CRITICAL → WARNING)

This minimizes LLM calls while capturing important state changes.
"""

from datetime import datetime, timedelta
from loguru import logger


class ResourceAwareDeduplicator:
    """
    CPU-friendly, insight-rich deduplication
    Tracks: First, Escalation, Recovery

    Example:
        180 alerts → 3 LLM calls (98.3% dedup rate)
        - First: WARNING
        - Escalation: CRITICAL
        - Recovery: WARNING
    """

    SEVERITY_LEVELS = {
        'critical': 3,
        'warning': 2,
        'info': 1
    }

    async def should_analyze(self, pool, alert_data: dict) -> tuple[bool, str]:
        """
        Determine if alert should be analyzed by LLM

        Returns:
            (should_analyze: bool, reason: str)

        Reasons:
            - first_occurrence: Never seen before
            - escalation: Severity increased
            - recovery: Severity decreased (situation improving)
            - duplicate_same_severity: Same severity as last analysis
        """
        alert_name = alert_data.get('labels', {}).get('alertname')
        instance = alert_data.get('labels', {}).get('instance')
        new_severity = alert_data.get('labels', {}).get('severity', 'warning')

        # Find last analysis for this alert
        last_analysis = await self._find_last_analysis(pool, alert_name, instance)

        if not last_analysis:
            logger.info(f"First occurrence: {alert_name} on {instance}")
            return (True, "first_occurrence")

        old_severity = last_analysis['severity']

        # ESCALATION (severity increasing - situation worsening)
        if self._is_escalation(old_severity, new_severity):
            logger.warning(f"Escalation detected: {alert_name} {old_severity} → {new_severity}")
            return (True, "escalation")

        # RECOVERY (severity decreasing - situation improving)
        if self._is_recovery(old_severity, new_severity):
            logger.info(f"Recovery detected: {alert_name} {old_severity} → {new_severity}")
            return (True, "recovery")

        # SAME SEVERITY → Duplicate (save CPU)
        logger.debug(f"Duplicate detected: {alert_name} (same {new_severity})")
        return (False, "duplicate_same_severity")

    async def _find_last_analysis(self, pool, alert_name: str, instance: str):
        """
        Find last ANALYZED (not duplicate) alert for this alert+instance
        """
        async with pool.acquire() as conn:
            return await conn.fetchrow("""
                SELECT
                    a.id as alert_id,
                    a.severity,
                    a.created_at,
                    r.id as analysis_id
                FROM alerts a
                INNER JOIN ai_analysis_results r
                    ON a.id = r.alert_id
                    AND r.analysis_type = 'llm_analysis'
                WHERE a.alert_name = $1
                  AND a.labels->>'instance' = $2
                  AND a.is_duplicate = FALSE
                ORDER BY a.created_at DESC
                LIMIT 1
            """, alert_name, instance)

    def _is_escalation(self, old_severity: str, new_severity: str) -> bool:
        """Check if severity is increasing (situation worsening)"""
        old_level = self.SEVERITY_LEVELS.get(old_severity, 1)
        new_level = self.SEVERITY_LEVELS.get(new_severity, 1)
        return new_level > old_level

    def _is_recovery(self, old_severity: str, new_severity: str) -> bool:
        """Check if severity is decreasing (situation improving)"""
        old_level = self.SEVERITY_LEVELS.get(old_severity, 1)
        new_level = self.SEVERITY_LEVELS.get(new_severity, 1)
        return new_level < old_level

    async def mark_as_duplicate(
        self,
        pool,
        alert_id: str,
        reference_alert_id: str,
        reference_analysis_id: str,
        reason: str = "duplicate_same_severity"
    ):
        """
        Mark alert as duplicate and create reference to original analysis
        """
        async with pool.acquire() as conn:
            # Mark alert as duplicate
            await conn.execute("""
                UPDATE alerts
                SET is_duplicate = TRUE,
                    reference_alert_id = $1
                WHERE id = $2
            """, reference_alert_id, alert_id)

            # Create reference record in ai_analysis_results
            await conn.execute("""
                INSERT INTO ai_analysis_results
                (alert_id, analysis_type, reference_analysis_id, model_name, analysis_data, confidence_score, metadata)
                VALUES ($1, 'duplicate_reference', $2, 'deduplication', $3, 1.0, $4)
            """,
            alert_id,
            reference_analysis_id,
            '{"duplicate": true, "message": "Same alert already analyzed"}',
            f'{{"analysis_reason": "{reason}"}}'
            )

        logger.debug(f"Alert {alert_id} marked as duplicate (reason: {reason})")
