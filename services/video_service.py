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

from config.logger import get_logger,log_time_taken


logger = get_logger(__name__)


from services.image_service import generate_images
from services.story_service import generate_story_content

async def generate_video(
    prompt: str,
    duration: int,
    aspect_ratio: str,
    style: str,
    bgm_audio: str,
    voice_character: str = "callum",
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