import requests
from dotenv import load_dotenv
import os
import json
import time

# Load environment variables
load_dotenv()

MODELSLAB_API_KEY = os.getenv("MODELSLAB_API_KEY")
MODELSLAB_API_URL = "https://modelslab.com/api/v6/realtime/text2img"
FETCH_API_URL = "https://modelslab.com/api/v6/realtime/fetch"

def read_prompts(file_path: str):
    """Reads prompts from a file and returns a list of prompts."""
    try:
        with open(file_path, "r") as f:
            return f.read().splitlines()
    except Exception as e:
        print(f"Error reading prompts from {file_path}: {e}")
        return []

def generate_images_from_prompts(prompts, style="anime"):
    """Generates images based on the provided prompts using the ModelsLab API."""
    style_prompts = {
        "anime": ", modern anime portrait, vibrant colors, bold outlines, dynamic composition, exaggerated expressions, detailed character design, style of Demon Slayer",
        "realistic": ", ultra-realistic portrait, high detail, professional photography, dramatic lighting, cinematic composition",
        "fantasy": ", fantasy portrait, ethereal atmosphere, magical elements, intricate details, dreamy lighting",
        "cyberpunk": ", cyberpunk portrait, neon lights, futuristic elements, high-tech urban background, gritty atmosphere",
        "oil_painting": ", oil painting portrait, textured brushstrokes, rich colors, classical composition, painterly style"
    }

    for i, prompt in enumerate(prompts, start=1):
        try:
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
                "enhance_style": style
            }

            response = requests.post(MODELSLAB_API_URL, json=payload)
            response_data = response.json()

            if response_data["status"] == "success":
                image_id = response_data["id"]
                print(f"Image generation initiated for prompt {i}. ID: {image_id}")
                fetch_and_download_image(image_id, i)
            else:
                print(f"Error generating image for prompt {i}: {response_data.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"Error generating image for prompt {i}: {e}")

def fetch_and_download_image(image_id, i, max_attempts=5, delay=10):
    """Fetches the generated image and downloads it."""
    for attempt in range(max_attempts):
        try:
            payload = {"key": MODELSLAB_API_KEY}
            response = requests.post(f"{FETCH_API_URL}/{image_id}", json=payload)
            response_data = response.json()

            if response_data["status"] == "success":
                image_url = response_data["output"][0]
                download_image(image_url, f"create_video/assets/images/story_img_{i}.png", i)
                return
            else:
                print(f"Image {i} not ready yet. Attempt {attempt + 1}/{max_attempts}")
                time.sleep(delay)
        except Exception as e:
            print(f"Error fetching image {i}: {e}")
    
    print(f"Failed to fetch image {i} after {max_attempts} attempts")

def download_image(image_url, file_name, i):
    """Downloads the image from the provided URL and saves it to the file."""
    try:
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            with open(file_name, "wb") as f:
                f.write(image_response.content)
            print(f"Image {i} saved as '{file_name}'")
        else:
            print(f"Failed to download Image {i}: Status code {image_response.status_code}")
    except Exception as e:
        print(f"Error downloading Image {i}: {e}")

if __name__ == "__main__":
    prompts_file = "prompts/prompts.txt"
    prompts = read_prompts(prompts_file)

    if prompts:
        generate_images_from_prompts(prompts, style="anime")
    else:
        print(f"No prompts found in {prompts_file}")