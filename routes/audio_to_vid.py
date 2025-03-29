# Fastapi imports
from fastapi import APIRouter
from fastapi import UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from pathlib import Path

# Helpers
from config.logger import get_logger 
from services.aud2vid.aud_to_vid_service import generate_aud2vid 
from helpers.audio_duration import get_audio_duration
from modules.speech2text import speech2text
from helpers.aws_uploader import upload_to_s3

from typing import Optional, List
from fastapi import Form, File, UploadFile, HTTPException

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


@router.post("/audio-to-video")
async def handle_aud2vid_request(
    # duration: int = Form(...),
    userID: str = Form(...),
    aspect_ratio: str = Form(...),
    style: str = Form(...),
    #voice_character: Optional[str] = Form(""),
    bgm_audio: Optional[str] = Form(""),
    voice_files: Optional[List[UploadFile]] = File(...),  # Explicitly make it optional
):

    duration = 45
    style = "anime"
    print(userID)
    print(duration)
    print(aspect_ratio)
    print(bgm_audio)
    print(style)
    print(voice_files)

    # Parameter validation
    if int(duration) not in VALID_DURATIONS:
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

    uploaded_files = []
    try:
        # Handle voice files if provided
        if voice_files:
            # Create uploads directory
            uploads_dir = Path("uploads")
            uploads_dir.mkdir(exist_ok=True)

            # Save all uploaded files
            for i, voice_file in enumerate(voice_files, start=1):
                file_path = str(uploads_dir / f"sample_{i}.mp3")
                with open(file_path, "wb") as f:
                    f.write(await voice_file.read())
                uploaded_files.append(file_path)

                # Check audio duration
                audio_duration = get_audio_duration(file_path)
                if audio_duration > MAX_VOICE_FILE_DURATION:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Each voice file must be under {MAX_VOICE_FILE_DURATION} seconds.",
                    )

        # Extract text from audio
        path = "uploads/sample_1.mp3"
        audio_text = speech2text(path) 

        # Generate video
        await generate_aud2vid(
            audio_text=audio_text,
            duration=int(duration),
            style=style,
            aspect_ratio=aspect_ratio,
            bgm_audio=bgm_audio,
            # voice_character=voice_character,
            voice_files=uploaded_files if uploaded_files else None,
        )

        # Determine the correct video path based on bgm_audio
        video_path = Path("video_creation/assets/videos")
        if bgm_audio != "":
            video_file = video_path / "final_output_video_bgm.mp4"
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
    finally:
        # Clean up uploaded files
        for file_path in uploaded_files:
            try:
                Path(file_path).unlink()
            except Exception as e:
                logger.error(f"Error deleting uploaded file {file_path}: {str(e)}")
