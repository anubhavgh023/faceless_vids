from openai import OpenAI
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

client = OpenAI()

client.api_key = os.getenv("OPENAI_API_KEY")

def read_prompts(file_path: str):
    """Reads prompts from a file and returns a list of prompts."""
    try:
        with open(file_path, "r") as f:
            return f.read().splitlines()
    except Exception as e:
        print(f"Error reading prompts from {file_path}: {e}")
        return []

def generate_images_from_prompts(prompts, style="anime"):
    """Generates images based on the provided prompts using the DALL-E model."""
    for i, prompt in enumerate(prompts, start=1):
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=f"{prompt}, in a modern portrait anime style with vibrant colors, bold outlines, dynamic action, exaggerated expressions, and detailed character designs, similar to the animation style of Demon Slayer: Kimetsu no Yaiba",
                quality="hd",
                size="1024x1792",  # Portrait size
                n=1,
            )
            image_url = response.data[0].url

            # Download the image
            download_image(image_url, f"create_video/assets/images/story_img_{i}.png", i)

        except Exception as e:
            print(f"Error generating image for prompt {i}: {e}")

def download_image(image_url, file_name, i):
    """Downloads the image from the provided URL and saves it to the file."""
    try:
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            with open(file_name, "wb") as f:
                f.write(image_response.content)
                print(f"Image {i} saved as '{file_name}'")
        else:
            print(f"Failed to download Image {i}: Status code {image_response.status_code}")
    except Exception as e:
        print(f"Error downloading Image {i}: {e}")

if __name__ == "__main__":
    # Step 1: Read prompts from file
    prompts_file = "prompts/prompts.txt"
    prompts = read_prompts(prompts_file)

    # Step 2: Generate images for each prompt
    if prompts:
        generate_images_from_prompts(prompts, style="anime")
    else:
        print(f"No prompts found in {prompts_file}")
