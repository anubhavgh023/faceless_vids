import concurrent.futures
import asyncio
import time
import traceback
import sys
import logging

from modules.gen_story import subtitle_generator_story, image_generator_story
from modules.gen_audio import generate_audio
from modules.gen_image import read_prompts, generate_images_from_prompts
from video_creation.create_video import log_time_taken
from video_creation.create_video import create_video

logging.info("Main script started")

def generate_story_and_assets(prompt: str, duration: int, character: str, style: str):
    start_time = time.time()
    
    # 1. Generate story prompts for subtitles and images using threads
    logging.info("Generating story prompts for subtitles and images...")
    step_start = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(subtitle_generator_story, prompt, duration),
            executor.submit(image_generator_story, prompt, duration),
        ]
        concurrent.futures.wait(futures)
    step_end = time.time()
    logging.info(f"Story prompts generated in {step_end - step_start:.2f} seconds.")

    # 2. Generate audio for the character
    step_start = time.time()
    logging.info("Generating audio for character...")
    generate_audio(character)
    step_end = time.time()
    log_time_taken("Audio generated", step_start, step_end)

    # 3. Generate images based on the image prompts
    step_start = time.time()
    logging.info("Reading image prompts...")
    prompts_file = "prompts/img_gen_prompts.txt"
    prompts = asyncio.run(read_prompts(prompts_file))
    step_end = time.time()
    log_time_taken("Image prompts read", step_start, step_end)


    if prompts:
        logging.info("Generating images from prompts...")
        step_start = time.time()
        asyncio.run(generate_images_from_prompts(prompts, style))
        step_end = time.time()
        log_time_taken("Images generated", step_start, step_end)

    else:
        logging.warning(f"No prompts found in {prompts_file}")

    end_time = time.time()
    log_time_taken("Total story and assets generation time", start_time, end_time)


def main():
    prompt = "A boy proposing a girl in front of eiffel tower"
    duration = 45  # Duration in seconds for the story
    character = "echo"  # Character for the audio generation
    style = "realistic"

    total_start_time = time.time()

    try:
        # Start generating the story and assets
        logging.info("Starting to generate story and assets...")
        generate_story_and_assets(prompt, duration, character, style)
        logging.info("Story and assets generation completed!")

        # Create the video after generating assets
        logging.info("Starting video creation...")
        step_start = time.time()
        create_video(output_video_duration=duration)  # Assuming create_video() handles the full video creation process
        step_end = time.time()
        log_time_taken("Video creation", step_start, step_end)

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error("Traceback:", exc_info=True)
        sys.exit(1)

    total_end_time = time.time()
    log_time_taken("Total execution time", total_start_time, total_end_time)


if __name__ == "__main__":
    main()
