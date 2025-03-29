from fastapi import APIRouter

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydub import AudioSegment
from pathlib import Path
from pydantic import BaseModel
from typing import Annotated

from modules.gen_audio import DEFAULT_VOICES
from helpers.aws_uploader import upload_to_s3

from config.logger import get_logger, log_time_taken

from services.video_service import generate_video
from modules.reddit_extracted import extract_reddit_url_data

logger = get_logger(__name__)

router = APIRouter()

VALID_DURATIONS = {45, 60, 75}
VALID_STYLES = {
    "anime",
    "realistic",
    "fantasy",
    "watercolor",
    "cyberpunk",
    "ink",
    "cartoon",
}
MAX_VOICE_FILE_DURATION = 120  # seconds
VALID_ASPECT_RATIOS = {"9:16", "16:9", "1:1"}


@router.post("/gen-reddit-video")
async def handle_video_request(
    userID: str,
    url: str,
    duration: int,
    aspect_ratio: str,
    style: str,
    voice_character: str = "",
    bgm_audio: str = "",
):

    # Parameter validation
    if duration not in VALID_DURATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid duration. Allowed values are {VALID_DURATIONS}.",
        )

    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise HTTPException(
            status_code=400, detail=f"Invalid aspect ratio: {aspect_ratio}"
        )

    if style not in VALID_STYLES:
        raise HTTPException(
            status_code=400, detail=f"Invalid style. Allowed styles are {VALID_STYLES}."
        )

    if voice_character not in DEFAULT_VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid voice. Allowed voices are {DEFAULT_VOICES.keys()}.",
        )

    # Extract Reddit text, feed it as prompt
    prompt = extract_reddit_url_data(url)
    content = prompt["content"]

    try:
        # Generate video
        await generate_video(
            prompt=content,
            duration=int(duration),
            style=style,
            aspect_ratio=aspect_ratio,
            bgm_audio=bgm_audio,
            voice_character=voice_character,
        )


        # Determine the correct video path based on bgm_audio
        video_path = Path("video_creation/assets/videos")

        if bgm_audio != "":
            video_file = video_path / "final_output_video_bgm.mp4"
            print("VIDEO FILE:",video_file)
        else:
            video_file = (
                video_path / "final_output_video.mp4"
            )  

        # Verify the video file exists before uploading
        if not video_file.exists():
            raise HTTPException(
                status_code=500, detail="Generated video file not found"
            )

        # Upload to aws-S3 with duration
        s3_url = upload_to_s3(str(video_file), int(duration))

        return JSONResponse(
            {"success": True, 
             "video_path": s3_url, 
             "duration": duration}
        )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")

        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )
