from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")


def speech2text(path):
    audio_file = open(path, "rb")
    transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    return transcription.text

if __name__ == "__main__":
    path = "test_files/b2.mp3"
    script = speech2text(path=path)

    print(script)
