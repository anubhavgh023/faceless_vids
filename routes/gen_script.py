from config.logger import get_logger
from modules.gen_story import generate_script
from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = get_logger(__name__)
router = APIRouter()

VALID_DURATIONS = {45, 60, 75}

@router.post("/gen-script")
async def handle_script_generation(
    prompt: str,
    duration: int,
):
    # Parameter validation
    if duration not in VALID_DURATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid duration. Allowed values are {VALID_DURATIONS}.",
        )

    try:
        script = await generate_script(prompt,duration)
        return JSONResponse({"success": True, "script": script})  

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")

        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )
