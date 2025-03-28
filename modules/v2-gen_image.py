# used asyncio
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger()

MODELSLAB_API_KEY = os.getenv("MODELSLAB_API_KEY")
MODELSLAB_API_URL = "https://modelslab.com/api/v6/realtime/text2img"
FETCH_API_URL = "https://modelslab.com/api/v6/realtime/fetch"
MAX_RETRIES = 3  # Max number of retries for failed requests
FETCH_MAX_ATTEMPTS = 7  # Max number of attempts for fetching images
FETCH_DELAY = 10  # Delay between fetch attempts in seconds

VALID_IMAGE_ASPECT_RATIOS = {
    "9:16": {"height": 1024, "width": 576},  # Portrait
    "16:9": {"height": 576, "width": 1024},  # Landscape
    "1:1": {"height": 1024, "width": 1024},  # Square
}


async def read_prompts(file_path: str):
    """Reads prompts from a file and returns a list of prompts."""
    try:
        with open(file_path, "r") as f:
            return f.read().splitlines()
    except Exception as e:
        logger.error(f"Error reading prompts from {file_path}: {e}")
        return []


async def generate_image_request(session, prompt, style, i, aspect_ratio):
    """Sends a single image generation request for the given prompt with retry logic."""

    style_prompts = {
        "anime": ", vibrant modern anime portrait, expressive characters, bold outlines, detailed features, vivid colors, and energetic composition. Enhance with 'anime'",
        "realistic": ", hyper-realistic portrait, sharp focus, cinematic composition, dramatic lighting, and high-level photographic details. Enhance with 'photograph' or 'hyperrealism'",
        "fantasy": ", ethereal fantasy portrait, magical atmosphere, intricate details, dreamlike scenery, and glowing elements. Enhance with 'fantasy-art' or 'dark-fantasy'",
        "cyberpunk": ", futuristic cyberpunk portrait, neon lights, gritty urban background, high-tech elements, and edgy styling. Enhance with 'futuristic-cyberpunk-cityscape'",
        "ink": ", intricate ink portrait, featuring bold, precise lines, and sharp contrast between light and shadow. The artwork has a strictly monochromatic aesthetic, with detailed cross-hatching and stippling to create depth and texture. The style emphasizes expressive features with a clean, minimalist approach. Enhance with 'japanese-ink-drawing'",
        "watercolor": ", delicate watercolor artwork, soft brush strokes, pastel colors, and a dreamy aesthetic. Enhance with 'watercolor'",
        "cartoon": ", whimsical cartoon style, playful characters, bold outlines, and exaggerated expressions. Enhance with 'adorable-kawaii' or 'cel-shaded-art'",
    }

    enhance_style_opts = {
        "anime": "anime",
        "realistic": "photograph",  # or "hyperrealism"
        "fantasy": "fantasy-art",  # or "dark-fantasy"
        "cyberpunk": "futuristic-cyberpunk-cityscape",
        "ink": "japanese-ink-drawing",
        "watercolor": "watercolor",
        "cartoon": "adorable-kawaii",  # or "cel-shaded-art"
    }

    enhanced_prompt = f"((masterpiece, best quality, highly detailed, sharp focus)),{prompt}{style_prompts.get(style,'')}"
    negative_prompt = "((blurry, low quality, low resolution, disfigured, deformed)), (extra limbs, extra fingers, extra arms, extra legs), bad anatomy, bad proportions, (unrealistic proportions), watermark, signature, cropped image"

    width = VALID_IMAGE_ASPECT_RATIOS[aspect_ratio]["width"]
    height = VALID_IMAGE_ASPECT_RATIOS[aspect_ratio]["height"]

    payload = {
        "key": MODELSLAB_API_KEY,
        "prompt": enhanced_prompt,
        "negative_prompt": negative_prompt,
        "width": f"{width}",
        "height": f"{height}",
        "samples": 1,
        "safety_checker": False,
        "enhance_prompt": True,
        "enhance_style": enhance_style_opts.get(style, ""),
    }

    for attempt in range(MAX_RETRIES):
        try:
            async with session.post(MODELSLAB_API_URL, json=payload) as response:
                response_data = await response.json()

                if response_data["status"] == "success":
                    image_id = response_data["id"]
                    logger.info(
                        f"Image generation initiated for prompt {i}. ID: {image_id}"
                    )
                    return (image_id, i)
                else:
                    logger.error(
                        f"Error generating image for prompt {i}: {response_data.get('error')}"
                    )
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Retrying prompt {i}, attempt {attempt + 2}")
                    await asyncio.sleep(1)  # Short delay before retry
        except Exception as e:
            logger.error(
                f"Exception occurred while generating image for prompt {i}: {e}"
            )
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Retrying prompt {i}, attempt {attempt + 2}")
            await asyncio.sleep(1)  # Short delay before retry

    logger.error(
        f"Failed to generate image for prompt {i} after {MAX_RETRIES} attempts"
    )
    return None


async def fetch_and_save_image(session, image_id, i):
    """Fetches the generated image and downloads it with the correct filename."""
    for attempt in range(FETCH_MAX_ATTEMPTS):
        try:
            payload = {"key": MODELSLAB_API_KEY}
            async with session.post(
                f"{FETCH_API_URL}/{image_id}", json=payload
            ) as response:
                response_data = await response.json()

                if response_data["status"] == "success":
                    image_url = response_data["output"][0]
                    file_name = f"video_creation/assets/images/story_img_{i}.png"
                    os.makedirs(os.path.dirname(file_name), exist_ok=True)

                    async with session.get(image_url) as image_response:
                        if image_response.status == 200:
                            with open(file_name, "wb") as f:
                                f.write(await image_response.read())
                            logger.info(f"Image {i} saved as '{file_name}'")
                            return
                        else:
                            logger.error(
                                f"Failed to download Image {i}: Status code {image_response.status}"
                            )
                else:
                    logger.warning(
                        f"Image {i} not ready yet. Attempt {attempt + 1}/{FETCH_MAX_ATTEMPTS}"
                    )
        except Exception as e:
            logger.error(f"Error fetching image {i}: {e}")

        if attempt < FETCH_MAX_ATTEMPTS - 1:
            await asyncio.sleep(FETCH_DELAY)

    logger.error(f"Failed to fetch image {i} after {FETCH_MAX_ATTEMPTS} attempts")


async def generate_images_from_prompts(prompts, style, aspect_ratio):
    """Generates images based on the provided prompts using the ModelsLab API."""
    async with aiohttp.ClientSession() as session:
        # Create tasks for all prompts at once
        generate_tasks = [
            generate_image_request(session, prompt, style, idx + 1, aspect_ratio)
            for idx, prompt in enumerate(prompts)
        ]

        # Wait for all generation tasks to complete
        image_ids = [
            result for result in await asyncio.gather(*generate_tasks) if result
        ]

        # Create tasks to fetch all generated images
        fetch_tasks = [
            fetch_and_save_image(session, image_id, idx) for image_id, idx in image_ids
        ]

        # Wait for all fetch tasks to complete
        await asyncio.gather(*fetch_tasks)

if __name__ == "__main__":
    async def main():
        file_path =  "prompts/img_gen_prompts.txt"
        prompts = await read_prompts(file_path)
        style = "anime" 
        aspect_ratio = "9:16"

        await generate_images_from_prompts(prompts, style, aspect_ratio)

    asyncio.run(main())
