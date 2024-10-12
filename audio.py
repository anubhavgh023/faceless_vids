from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = OpenAI()

client.api_key = os.getenv("OPENAI_API_KEY")



# Text prompts for the voiceover
prompts = [
    "A knight in shiny silver armor rides a black horse, entering a misty, dense forest with glowing lanterns.",
    "The knight encounters a mysterious figure with a glowing staff in the dark forest, trees looming around.",
    "The knight battles a fearsome red dragon on the edge of a rocky cliff, flames and sparks filling the air.",
    "The knight rests by a fire, his armor reflecting the flames, the battle-worn sword lying nearby.",
    "The knight returns to a grand castle at dawn, the sun rising behind tall towers.",
]

# Save directory for audio files
audio_dir = "audio/"

# Loop through each prompt and generate voiceover audio
for i, prompt in enumerate(prompts, start=1):
    audio_response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",  
        input=prompt
    )

    audio_file = f"{audio_dir}prompt_{i}.mp3"
    audio_response.stream_to_file(audio_file)

    # # Save the audio file
    # with open(audio_file, "wb") as f:
    #     f.write(audio_data)

    print(f"Audio for prompt {i} saved as 'prompt_{i}.mp3'")
