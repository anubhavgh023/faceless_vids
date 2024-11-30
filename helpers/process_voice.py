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
                output_path="assets/audio/combined_story_audio.wav",
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
