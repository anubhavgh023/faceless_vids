# normal generation of sentences
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")


# Generate story in a single API call
def generate_story(prompt: str, duration: int):
    try:
        # Define number of sentences based on duration
        if duration == 45:
            num_of_sentences = 5
        elif duration == 90:
            num_of_sentences = 10
        else:
            print("Invalid duration")
            return

        # Request a full story with the required number of sentences
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a storyteller."},
                {
                    "role": "user",
                    "content": f"Write a visually engaging and vivid story with exactly {num_of_sentences} sentences based on this prompt: '{prompt}'. Each sentence should paint a clear, detailed picture, focusing on rich visual descriptions, scene-setting, and emotions. Ensure each sentence is approximately 50 words, filled with dynamic imagery and details that could inspire a series of illustrations or visual scenes.",
                },
            ],
        )

        # Extract the full story content
        story = completion.choices[0].message.content

        # Split the story into sentences
        sentences = story.split(". ")

        # Write each sentence on a new line in the file
        with open("prompts/prompts.txt", "w") as f:
            for sentence in sentences:
                if sentence.strip():  # Skip empty sentences
                    f.write(sentence.strip() + ".\n")

        print("Story successfully written to prompts.txt")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    prompt = "A knight in a dark forest."
    duration = 45
    generate_story(prompt=prompt, duration=duration)
