import os
import asyncio
import aiohttp
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# logger = logging.getLogger()
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )

LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
LEONARDO_GENERATE_API_URL = "https://cloud.leonardo.ai/api/rest/v1/generations"
LEONARDO_FETCH_API_URL = "https://cloud.leonardo.ai/api/rest/v1/generations"

MAX_RETRIES = 2  # Max number of retries for failed requests
FETCH_MAX_ATTEMPTS = 5  # Max number of attempts for fetching images
FETCH_DELAY = 10  # Delay between fetch attempts in seconds

VALID_IMAGE_ASPECT_RATIOS = {
    "9:16": {"height": 1024, "width": 576},  # Portrait
    "16:9": {"height": 576, "width": 1024},  # Landscape
    "1:1": {"height": 1024, "width": 1024},  # Square
}

PRESET_STYLES = {
    "anime": "ANIME",
    "realistic": "PHOTOGRAPHIC",
    "fantasy": "FANTASY_ART",
    "cyberpunk": "CYBERPUNK",
    "ink": "SKETCH",
    "watercolor": "WATERCOLOR",
    "cartoon": "CARTOON",
}

MODEL_IDS = {
    "anime": "e71a1c2f-4f80-4800-934f-2c68979d8cc8",  # Anime XL
    "realistic": "6bef9f1b-29a2-4ca3-8417-dad1b960bf38",  # PhotoReal V1
    "fantasy": "eaa9a7c1-31d5-4de2-a3ec-e8a8842beb36",  # Fantasy World V1
    # Add more model IDs as needed
}

# async def read_prompts(file_path: str):
#     """
#     Reads prompts from a file and returns an enhanced list of prompts
#     with cumulative context for image generation.
#     """
#     try:
#         with open(file_path, "r") as f:
#             sentences = f.read().splitlines()

#         # Create cumulative prompts
#         cumulative_prompts = []
#         for i in range(len(sentences)):
#             # Combine current sentence with subsequent sentences
#             prompt = " ".join(sentences[i : i + 2])
#             cumulative_prompts.append(prompt)

#         return cumulative_prompts
#     except Exception as e:
#         logger.error(f"Error reading prompts from {file_path}: {e}")
#         return []


# line-by-line
async def read_prompts(file_path: str):
    """Reads prompts from a file and returns a list of prompts."""
    try:
        with open(file_path, "r") as f:
            return f.read().splitlines()
    except Exception as e:
        logger.error(f"Error reading prompts from {file_path}: {e}")
        return []


async def generate_image_request(
    session, prompt, style, i, aspect_ratio, prev_image_id=None
):
    """Sends a single image generation request with content progression guidance."""
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}",
        "content-type": "application/json",
    }

    payload = {
        "alchemy": True,
        "height": VALID_IMAGE_ASPECT_RATIOS[aspect_ratio]["height"],
        "width": VALID_IMAGE_ASPECT_RATIOS[aspect_ratio]["width"],
        "modelId": MODEL_IDS.get(style, MODEL_IDS["anime"]),
        "num_images": 1,
        "presetStyle": PRESET_STYLES.get(style, PRESET_STYLES["anime"]),
        "prompt": prompt,
        "highContrast": True,
        "highResolution": True,
        "num_inference_steps": 15,
        "promptMagic": True,
        "sd_version": "SDXL_LIGHTNING",
    }

    # Add image progression guidance if a previous image exists
    if prev_image_id:
        payload.update(
            {
                "controlnets": [
                    {
                        "initImageId": prev_image_id,
                        "initImageType": "GENERATED",
                        "preprocessorId": 100,  # Content Reference ID
                        "weight": 0.4,  # Moderate content influence
                    }
                ],
                "init_generation_image_id": prev_image_id,
                "init_strength": 0.3,  # Lower strength for more creative freedom
            }
        )

    for attempt in range(MAX_RETRIES):
        try:
            async with session.post(
                LEONARDO_GENERATE_API_URL, json=payload, headers=headers
            ) as response:
                response_data = await response.json()

                if (
                    "sdGenerationJob" in response_data
                    and "generationId" in response_data["sdGenerationJob"]
                ):
                    generation_id = response_data["sdGenerationJob"]["generationId"]
                    logger.info(
                        f"Image generation initiated for prompt {i}. ID: {generation_id}"
                    )
                    return (generation_id, i)
                else:
                    logger.error(
                        f"Error generating image for prompt {i}: {response_data}"
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


async def fetch_and_save_image(session, generation_id, i):
    """Fetches the generated image and downloads it with the correct filename."""
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}",
    }

    for attempt in range(FETCH_MAX_ATTEMPTS):
        try:
            async with session.get(
                f"{LEONARDO_FETCH_API_URL}/{generation_id}", headers=headers
            ) as response:
                response_data = await response.json()

                if response_data.get("generations_by_pk", {}).get(
                    "status"
                ) == "COMPLETE" and response_data.get("generations_by_pk", {}).get(
                    "generated_images"
                ):

                    image_url = response_data["generations_by_pk"]["generated_images"][
                        0
                    ]["url"]
                    image_id = response_data["generations_by_pk"]["generated_images"][
                        0
                    ]["id"]
                    file_name = f"video_creation/assets/images/story_img_{i}.png"
                    os.makedirs(os.path.dirname(file_name), exist_ok=True)

                    async with session.get(image_url) as image_response:
                        if image_response.status == 200:
                            with open(file_name, "wb") as f:
                                f.write(await image_response.read())
                            logger.info(f"Image {i} saved as '{file_name}'")
                            return image_id
                        else:
                            logger.error(
                                f"Failed to download Image {i}: Status code {image_response.status}"
                            )
                else:
                    logger.warning(
                        f"Image {i} not ready yet. Attempt {attempt + 1}/{FETCH_MAX_ATTEMPTS}"
                    )
                    await asyncio.sleep(FETCH_DELAY)

        except Exception as e:
            logger.error(f"Error fetching image {i}: {e}")

    logger.error(f"Failed to fetch image {i} after {FETCH_MAX_ATTEMPTS} attempts")
    return None


async def generate_images_from_prompts(prompts, style, aspect_ratio):
    """Generates images based on the provided prompts using the Leonardo AI API."""
    async with aiohttp.ClientSession() as session:
        # Store image IDs to use for guidance
        image_ids = []

        # Create tasks for all prompts with image-to-image guidance
        for idx, prompt in enumerate(prompts):
            # Use the previous image's ID for guidance if available
            prev_image_id = image_ids[-1] if image_ids else None

            # Generate image request task
            generation_task = generate_image_request(
                session, prompt, style, idx + 1, aspect_ratio, prev_image_id
            )

            # Wait for generation and get generation ID
            generation_result = await generation_task

            if generation_result:
                generation_id, image_index = generation_result

                # Wait a bit to ensure image is ready
                await asyncio.sleep(10)

                # Fetch and save image, getting its ID
                image_id = await fetch_and_save_image(
                    session, generation_id, image_index
                )

                if image_id:
                    image_ids.append(image_id)


if __name__ == "__main__":

    async def main():
        file_path = "prompts/subtitle_gen_prompts.txt"
        prompts = await read_prompts(file_path)
        style = "anime"
        aspect_ratio = "9:16"

        print(prompts)

        await generate_images_from_prompts(prompts, style, aspect_ratio)

    asyncio.run(main())
