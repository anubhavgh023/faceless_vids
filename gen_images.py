from openai import OpenAI
import requests
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()

client.api_key = os.getenv("OPENAI_API_KEY")

style = "anime"

# List of story prompts with detailed descriptions
prompts = []
with open("prompts/prompts.txt", "r") as f:
    prompts = f.read().splitlines()
    

for i, prompt in enumerate(prompts, start=1):
    response = client.images.generate(
        model="dall-e-3",
        prompt = f"{prompt}, in a modern anime style with vibrant colors, bold outlines, dynamic action, exaggerated expressions, and detailed character designs, similar to the animation style of Demon Slayer: Kimetsu no Yaiba",
        quality="hd",
        # size="1024x1024", # desktop
        size="1024x1792",
        n=1,
    )
    image_url = response.data[0].url
    print(image_url)

    image_response = requests.get(image_url)

    if image_response.status_code == 200:
        with open(f"images/t4_story_img_{i}.png", "wb") as f:
            f.write(image_response.content)
            print(f"Image {i} saved as 'story_image_{i}.png'")
    else:
        print(f"Failed to download Image {i}")
