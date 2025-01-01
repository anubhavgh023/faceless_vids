from fastapi import APIRouter

router = APIRouter()


@router.get("/health-now")
async def handle_health_check():
    return {"status": "healthy"}
