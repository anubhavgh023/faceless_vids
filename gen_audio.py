from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = OpenAI()

client.api_key = os.getenv("OPENAI_API_KEY")

def generate_audio(character: str):
    # Text prompts for the voiceover
    prompts = []
    with open("prompts/prompts.txt", "r") as f:
        prompts = f.read().splitlines()

    # Save directory for audio files
    audio_dir = "create_video/assets/audio/"

    # Loop through each prompt and generate voiceover audio
    for i, prompt in enumerate(prompts, start=1):
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice=character, 
            input=prompt
        )

        audio_file = f"{audio_dir}prompt_{i}.mp3"
        audio_response.stream_to_file(audio_file)

        print(f"Audio for prompt {i} saved as 'prompt_{i}.mp3'")

if __name__ == "__main__":
    generate_audio(character="onyx")
