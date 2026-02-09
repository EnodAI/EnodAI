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
            "stream": False,
            "format": "json"
        }

        try:
            # Note: In a production async app, use aiohttp or httpx. 
            # Using requests here for simplicity as per requirements.
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=240)
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

        return f"""You are a Senior Site Reliability Engineer with 10+ years of experience in production systems.

ALERT DETAILS:
- Name: {labels.get('alertname', 'Unknown')}
- Severity: {labels.get('severity', 'Unknown')}
- Instance: {labels.get('instance', 'Unknown')}
- Description: {annotations.get('description', 'No description')}
- Summary: {annotations.get('summary', 'No summary')}
- Context: {json.dumps(labels)}

Analyze this alert and provide actionable recommendations with specific technical details.

Respond with a valid JSON object with these exact keys:
{{
  "root_cause": {{
    "technical_reason": "Specific technical cause with metrics",
    "affected_component": "Which component/service is affected",
    "impact": "Business/system impact"
  }},
  "immediate_actions": [
    {{
      "action": "Specific command or action",
      "rationale": "Why this action",
      "estimated_time": "How long it takes",
      "priority": "high/medium/low"
    }}
  ],
  "short_term_actions": [
    {{
      "action": "Optimization or fix",
      "rationale": "Expected improvement",
      "estimated_time": "2-24 hours",
      "priority": "high/medium/low"
    }}
  ],
  "long_term_actions": [
    {{
      "action": "Architectural improvement",
      "rationale": "Long-term benefit",
      "estimated_time": "1-7 days",
      "priority": "high/medium/low"
    }}
  ],
  "monitoring": {{
    "key_metrics": ["metric1", "metric2"],
    "alert_threshold": "When to escalate"
  }}
}}

Be specific: include numbers, commands, configuration changes, and timelines.
Focus on actionable steps, not generic advice."""