from fastapi import APIRouter
from app.database import Database

router = APIRouter()

@router.get("/health")
async def health_check():
    try:
        # Simple DB check
        await Database.execute("SELECT 1")
        return {"status": "ok", "service": "ai-service"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}