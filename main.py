import concurrent.futures
import asyncio

from modules.gen_story import subtitle_generator_story, image_generator_story
from modules.gen_audio import generate_audio
from modules.gen_image import read_prompts, generate_images_from_prompts
from video_creation.create_video import create_video

def generate_story_and_assets(prompt: str, duration: int, character: str,style:str):
    # 1. Generate story prompts for subtitles and images using threads
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(subtitle_generator_story, prompt, duration),
            executor.submit(image_generator_story, prompt, duration),
        ]
        concurrent.futures.wait(futures)

    # 2. Generate audio for the character
    generate_audio(character)

    # 3. Generate images based on the image prompts
    prompts_file = "prompts/img_gen_prompts.txt"
    prompts = asyncio.run(read_prompts(prompts_file))

    if prompts:
        asyncio.run(generate_images_from_prompts(prompts, style))
    else:
        print(f"No prompts found in {prompts_file}")


def main():
    prompt = "Horror Story, dark fantasy"
    duration = 45  # Duration in seconds for the story
    character = "nova"  # Character for the audio generation
    style = "ink"

    # Start generating the story and assets
    print("Starting to generate story and assets...")
    # generate_story_and_assets(prompt, duration, character,style)
    print("Story and assets generation completed!")

    # Create the video after generating assets
    print("Starting video creation...")
    create_video()  # Assuming create_video() handles the full video creation process
    print("Video creation completed!")

if __name__ == "__main__":
    main()
