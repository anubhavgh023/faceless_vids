from openai import OpenAI
import requests
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()

client.api_key = os.getenv("OPENAI_API_KEY")

# duration is in seconds
def generate_story(prompt: str, duration: int):
    try:
        if duration == 30:
            num_of_sentences = 4
        elif duration == 60:
            num_of_sentences = 7
        else:
            print("Invalid duration")
            return

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a story teller."},
                {
                    "role": "user",
                    "content": f"Write exactly {num_of_sentences} sentences based on this prompt: '{prompt}' make a story out of it. Each sentence should be around 40 words long.",
                },
            ],
        )

        # Extract the content
        story = completion.choices[0].message.content

        # Split the story into sentences
        sentences = story.split(". ")

        # Write each sentence to the file
        with open("prompts/prompts.txt", "w") as f:
            for sentence in sentences:
                if sentence.strip():  # Ensure empty sentences are not written
                    f.write(sentence.strip() + ".\n")

        print("Story successfully written to prompts.txt")

    except Exception as e:
        print(f"Error : {e}")


if __name__ == "__main__":
    prompt = "I was walking down the amazon jungle."
    duration = 60
    generate_story(prompt=prompt, duration=duration)
