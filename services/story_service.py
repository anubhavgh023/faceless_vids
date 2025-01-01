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

async def generate_story_content(prompt: str, duration: int):
    """Generate subtitles and image prompts concurrently"""
    start_time = time.time()

    # Run story generation tasks concurrently
    subtitle_task = asyncio.create_task(subtitle_generator_story(prompt, duration))
    image_prompt_task = asyncio.create_task(image_generator_story(prompt, duration))
    await asyncio.gather(subtitle_task, image_prompt_task)

    log_time_taken("Story content generation", start_time, time.time())
