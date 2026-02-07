from fastapi import APIRouter, HTTPException
from app.database import Database
import json

router = APIRouter()

@router.get("/latest")
async def get_latest_analysis():
    try:
        query = """
            SELECT 
                id, alert_id, analysis_type, model_name, analysis_data, confidence_score, created_at 
            FROM ai_analysis_results 
            ORDER BY created_at DESC 
            LIMIT 10
        """
        rows = await Database.fetch(query)
        
        results = []
        for row in rows:
            results.append({
                "id": str(row["id"]),
                "alert_id": str(row["alert_id"]),
                "analysis_type": row["analysis_type"],
                "model_name": row["model_name"],
                "analysis_data": json.loads(row["analysis_data"]) if isinstance(row["analysis_data"], str) else row["analysis_data"],
                "confidence_score": float(row["confidence_score"]),
                "created_at": row["created_at"]
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))