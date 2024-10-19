# normal generation of sentences, improved prompts
from openai import OpenAI
import os
from dotenv import load_dotenv
import concurrent.futures
import asyncio
import re

load_dotenv()

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")


# Generate story-prompts which are going be used as subtitles
def subtitle_generator_story(prompt: str, duration: int):
    try:
        # Define number of sentences based on duration
        if duration == 45:
            num_of_sentences = 10
        elif duration == 60:
            num_of_sentences = 13
        elif duration == 75:
            num_of_sentences = 16
        else:
            print("Invalid duration")
            return

        # Request a full story with the required number of sentences
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a short storyteller."},
                {
                    "role": "user",
                    "content": f"Write a compelling story in exactly {num_of_sentences} sentences about {prompt}, each sentence should be of 11 words each, A sentence ends when there is a full stop(.). Keep the language concise yet engaging, focusing on clear narrative flow and emotional depth. Ensure each sentence naturally follows the previous one, creating a cohesive short story.",
                },
            ],
        )

        # Extract the full story content
        story = completion.choices[0].message.content

        # Split the story into sentences
        sentences = story.split(". ")

        # Write each sentence on a new line in the file
        with open("prompts/subtitle_gen_prompts.txt", "w") as f:
            for sentence in sentences:
                if sentence.strip():  # Skip empty sentences
                    f.write(sentence.strip() + ".\n")

        print("Story successfully written to subtitle_gen_prompts.txt")

    except Exception as e:
        print(f"Error: {e}")


# Generate story-prompts to which are going to be used to gen images
def image_generator_story(prompt: str, duration: int):
    try:
        # Define number of sentences based on duration
        if duration == 45:
            num_of_sentences = 10
        elif duration == 60:
            num_of_sentences = 13
        elif duration == 75:
            num_of_sentences = 16
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
                    "content": f"""Create a visually rich story of exactly {num_of_sentences} sentences based on the prompt: '{prompt}'.

                        Each sentence should be around 50 words, focusing on vivid visual elements (colors, textures, light), sensory details (sounds, smells, touch), motion, and atmosphere. Alternate between wide, sweeping views and close-up details to create a cinematic, immersive narrative that inspires visual storytelling.Just write the sentences.

                        Ensure each sentence serves as a clear, captivating visual scene, perfect for illustrations or film compositions.""",
                },
            ],
        )
        # Extract the full story content
        story = completion.choices[0].message.content.strip()

        # Split the story into sentences
        sentences = []
        for sentence in story.split("."):
            sentence = sentence.strip()
            if sentence:
                sentences.append(sentence)

        # Write up to the specified number of sentences (e.g., 10)
        with open("prompts/img_gen_prompts.txt", "w") as f:
            for i in range(min(num_of_sentences, len(sentences))):
                f.write(sentences[i] + ".\n")

        print("Story successfully written to img_gen_prompts.txt")

    except Exception as e:
        print(f"Error: {e}")
