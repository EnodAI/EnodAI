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
        description = annotations.get('description', 'No description')

        # Detect technology from alert to provide specific guidance
        tech_hint = self._get_technology_hint(labels.get('alertname', ''), description)

        # Base prompt
        base = f"""You are a Senior SRE responding to a PRODUCTION EMERGENCY.

CRITICAL RULES:
1. Use ONLY info from THIS alert's description
2. Extract EXACT server names, IPs, metrics from description
3. {tech_hint}
4. NEVER suggest actions for technologies NOT mentioned in the description

ALERT: {labels.get('alertname', 'Unknown')} | Severity: {labels.get('severity', 'Unknown')}
Instance: {labels.get('instance', 'Unknown')}

DESCRIPTION:
{description}"""

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

    def _get_technology_hint(self, alert_name: str, description: str) -> str:
        """
        Detect technology from alert name/description and provide specific guidance.
        Returns technology-specific instructions to prevent mixing technologies.
        """
        alert_lower = alert_name.lower()
        desc_lower = description.lower()

        # Check for specific technologies
        if 'redis' in alert_lower or 'redis' in desc_lower:
            return "Technology: REDIS. Use Redis-specific terms: memory/eviction/keys/fragmentation. NO MongoDB/PostgreSQL commands!"

        elif 'mongo' in alert_lower or 'mongo' in desc_lower:
            return "Technology: MONGODB. Use MongoDB-specific terms: WiredTiger/collections/documents. NO Redis/PostgreSQL commands!"

        elif 'postgres' in alert_lower or 'postgres' in desc_lower or 'postgresql' in alert_lower or 'postgresql' in desc_lower:
            return "Technology: POSTGRESQL. Use PostgreSQL-specific terms: connections/queries/tables. NO Redis/MongoDB commands!"

        elif 'mysql' in alert_lower or 'mysql' in desc_lower or 'mariadb' in alert_lower or 'mariadb' in desc_lower:
            return "Technology: MYSQL. Use MySQL-specific terms: InnoDB/queries/tables/binlog. NO Redis/MongoDB/PostgreSQL commands!"

        elif 'nginx' in alert_lower or 'nginx' in desc_lower:
            return "Technology: NGINX. Use Nginx-specific terms: upstream/backend/proxy. NO database commands!"

        elif 'kafka' in alert_lower or 'kafka' in desc_lower:
            return "Technology: KAFKA. Use Kafka-specific terms: topics/partitions/consumer-lag/offsets. NO database commands!"

        elif 'elasticsearch' in alert_lower or 'elastic' in desc_lower:
            return "Technology: ELASTICSEARCH. Use ES-specific terms: shards/indices/heap/cluster. NO database commands!"

        elif 'rabbitmq' in alert_lower or 'rabbitmq' in desc_lower:
            return "Technology: RABBITMQ. Use RabbitMQ-specific terms: queues/exchanges/consumers. NO database commands!"

        elif 'cassandra' in alert_lower or 'cassandra' in desc_lower:
            return "Technology: CASSANDRA. Use Cassandra-specific terms: compaction/SSTables/keyspaces. NO Redis/MongoDB commands!"

        elif 'disk' in alert_lower or 'disk' in desc_lower or 'filesystem' in alert_lower or 'storage' in desc_lower:
            return "Focus on DISK/FILESYSTEM operations. Use disk-specific commands: df/du/fsck/resize2fs. Suggest cleanup based on files mentioned in description."

        elif 'cpu' in alert_lower or 'cpu' in desc_lower or 'load' in alert_lower:
            return "Focus on CPU/PROCESS operations. Use CPU-specific commands: top/htop/kill/nice. Analyze processes mentioned in description."

        elif 'memory' in alert_lower or 'ram' in desc_lower or 'oom' in alert_lower:
            return "Focus on MEMORY operations. Use memory-specific commands: free/vmstat/oom. Analyze memory consumers mentioned in description."

        else:
            return "Use ONLY technologies and commands mentioned in the alert description. DO NOT assume or add other technologies."