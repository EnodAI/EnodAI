import json
import asyncio
import redis.asyncio as redis
from loguru import logger
from app.config import get_settings
from app.database import get_db_pool

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

    async def cleanup_old_pending(self, max_idle_ms=300000):
        """
        Clean up old pending messages (older than 5 minutes by default)
        These are messages that failed to process and are blocking the queue
        """
        if not self.redis:
            return 0

        try:
            # Get pending messages info
            pending_info = await self.redis.xpending(
                self.settings.redis_stream,
                self.settings.redis_group
            )

            if not pending_info or pending_info[0] == 0:
                return 0

            # Get detailed pending messages
            pending_messages = await self.redis.xpending_range(
                self.settings.redis_stream,
                self.settings.redis_group,
                min='-',
                max='+',
                count=100
            )

            cleaned = 0
            for msg in pending_messages:
                message_id = msg['message_id']
                idle_time = msg['time_since_delivered']

                # If message is stuck (idle > 5 minutes), acknowledge it
                if idle_time > max_idle_ms:
                    logger.warning(f"Cleaning up stuck message {message_id} (idle: {idle_time}ms)")
                    await self.redis.xack(self.settings.redis_stream, self.settings.redis_group, message_id)
                    cleaned += 1

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} stuck pending messages")
            return cleaned

        except Exception as e:
            logger.error(f"Error cleaning up pending messages: {e}")
            return 0

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

        logger.info("Starting Redis consumer...")
        self.running = True

        # Initialize components
        detector = AnomalyDetector()
        llm_analyzer = LLMAnalyzer(f"http://{self.settings.ollama_host}:{self.settings.ollama_port}")

        # Connect to Redis
        await self.client.connect()

        # Cleanup counter for periodic pending message cleanup
        cleanup_counter = 0
        cleanup_interval = 50  # Clean up every 50 iterations (~5 seconds)

        while self.running:
            try:
                # Periodic cleanup of stuck pending messages
                cleanup_counter += 1
                if cleanup_counter >= cleanup_interval:
                    await self.client.cleanup_old_pending()
                    cleanup_counter = 0

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
                            # Acknowledge message ALWAYS (even on error, to avoid blocking)
                            await self.client.ack(message_id)
                        except Exception as e:
                            logger.error(f"Error processing message {message_id}: {e}")
                            # ACK anyway to prevent blocking the queue
                            await self.client.ack(message_id)

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
        """Process alert with resource-aware deduplication and LLM analysis"""
        from app.services.deduplication import ResourceAwareDeduplicator

        alert_id = alert_data.get('alert_id')
        payload = alert_data.get('payload', {})

        # 1. Should we analyze this alert?
        deduplicator = ResourceAwareDeduplicator()
        should_analyze, reason = await deduplicator.should_analyze(pool, payload)

        if not should_analyze:
            # DUPLICATE - Skip LLM, mark as duplicate
            logger.info(f"Alert {alert_id} is duplicate ({reason}), skipping LLM analysis")

            # Find the original analysis to reference
            last_analysis = await deduplicator._find_last_analysis(
                pool,
                payload.get('labels', {}).get('alertname'),
                payload.get('labels', {}).get('instance')
            )

            if last_analysis:
                await deduplicator.mark_as_duplicate(
                    pool,
                    alert_id,
                    last_analysis['alert_id'],
                    last_analysis['analysis_id'],
                    reason
                )
            return

        # 2. UNIQUE/ESCALATION/RECOVERY - Perform LLM analysis
        logger.info(f"Alert {alert_id} requires analysis: {reason}")

        # Retry logic for LLM analysis with context
        max_retries = 2
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                logger.info(f"LLM analysis attempt {attempt + 1}/{max_retries} for alert {alert_id} (reason: {reason})")

                # Perform LLM analysis with context-aware prompt
                analysis = await llm_analyzer.analyze(payload, analysis_reason=reason)

                # Check if analysis has error
                if analysis.get('error'):
                    raise Exception(f"LLM returned error: {analysis['error']}")

                logger.info(f"LLM analysis completed for alert {alert_id} (reason: {reason})")

                # Store analysis result with metadata
                async with pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO ai_analysis_results
                        (alert_id, analysis_type, model_name, analysis_data, confidence_score, metadata)
                        VALUES ($1, 'llm_analysis', 'llama2', $2, $3, $4)
                    """,
                    alert_id,
                    json.dumps(analysis),
                    0.85,
                    json.dumps({"analysis_reason": reason})
                    )
                return  # Success, exit retry loop

            except Exception as e:
                logger.error(f"Alert processing error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    # Final failure - store error result
                    logger.error(f"Failed to analyze alert {alert_id} after {max_retries} attempts")
                    try:
                        async with pool.acquire() as conn:
                            await conn.execute("""
                                INSERT INTO ai_analysis_results
                                (alert_id, analysis_type, model_name, analysis_data, confidence_score, metadata)
                                VALUES ($1, 'llm_analysis', 'llama2', $2, $3, $4)
                            """,
                            alert_id,
                            json.dumps({"error": f"Analysis failed after {max_retries} attempts: {str(e)}"}),
                            0.0,
                            json.dumps({"analysis_reason": reason, "failure": True})
                            )
                    except Exception as store_error:
                        logger.error(f"Failed to store error result: {store_error}")

    async def stop(self):
        """Stop consuming messages"""
        logger.info("Stopping Redis consumer...")
        self.running = False