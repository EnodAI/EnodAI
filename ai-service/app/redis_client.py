import json
import asyncio
import redis.asyncio as redis
from loguru import logger
from app.config import get_settings

class RedisClient:
    def __init__(self):
        self.settings = get_settings()
        self.redis = None
        self.consumer_name = "ai-worker-1"

    async def connect(self):
        self.redis = redis.from_url(
            self.settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        try:
            await self.redis.ping()
            logger.info("Connected to Redis")
            # Create consumer group
            try:
                await self.redis.xgroup_create(
                    self.settings.redis_stream,
                    self.settings.redis_group,
                    id='0',
                    mkstream=True
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            # Don't raise here, allow retry in main loop or handle gracefully

    async def consume(self):
        if not self.redis:
            return []

        try:
            messages = await self.redis.xreadgroup(
                groupname=self.settings.redis_group,
                consumername=self.consumer_name,
                streams={self.settings.redis_stream: '>'},
                count=10,
                block=1000
            )
            return messages
        except redis.ConnectionError:
            logger.error("Redis connection lost during consume")
            return []
        except Exception as e:
            logger.error(f"Error consuming stream: {e}")
            return []

    async def ack(self, message_id):
        if self.redis:
            try:
                await self.redis.xack(self.settings.redis_stream, self.settings.redis_group, message_id)
            except Exception as e:
                logger.error(f"Failed to ACK message {message_id}: {e}")

    async def close(self):
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")


class RedisConsumer:
    """
    Redis Stream Consumer that processes metrics and alerts
    Integrates with anomaly detection and LLM analysis
    """
    def __init__(self):
        self.client = RedisClient()
        self.running = False
        self.settings = get_settings()

    async def start_consuming(self):
        """Start consuming messages from Redis Stream"""
        from app.detector import AnomalyDetector
        from app.services.hybrid_analyzer import LLMAnalyzer
        from app.database import get_db_pool

        logger.info("Starting Redis consumer...")
        self.running = True

        # Initialize components
        detector = AnomalyDetector()
        llm_analyzer = LLMAnalyzer(f"http://{self.settings.ollama_host}:{self.settings.ollama_port}")

        # Connect to Redis
        await self.client.connect()

        while self.running:
            try:
                messages = await self.client.consume()

                if not messages:
                    await asyncio.sleep(0.1)
                    continue

                # Process each message
                for stream_name, message_list in messages:
                    for message_id, message_data in message_list:
                        try:
                            await self._process_message(
                                message_id,
                                message_data,
                                detector,
                                llm_analyzer
                            )
                            # Acknowledge message
                            await self.client.ack(message_id)
                        except Exception as e:
                            logger.error(f"Error processing message {message_id}: {e}")
                            # Don't ACK failed messages, they'll be redelivered

            except asyncio.CancelledError:
                logger.info("Consumer task cancelled")
                break
            except Exception as e:
                logger.error(f"Consumer loop error: {e}")
                await asyncio.sleep(5)  # Wait before retry

        await self.client.close()
        logger.info("Redis consumer stopped")

    async def _process_message(self, message_id: str, data: dict, detector, llm_analyzer):
        """Process individual message from stream"""
        try:
            msg_type = data.get('type', '')
            msg_data = json.loads(data.get('data', '{}'))

            pool = await get_db_pool()

            if msg_type == 'metric':
                # Process metric for anomaly detection
                await self._process_metric(msg_data, detector, pool)

            elif msg_type == 'alert':
                # Process alert with LLM analysis
                await self._process_alert(msg_data, llm_analyzer, pool)

            else:
                logger.warning(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message data: {e}")
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            raise

    async def _process_metric(self, metric_data: dict, detector, pool):
        """Process metric and detect anomalies"""
        try:
            result = await detector.detect(metric_data)

            if result.get('is_anomaly'):
                logger.warning(f"Anomaly detected: {metric_data.get('metric_name')} = {metric_data.get('metric_value')}")

                # Store anomaly result
                async with pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO ai_analysis_results
                        (alert_id, analysis_type, model_name, analysis_data, confidence_score)
                        VALUES (NULL, 'anomaly_detection', $1, $2, $3)
                    """,
                    result.get('model_version'),
                    json.dumps({
                        'metric_name': metric_data.get('metric_name'),
                        'metric_value': metric_data.get('metric_value'),
                        'anomaly_score': result.get('anomaly_score')
                    }),
                    abs(result.get('anomaly_score', 0.0))
                    )

        except Exception as e:
            logger.error(f"Metric processing error: {e}")

    async def _process_alert(self, alert_data: dict, llm_analyzer, pool):
        """Process alert with LLM analysis"""
        try:
            alert_id = alert_data.get('alert_id')
            payload = alert_data.get('payload', {})

            # Perform LLM analysis
            analysis = await llm_analyzer.analyze(payload)

            logger.info(f"LLM analysis completed for alert {alert_id}")

            # Store analysis result
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO ai_analysis_results
                    (alert_id, analysis_type, model_name, analysis_data, confidence_score)
                    VALUES ($1, 'llm_analysis', 'llama2', $2, $3)
                """,
                alert_id,
                json.dumps(analysis),
                0.85  # Default confidence for LLM analysis
                )

        except Exception as e:
            logger.error(f"Alert processing error: {e}")

    async def stop(self):
        """Stop consuming messages"""
        logger.info("Stopping Redis consumer...")
        self.running = False