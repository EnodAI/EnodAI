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
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=30)
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
        
        return f"""
        Act as a Senior Site Reliability Engineer. Analyze the following system alert:
        
        Alert Name: {labels.get('alertname', 'Unknown')}
        Severity: {labels.get('severity', 'Unknown')}
        Description: {annotations.get('description', 'No description')}
        Summary: {annotations.get('summary', 'No summary')}
        Full Context: {json.dumps(labels)}

        Provide a JSON response with exactly these keys:
        1. "root_cause": Possible technical root cause
        2. "mitigation": Immediate steps to fix
        3. "analysis": Brief summary
        """