from openai import OpenAI
import requests
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()

client.api_key = os.getenv("OPENAI_API_KEY")

style = "anime"

# List of story prompts with detailed descriptions
prompts = [
    "A knight in shiny silver armor rides a black horse, entering a misty, dense forest with glowing lanterns",
    "The knight encounters a mysterious figure with a glowing staff in the dark forest, trees looming around",
    "The knight battles a fearsome red dragon on the edge of a rocky cliff, flames and sparks filling the air,",
    "The knight rests by a fire, his armor reflecting the flames, the battle-worn sword lying nearby",
    "The knight returns to a grand castle at dawn, the sun rising behind tall towers"
]

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
