import json
import requests
import logging

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    def __init__(self, ollama_url: str):
        self.ollama_url = ollama_url
        self.model_name = "llama2"

    async def analyze(self, alert_data: dict) -> dict:
        """
        Send alert data to Ollama for Root Cause Analysis
        """
        prompt = self._create_prompt(alert_data)
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            # Note: In a production async app, use aiohttp or httpx. 
            # Using requests here for simplicity as per requirements.
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=480)
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

    def _create_prompt(self, alert: dict) -> str:
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})

        return f"""You are a Senior SRE analyzing a production alert.

CRITICAL RULES:
1. Use ONLY information from THIS alert's description below
2. Match technology terms EXACTLY (MongoDB=WiredTiger, Redis=memory/eviction, PostgreSQL=connections, Nginx=workers)
3. Extract EXACT server names, IPs, and metrics from description
4. If detail not in description, don't mention it

ALERT: {labels.get('alertname', 'Unknown')} | {labels.get('severity', 'Unknown')}
Instance: {labels.get('instance', 'Unknown')} | Service: {labels.get('service', 'Unknown')}

DESCRIPTION:
{annotations.get('description', 'No description')}

SUMMARY: {annotations.get('summary', 'No summary')}

Respond with JSON:
{{
  "root_cause": {{
    "technical_reason": "Extract EXACT problem with metrics from description (e.g., 'memory 63.8GB/64GB eviction ACTIVE' for Redis, 'WiredTiger 8.2GB/8GB' for MongoDB)",
    "affected_component": "List specific servers/IPs from description",
    "impact": "Quote business impact with numbers from description"
  }},
  "immediate_actions": [
    {{
      "action": "Specific action with server name/command from description",
      "rationale": "Why based on root cause",
      "estimated_time": "5-30 min",
      "priority": "high"
    }}
  ],
  "short_term_actions": [
    {{
      "action": "Config change with specific values",
      "rationale": "Why this helps",
      "estimated_time": "2-24 hours",
      "priority": "medium"
    }}
  ],
  "long_term_actions": [
    {{
      "action": "Infrastructure improvement",
      "rationale": "Prevent recurrence",
      "estimated_time": "1-7 days",
      "priority": "medium"
    }}
  ],
  "monitoring": {{
    "key_metrics": ["Metrics to watch from description"],
    "alert_threshold": "Threshold from description"
  }}
}}

VERIFY: Every technical term in your response must appear in the description above."""