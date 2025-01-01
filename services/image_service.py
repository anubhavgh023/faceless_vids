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
