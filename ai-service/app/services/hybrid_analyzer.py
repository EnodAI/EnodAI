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

        return f"""You are a Senior Site Reliability Engineer with 10+ years of experience in production systems.

🚨 CRITICAL RULES - VIOLATION WILL CAUSE INCORRECT ANALYSIS:
1. READ ONLY THIS ALERT'S DESCRIPTION - Do NOT use information from other alerts or previous requests
2. EXTRACT ONLY technical details that appear in THIS description - Do NOT invent or assume details
3. USE ONLY the technology mentioned in THIS alert (MongoDB uses WiredTiger not JVM, Redis uses memory not JVM, etc.)
4. If a specific metric/detail is NOT in the description, DO NOT mention it in root cause
5. VERIFY every technical term you use appears in the description below

EXTRACTION RULES:
- Server names/IPs: Extract ALL mentioned (e.g., "mongo-primary-01.company.internal (10.3.2.10)")
- Technical problem: Use EXACT terms from description (e.g., if it says "WiredTiger cache 8.2GB/8GB", say that, NOT "JVM heap")
- Metrics: Use EXACT numbers from description (e.g., "63.8GB/64GB", "96% disk I/O")
- DO NOT use generic terms - use specific technology terms from THIS alert

ALERT DETAILS:
- Alert Name: {labels.get('alertname', 'Unknown')}
- Severity: {labels.get('severity', 'Unknown')}
- Instance: {labels.get('instance', 'Unknown')}
- Environment: {labels.get('environment', 'Unknown')}
- Service: {labels.get('service', 'Unknown')}
- Datacenter: {labels.get('datacenter', 'Unknown')}
- Team: {labels.get('team', 'Unknown')}

DETAILED DESCRIPTION (READ CAREFULLY):
{annotations.get('description', 'No description')}

SUMMARY:
{annotations.get('summary', 'No summary')}

ANALYSIS REQUIREMENTS:
- For "technical_reason": Extract the ACTUAL problem from description (e.g., "JVM heap exhausted 31.8GB/32GB", "max_connections=200 reached", "GC pauses 45+ seconds")
- For "affected_component": List SPECIFIC servers/IPs from description (e.g., "kafka-prod-01 through kafka-prod-05 (10.0.3.10-14)")
- For actions: Use SPECIFIC server names and commands (e.g., "Restart kafka-prod-01.company.internal", "Increase max_connections from 200 to 400 on db-prod-01")

Respond with a valid JSON object:
{{
  "root_cause": {{
    "technical_reason": "COPY EXACT technical problem from THIS alert's description with actual metrics. Use ONLY terms that appear in the description. Examples: 'WiredTiger cache 8.2GB/8GB thrashing' (MongoDB), 'memory 63.8GB/64GB eviction policy ACTIVE' (Redis), 'max_connections=200 reached' (PostgreSQL). DO NOT use 'JVM heap' unless the description specifically mentions JVM.",
    "affected_component": "LIST specific servers/IPs from THIS alert's description (e.g., 'mongo-primary-01 (10.3.2.10), mongo-secondary-01/02 (10.3.2.11/12)')",
    "impact": "QUOTE business impact from THIS alert's description with exact numbers (e.g., '$52,000/hour revenue loss, 15,200 users affected')"
  }},
  "immediate_actions": [
    {{
      "action": "SPECIFIC action with server names and commands (e.g., 'Restart JVM on kafka-prod-01 through kafka-prod-05 with -Xmx64g flag')",
      "rationale": "EXPLAIN based on root cause from description",
      "estimated_time": "5-30 min",
      "priority": "high"
    }}
  ],
  "short_term_actions": [
    {{
      "action": "Configuration change with specific values (e.g., 'Increase max_connections from 200 to 400 in postgresql.conf')",
      "rationale": "Why this helps based on description",
      "estimated_time": "2-24 hours",
      "priority": "medium/high"
    }}
  ],
  "long_term_actions": [
    {{
      "action": "Infrastructure improvement (e.g., 'Add 2 more Kafka brokers to distribute load')",
      "rationale": "Prevent recurrence",
      "estimated_time": "1-7 days",
      "priority": "medium"
    }}
  ],
  "monitoring": {{
    "key_metrics": ["EXTRACT from description: metrics to watch"],
    "alert_threshold": "Specific threshold from description"
  }}
}}

MANDATORY RULES:
1. Extract server names, IPs, metrics ONLY from THIS alert's description
2. DO NOT give generic advice
3. DO NOT use technical terms that don't appear in THIS alert's description
4. DO NOT mix information from other alerts or use cached knowledge
5. If description says "WiredTiger cache", use that term. If it says "memory exhausted", use that term. DO NOT substitute with different technology terms.

VALIDATION CHECK: Before responding, verify that every technical term in your root_cause appears in the description above."""