# Used asyncio, made img gen concurrent

import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MODELSLAB_API_KEY = os.getenv("MODELSLAB_API_KEY")
MODELSLAB_API_URL = "https://modelslab.com/api/v6/realtime/text2img"
FETCH_API_URL = "https://modelslab.com/api/v6/realtime/fetch"
MAX_RETRIES = 2  # Max number of retries for failed requests


async def read_prompts(file_path: str):
    """Reads prompts from a file and returns a list of prompts."""
    try:
        with open(file_path, "r") as f:
            return f.read().splitlines()
    except Exception as e:
        print(f"Error reading prompts from {file_path}: {e}")
        return []


async def generate_image_request(session, prompt, style, i, attempt=1):
    """Sends a single image generation request for the given prompt with retry logic."""
    try:
        style_prompts = {
            "anime": ", modern anime portrait, vibrant colors, bold outlines, dynamic composition, exaggerated expressions and detailed character design.",
            "realistic": ", ultra-realistic portrait, high detail, professional photography, dramatic lighting, cinematic composition",
            "fantasy": ", fantasy portrait, ethereal atmosphere, magical elements, intricate details, dreamy lighting",
            "cyberpunk": ", cyberpunk portrait, neon lights, futuristic elements, high-tech urban background, gritty atmosphere",
            "oil_painting": ", oil painting portrait, textured brushstrokes, rich colors, classical composition, painterly style",
        }

        enhanced_prompt = f"((masterpiece, best quality, highly detailed, sharp focus)), (portrait:1.4), {prompt}{style_prompts.get(style, '')}"
        negative_prompt = "((blurry, low quality, low resolution, disfigured, deformed)), (extra limbs, extra fingers, extra arms, extra legs), bad anatomy, bad proportions, (unrealistic proportions), watermark, signature, cropped image"

        payload = {
            "key": MODELSLAB_API_KEY,
            "prompt": enhanced_prompt,
            "negative_prompt": negative_prompt,
            "width": "576",
            "height": "1024",  # Portrait size
            "samples": 1,
            "safety_checker": True,
            "enhance_prompt": True,
            "enhance_style": style,
        }

        async with session.post(MODELSLAB_API_URL, json=payload) as response:
            response_data = await response.json()

            if response_data["status"] == "success":
                image_id = response_data["id"]
                print(f"Image generation initiated for prompt {i}. ID: {image_id}")
                return (image_id, i)  # Return both the image_id and the index (i)
            else:
                print(
                    f"Error generating image for prompt {i}: {response_data.get('error')}"
                )
                if attempt < MAX_RETRIES:
                    print(f"Retrying prompt {i}, attempt {attempt + 1}")
                    return await generate_image_request(
                        session, prompt, style, i, attempt + 1
                    )  # Retry
                else:
                    print(
                        f"Failed to generate image for prompt {i} after {MAX_RETRIES} attempts"
                    )
                    return None
    except Exception as e:
        print(f"Error generating image for prompt {i}: {e}")
        if attempt < MAX_RETRIES:
            print(f"Retrying prompt {i}, attempt {attempt + 1}")
            return await generate_image_request(
                session, prompt, style, i, attempt + 1
            )  # Retry
        else:
            print(
                f"Failed to generate image for prompt {i} after {MAX_RETRIES} attempts"
            )
            return None


async def fetch_image(session, image_id, i, max_attempts=5, delay=10):
    """Fetches the generated image and downloads it with the correct filename."""
    for attempt in range(max_attempts):
        try:
            payload = {"key": MODELSLAB_API_KEY}
            async with session.post(
                f"{FETCH_API_URL}/{image_id}", json=payload
            ) as response:
                response_data = await response.json()

                if response_data["status"] == "success":
                    image_url = response_data["output"][0]
                    await download_image(
                        session,
                        image_url,
                        f"create_video/assets/images/story_img_{i}.png",
                        i,
                    )
                    return
                else:
                    print(
                        f"Image {i} not ready yet. Attempt {attempt + 1}/{max_attempts}"
                    )
                    await asyncio.sleep(delay)
        except Exception as e:
            print(f"Error fetching image {i}: {e}")

    print(f"Failed to fetch image {i} after {max_attempts} attempts")


async def download_image(session, image_url, file_name, i):
    """Downloads the image from the provided URL and saves it to the file."""
    try:
        async with session.get(image_url) as image_response:
            if image_response.status == 200:
                os.makedirs(os.path.dirname(file_name), exist_ok=True)
                with open(file_name, "wb") as f:
                    f.write(await image_response.read())
                print(f"Image {i} saved as '{file_name}'")
            else:
                print(
                    f"Failed to download Image {i}: Status code {image_response.status}"
                )
    except Exception as e:
        print(f"Error downloading Image {i}: {e}")


async def generate_images_from_prompts(prompts, style):
    """Generates images based on the provided prompts using the ModelsLab API."""
    max_parallel = 5  # generate 5 images in parallel

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, prompt in enumerate(prompts, start=1):
            tasks.append(generate_image_request(session, prompt, style, i))

        image_ids = [result for result in await asyncio.gather(*tasks) if result]

        # Now we fetch the images in parallel, but we ensure each image is saved with the correct filename
        fetch_tasks = [fetch_image(session, image_id, i) for image_id, i in image_ids]
        await asyncio.gather(*fetch_tasks)


if __name__ == "__main__":
    prompts_file = "prompts/prompts.txt"
    prompts = asyncio.run(read_prompts(prompts_file))

    if prompts:
        asyncio.run(generate_images_from_prompts(prompts, style="anime"))
    else:
        print(f"No prompts found in {prompts_file}")
