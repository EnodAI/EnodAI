import json
import requests
import asyncio
import logging

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """
    Throttled LLM Analyzer with CPU protection

    Features:
    - Max 2 concurrent LLM calls (prevents CPU overload)
    - Context-aware prompts (first_occurrence, escalation, recovery)
    - Queue depth tracking
    """

    def __init__(self, ollama_url: str, max_concurrent: int = 2):
        self.ollama_url = ollama_url
        self.model_name = "llama2"
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue_depth = 0

    async def analyze(self, alert_data: dict, analysis_reason: str = "first_occurrence") -> dict:
        """
        Send alert data to Ollama for Root Cause Analysis

        Args:
            alert_data: Alert payload
            analysis_reason: Why we're analyzing (first_occurrence, escalation, recovery)
        """
        self.queue_depth += 1
        logger.info(f"LLM queue depth: {self.queue_depth}, reason: {analysis_reason}")

        try:
            async with self.semaphore:  # Throttle: max 2 concurrent
                prompt = self._create_prompt(alert_data, analysis_reason)

                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }

                # Note: In a production async app, use aiohttp or httpx.
                # Using requests here for simplicity as per requirements.
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=480
                )
                response.raise_for_status()

                result = response.json()
                response_text = result.get("response", "{}")

                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return {"raw_analysis": response_text, "error": "Failed to parse JSON"}

        except Exception as e:
            logger.error(f"LLM Analysis failed: {e}")
            return {"error": str(e)}

        finally:
            self.queue_depth -= 1

    def _create_prompt(self, alert: dict, reason: str = "first_occurrence") -> str:
        """
        Create context-aware prompt based on analysis reason
        """
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})

        # Base prompt
        base = f"""You are a Senior SRE responding to a PRODUCTION EMERGENCY.

CRITICAL RULES:
1. Use ONLY info from THIS alert's description
2. Extract EXACT server names, IPs, metrics from description
3. Use correct tech terms: MongoDB=WiredTiger, Redis=memory/eviction, PostgreSQL=connections

ALERT: {labels.get('alertname', 'Unknown')} | Severity: {labels.get('severity', 'Unknown')}
Instance: {labels.get('instance', 'Unknown')}

DESCRIPTION:
{annotations.get('description', 'No description')}"""

        # Context based on reason
        if reason == "recovery":
            context = """

⭐ RECOVERY ANALYSIS:
This alert's severity has DECREASED (situation improving).

Focus on:
1. What action was likely taken that helped?
2. Is the system fully recovered or still recovering?
3. What should be monitored to ensure stability?

Respond with JSON:
{
  "root_cause": {
    "problem": "Original issue (now improving)",
    "servers": "Affected servers",
    "recovery_status": "Recovering / Fully recovered"
  },
  "immediate_actions": [
    {
      "step": 1,
      "action": "Monitor X for Y minutes to confirm recovery",
      "command": "command if applicable",
      "time": "time estimate",
      "critical": false
    }
  ]
}"""

        elif reason == "escalation":
            context = """

🔥 ESCALATION ALERT:
This alert's severity has INCREASED (situation worsening).

Focus on:
1. Why did the situation escalate?
2. What immediate action is needed NOW?
3. What's the business impact?

Respond ONLY with JSON:
{
  "root_cause": {
    "problem": "EXACT technical issue with metrics from description",
    "servers": "Specific server names/IPs from description",
    "impact": "Business impact from description"
  },
  "immediate_actions": [
    {
      "step": 1,
      "action": "Specific command or action with server names",
      "command": "Exact command to run (if applicable)",
      "time": "5-15 min",
      "critical": true
    }
  ]
}"""

        else:  # first_occurrence
            context = """

Respond ONLY with JSON:
{
  "root_cause": {
    "problem": "EXACT technical issue with metrics from description",
    "servers": "Specific server names/IPs from description",
    "impact": "Business impact from description"
  },
  "immediate_actions": [
    {
      "step": 1,
      "action": "Specific command or action with server names",
      "command": "Exact command to run (if applicable)",
      "time": "5-15 min",
      "critical": true
    }
  ]
}

Focus: Give me 2-3 IMMEDIATE actions to fix this NOW. No future plans."""

        return base + context