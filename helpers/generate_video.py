import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, List, Tuple

from modules.gen_story import subtitle_generator_story, image_generator_story
from modules.gen_audio import (
    generate_audio,
    create_voice_clone,
    delete_cloned_voice,
    DEFAULT_VOICES,
)
from modules.gen_image import read_prompts, generate_images_from_prompts
from video_creation.create_video import create_video, log_time_taken

logger = logging.getLogger()


async def generate_video(
    prompt: str,
    duration: int,
    style: str,
    bgm_audio: str,
    voice_character: str,
    voice_files: Optional[List[str]] = None,
) -> str:
    """Main function to handle video generation process"""
    total_start_time = time.time()
    cloned_voice_id = None

    try:
        # 1. Generate story content
        await generate_story_content(prompt, duration)

        # 2. Generate audio and images concurrently
        audio_task = process_voice(voice_character, voice_files)
        images_task = generate_images(style)

        # Wait for both tasks to complete
        (audio_success, audio_path, cloned_voice_id), _ = await asyncio.gather(
            audio_task, images_task
        )

        if not audio_success:
            raise Exception(f"Audio generation failed: {audio_path}")

        # 3. Create final video
        start_time = time.time()
        video_path = await create_video(
            output_video_duration=duration, bgm_audio=bgm_audio
        )
        log_time_taken("Video creation", start_time, time.time())

        # Log total time taken
        log_time_taken("Total video generation", total_start_time, time.time())

        return video_path

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
