import asyncio
import json
import numpy as np
from typing import List, Dict, Any
from loguru import logger
from app.models.isolation_forest import IsolationForestWrapper
from app.config import get_settings
from app.database import get_db_pool

class AnomalyDetector:
    def __init__(self):
        self.settings = get_settings()
        self.model = IsolationForestWrapper(self.settings.model_path)
        self.model.load()

    async def detect(self, metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect anomaly for a single metric point.
        """
        try:
            raw_value = metric_data.get('metric_value')
            if raw_value is None:
                return {"is_anomaly": False, "error": "Missing metric_value"}

            value = float(raw_value)
            
            # Edge case: Handle NaN or Infinite values
            if not np.isfinite(value):
                logger.warning(f"Non-finite metric value detected: {value}")
                return {"is_anomaly": False, "error": "Non-finite value"}

            # Simple feature: [value]
            features = np.array([[value]])
            
            # Handle NaN in numpy array just in case
            features = np.nan_to_num(features)
            
            prediction = self.model.predict(features)[0]
            score = self.model.score_samples(features)[0]
            
            is_anomaly = prediction == -1
            
            return {
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": float(score),
                "model_version": "if_v1"
            }
        except ValueError as e:
            logger.error(f"Value error in detection: {e}")
            return {"is_anomaly": False, "error": "Invalid value"}
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return {"is_anomaly": False, "error": str(e)}

    async def train_model(self):
        """
        Fetch historical data from DB and retrain the model.
        """
        logger.info("Starting model retraining task...")
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Fetch last 10000 points
                # Use timeout to prevent long running queries
                rows = await conn.fetch("""
                    SELECT metric_value FROM metrics 
                    ORDER BY timestamp DESC LIMIT 10000
                """)
                
                if not rows:
                    logger.warning("No data found for training")
                    return

                # Convert to numpy array and handle potential NULLs
                data = np.array([[r['metric_value'] if r['metric_value'] is not None else 0.0] for r in rows])
                
                # Check for NaNs
                data = np.nan_to_num(data)
                
                # Run training in executor to avoid blocking event loop
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.model.train, data)
                
        except Exception as e:
            logger.error(f"Training failed: {e}")