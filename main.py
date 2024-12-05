import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, List, Tuple
import os

from modules.gen_story import subtitle_generator_story, image_generator_story
from modules.gen_audio import (
    generate_audio,
    create_voice_clone,
    delete_cloned_voice,
    DEFAULT_VOICES,
)
from modules.gen_image import read_prompts, generate_images_from_prompts
from video_creation.create_video import create_video, log_time_taken
from helpers.aws_uploader import upload_to_s3
from helpers.clean_video_folder import clean_video_folder

# Set up logging configuration
logging.basicConfig(
    filename="logs/application.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger()


# Function to log timing information
def log_time_taken(function_name, start_time, end_time):
    time_taken = end_time - start_time
    log_message = f"{function_name}: {time_taken:.2f} seconds"
    logger.info(log_message)


# 1.
async def generate_images(style: str, aspect_ratio):
    """Generate images from prompts"""
    start_time = time.time()

    try:
        prompts = await read_prompts("prompts/img_gen_prompts.txt")
        if not prompts:
            raise ValueError("No image prompts found in file")

        await generate_images_from_prompts(prompts, style, aspect_ratio)
        log_time_taken("Image generation", start_time, time.time())

    except Exception as e:
        logger.error(f"Error in image generation: {str(e)}")
        raise


# 2.
async def generate_story_content(prompt: str, duration: int):
    """Generate subtitles and image prompts concurrently"""
    start_time = time.time()

    # Run story generation tasks concurrently
    subtitle_task = asyncio.create_task(subtitle_generator_story(prompt, duration))
    image_prompt_task = asyncio.create_task(image_generator_story(prompt, duration))
    await asyncio.gather(subtitle_task, image_prompt_task)

    log_time_taken("Story content generation", start_time, time.time())


# 3.
async def generate_video(
    prompt: str,
    duration: int,
    aspect_ratio: str,
    style: str,
    bgm_audio: str,
    voice_character: str = "alice",
    voice_files: Optional[List[str]] = None,
):
    """Main function to handle video generation process"""
    total_start_time = time.time()
    cloned_voice_id = None

    try:
        # 1. Generate story content
        await generate_story_content(prompt, duration)

        # 2. Generate audio and images concurrently
        audio_task = process_voice(voice_character, voice_files)
        images_task = generate_images(style, aspect_ratio)

        # Wait for both tasks to complete
        (audio_success, audio_path, cloned_voice_id), _ = await asyncio.gather(
            audio_task, images_task
        )

        if not audio_success:
            raise Exception(f"Audio generation failed: {audio_path}")

        # 3. Create final video
        start_time = time.time()
        await create_video(
            output_video_duration=duration,
            bgm_audio=bgm_audio,
            aspect_ratio=aspect_ratio,
        )
        log_time_taken("Video creation", start_time, time.time())

        # Log total time taken
        log_time_taken("Total video generation", total_start_time, time.time())

    except Exception as e:
        logger.error(f"Error in video generation: {str(e)}", exc_info=True)
        raise
    finally:
        # Always clean up cloned voice if it exists
        if cloned_voice_id:
            logger.info(f"Cleaning up cloned voice: {cloned_voice_id}")
            if delete_cloned_voice(cloned_voice_id):
                logger.info("Successfully deleted cloned voice")
            else:
                logger.error("Failed to delete cloned voice")


# 4.
async def process_voice(
    voice_character: str, voice_samples: Optional[List[str]] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Generate audio using either default voice or cloned voice
    Returns: (success, result_path, cloned_voice_id)
    """
    start_time = time.time()
    cloned_voice_id = None

    try:
        if voice_samples:
            cloned_voice_id = create_voice_clone(
                voice_samples=voice_samples, voice_name="temp_voice_clone"
            )

            if not cloned_voice_id:
                raise Exception("Voice cloning failed")

            logger.info(f"Voice clone created with ID: {cloned_voice_id}")

            # Use cloned voice for generation
            success, result = generate_audio(
                character="clone",
                voice_samples=voice_samples,
                output_path="video_creation/assets/audio/combined_story_audio.wav",
            )
        else:
            # Validate default voice
            if voice_character.lower() not in DEFAULT_VOICES:
                raise Exception(f"Invalid voice character: {voice_character}")

            # Use default voice
            success, result = generate_audio(
                character=voice_character,
                output_path="video_creation/assets/audio/combined_story_audio.wav",
            )

        log_time_taken("Audio generation", start_time, time.time())

        if not success:
            raise Exception(f"Audio generation failed: {result}")

        return success, result, cloned_voice_id

    except Exception as e:
        logger.error(f"Error in audio generation: {str(e)}")
        # Clean up cloned voice if there was an error
        if cloned_voice_id:
            delete_cloned_voice(cloned_voice_id)
        raise


# FastAPI integration
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydub import AudioSegment
from pathlib import Path
from pydantic import BaseModel
from typing import Annotated

from modules.gen_audio import DEFAULT_VOICES

app = FastAPI()

VALID_DURATIONS = {45, 60, 75}
VALID_STYLES = {"anime", "realistic", "fantasy","watercolor", "cyberpunk", "ink","cartoon"}
MAX_VOICE_FILE_DURATION = 120  # seconds
VALID_ASPECT_RATIOS = {"9:16", "16:9", "1:1"}

origins = [
    "http://localhost:*",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    return {"message": "health check endpoint"}


def get_audio_duration(file_path: str) -> float:
    """Returns the duration of an audio file in seconds."""
    try:
        audio = AudioSegment.from_file(file_path)
        return audio.duration_seconds
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid audio file format or corrupted file."
        )


class FormData(BaseModel):
    prompt: str  # fun fact , history video
    duration: str  # frontend : take int
    aspect_ratio: str
    style: str
    voice_character: str = ""
    bgm_audio: str = ""  # add bgm option (optional)
    voice_files: List[UploadFile] = File(None)


@app.post("/generate-video")
# async def handle_video_request(data: Annotated[FormData, Form()]):
async def handle_video_request(
    prompt: str = Form(...),
    duration: int = Form(...),
    aspect_ratio: str = Form(...),
    style: str = Form(...),
    voice_character: Optional[str] = Form(""),
    bgm_audio: Optional[str] = Form(""),
    voice_files: Optional[List[UploadFile]] = File(None),
):
    # prompt = data.prompt
    # duration = int(data.duration)
    # aspect_ratio = str(data.aspect_ratio)
    # bgm_audio = data.bgm_audio
    # style = data.style
    # voice_character = data.voice_character
    # voice_files = data.voice_files

    print(prompt)
    print(duration)
    print(aspect_ratio)
    print(bgm_audio)
    print(style)
    print(voice_character)
    print(voice_files)

    # Parameter validation
    if int(duration) not in VALID_DURATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid duration. Allowed values are {VALID_DURATIONS}.",
        )

    # set img aspect ratio
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise HTTPException(
            status_code=400, detail=f"Invalid aspect ratio: {aspect_ratio}"
        )
    # aspect_ratio = data.aspect_ratio

    if style not in VALID_STYLES:
        raise HTTPException(
            status_code=400, detail=f"Invalid style. Allowed styles are {VALID_STYLES}."
        )

    if voice_character not in DEFAULT_VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid voice. Allowed voices are {DEFAULT_VOICES.keys()}.",
        )
    # # TODO: check bgm voices

    uploaded_files = []
    try:
        # Handle voice files if provided
        if voice_files:
            # Create uploads directory
            uploads_dir = Path("uploads")
            uploads_dir.mkdir(exist_ok=True)

            # Save all uploaded files
            uploaded_files = []
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

        # Generate video
        await generate_video(
            prompt=prompt,
            duration=int(duration),
            style=style,
            aspect_ratio=aspect_ratio,  # video aspect ratio
            bgm_audio=bgm_audio,
            voice_character=voice_character,
            voice_files=uploaded_files if uploaded_files else None,
        )

        # # upload video to s3
        # if bgm_audio != "":
        #     video_path = "video_creation/assets/videos/final_output_video_bgm.mp4"
        # else:
        #     video_path = "video_creation/assets/videos/final_output_video_subtitles.mp4"
        # s3_url = upload_to_s3(file_path=video_path, duration=duration)
        # logger.info(f"S3 URL: {s3_url}")

        # # delete all videos after s3 upload
        # clean_video_folder()

        return JSONResponse({"success": True, "video_path": "s3_url"})  # aws s3 link

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