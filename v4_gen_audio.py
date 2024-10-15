# using threadpool

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

def generate_audio_for_prompt(character, prompt, index, audio_dir):
    """Generates audio for a single prompt."""
    try:
        # Call the API to generate the audio
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice=character,
            input=prompt
        )
        
        # Save the audio file
        audio_file = f"{audio_dir}prompt_{index}.mp3"
        with open(audio_file, "wb") as f:
            f.write(audio_response.content)  # Save audio binary data to file

        print(f"Audio for prompt {index} saved as 'prompt_{index}.mp3'")
    except Exception as e:
        print(f"Error generating audio for prompt {index}: {e}")

def generate_audio(character: str):
    """Generates audio for all prompts using a thread pool."""
    # Load text prompts for the voiceover
    with open("prompts/prompts.txt", "r") as f:
        prompts = f.read().splitlines()

    audio_dir = "create_video/assets/audio/"
    os.makedirs(audio_dir, exist_ok=True)

    # Use ThreadPoolExecutor to run tasks concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(generate_audio_for_prompt, character, prompt, i, audio_dir) 
                   for i, prompt in enumerate(prompts, start=1)]

        # Wait for all tasks to complete
        for future in as_completed(futures):
            future.result()

if __name__ == "__main__":
    character = "onyx"
    generate_audio(character)
