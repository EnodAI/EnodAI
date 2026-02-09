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

        return f"""You are a Senior SRE responding to a PRODUCTION EMERGENCY.

CRITICAL RULES:
1. Use ONLY info from THIS alert's description
2. Extract EXACT server names, IPs, metrics from description
3. Use correct tech terms: MongoDB=WiredTiger, Redis=memory/eviction, PostgreSQL=connections

ALERT: {labels.get('alertname', 'Unknown')} | Severity: {labels.get('severity', 'Unknown')}
Instance: {labels.get('instance', 'Unknown')}

DESCRIPTION:
{annotations.get('description', 'No description')}

Respond ONLY with JSON:
{{
  "root_cause": {{
    "problem": "EXACT technical issue with metrics from description",
    "servers": "Specific server names/IPs from description",
    "impact": "Business impact from description"
  }},
  "immediate_actions": [
    {{
      "step": 1,
      "action": "Specific command or action with server names",
      "command": "Exact command to run (if applicable)",
      "time": "5-15 min",
      "critical": true
    }},
    {{
      "step": 2,
      "action": "Next immediate action",
      "command": "Command if applicable",
      "time": "10-20 min",
      "critical": true
    }}
  ]
}}

Focus: Give me 2-3 IMMEDIATE actions to fix this NOW. No future plans."""