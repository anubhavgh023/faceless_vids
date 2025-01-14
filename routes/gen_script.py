from config.logger import get_logger
from modules.gen_script import generate_script
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = get_logger(__name__)
router = APIRouter()

VALID_DURATIONS = {45, 60, 75}

@router.post("/gen-script")
async def handle_script_generation(
    style: str,
    duration: int,
    topic,
):
    # Parameter validation
    if duration not in VALID_DURATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid duration. Allowed values are {VALID_DURATIONS}.",
        )

    try:
        script = await generate_script(style,int(duration),topic)
        return JSONResponse({"success": True, "script": script})  

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")

        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )
