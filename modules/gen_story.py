# normal generation of sentences, improved prompts
import asyncio
from openai import OpenAI
import os
from dotenv import load_dotenv
import concurrent.futures
import asyncio
import re
import logging
from config.logger import get_logger

load_dotenv()

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

logger = get_logger(__name__)

# Generate Script : For generating scripts repeatedly
async def generate_script(prompt: str, duration: int):
    try:
        # Define number of sentences based on duration
        if duration == 45:
            num_of_sentences = 7
        elif duration == 60:
            num_of_sentences = 11
        elif duration == 75:
            num_of_sentences = 14
        else:
            logger.info("Invalid duration")
            return

        # Function to request story generation
        def request_story():
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a short storyteller."},
                    {
                        "role": "user",
                        "content": (
                            f"Write a cohesive and compelling story about '{prompt}'. "
                            f"The story must have exactly {num_of_sentences} sentences. "
                            f"Each sentence must be exactly 12 words long, no more, no less. "
                            f"A sentence ends when there is a period (.). Use simple, expressive language, "
                            f"punctuation (e.g., !, ?), and capitalization to add emotion. "
                            f"Ensure no extra sentences and no incomplete ones—strictly {num_of_sentences}. "
                            f"The story should flow naturally from beginning to end."
                        ),
                    },
                ],
            )
            return completion.choices[0].message.content

        # Generate the story with a retry mechanism
        max_retries = 4
        retries = 0

        while retries < max_retries:
            story = request_story()

            # Split the story into sentences
            sentences = story.split(". ")
            sentences = [
                s.strip() + "." for s in sentences if s.strip()
            ]  # Clean and ensure full stops

            if len(sentences) == num_of_sentences:
                break  # Exit loop if sentence count is correct

            retries += 1
            logger.info(
                f"Retry {retries}/{max_retries}: Expected {num_of_sentences} sentences, "
                f"but got {len(sentences)}. Retrying story generation..."
            )

        if retries == max_retries:
            logger.error(
                "Max retries reached. Could not generate the story with the correct sentence count."
            )
            return

        return sentences

        logger.info("Story successfully written to subtitle_gen_prompts.txt")

    except Exception as e:
        logger.error(f"Error: {e}")


async def subtitle_generator_story(prompt: str, duration: int):
    try:
        # Define number of sentences based on duration
        if duration == 45:
            num_of_sentences = 7
        elif duration == 60:
            num_of_sentences = 11
        elif duration == 75:
            num_of_sentences = 14
        else:
            logger.info("Invalid duration")
            return

        # Function to request story generation
        def request_story():
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a short storyteller."},
                    {
                        "role": "user",
                        "content": (
                            f"Write a cohesive and compelling story about '{prompt}'. "
                            f"The story must have exactly {num_of_sentences} sentences. "
                            f"Each sentence must be exactly 12 words long, no more, no less. "
                            f"A sentence ends when there is a period (.). Use simple, expressive language, "
                            f"punctuation (e.g., !, ?), and capitalization to add emotion. "
                            f"Ensure no extra sentences and no incomplete ones—strictly {num_of_sentences}. "
                            f"The story should flow naturally from beginning to end."
                        ),
                    },
                ],
            )
            return completion.choices[0].message.content

        # Generate the story with a retry mechanism
        max_retries = 4
        retries = 0

        while retries < max_retries:
            story = request_story()

            # Split the story into sentences
            sentences = story.split(". ")
            sentences = [
                s.strip() + "." for s in sentences if s.strip()
            ]  # Clean and ensure full stops

            if len(sentences) == num_of_sentences:
                break  # Exit loop if sentence count is correct

            retries += 1
            logger.info(
                f"Retry {retries}/{max_retries}: Expected {num_of_sentences} sentences, "
                f"but got {len(sentences)}. Retrying story generation..."
            )

        if retries == max_retries:
            logger.error(
                "Max retries reached. Could not generate the story with the correct sentence count."
            )
            return

        # Write each sentence on a new line in the file
        with open("prompts/subtitle_gen_prompts.txt", "w") as f:
            for sentence in sentences:
                f.write(sentence + "\n")

        logger.info("Story successfully written to subtitle_gen_prompts.txt")

    except Exception as e:
        logger.error(f"Error: {e}")


# Generate story-prompts to which are going to be used to gen images
async def image_generator_story(prompt: str, duration: int):
    try:
        # Define number of sentences based on duration
        if duration == 45:
            num_of_sentences = 7
        elif duration == 60:
            num_of_sentences = 11
        elif duration == 75:
            num_of_sentences = 14
        else:
            logger.error("Invalid duration")
            return

        # Request a full story with the required number of sentences
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a storyteller."},
                {
                    "role": "user",
                    "content": f"""
                Create a visually rich and cinematic story of exactly {num_of_sentences} sentences based on the following prompt:
                '{prompt}'
                Each sentence should vividly depict:

                - Mention character's physicals and environment
                - A cinematic, slightly distant perspective, capturing the subject within their environment.
                - Dynamic and atmospheric details (light, weather, shadows).
                - Rich visual elements (colors, textures, motion) that bring the scene to life.
                
                Focus on crafting a cohesive narrative where each sentence paints a vivid image that inspires cinematic illustration or film composition. Avoid extreme close-ups or very distant views; aim for a medium cinematic perspective with a harmonious blend of subject and surroundings.
            """,
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

        logger.info("Story successfully written to img_gen_prompts.txt")

    except Exception as e:
        logger.error(f"Error: {e}")


# -- TESTING --
if __name__ == "__main__":
    async def main():
        
        prompt = "jungle adventure in amazon rain forest"
        duration = 45
        await subtitle_generator_story(prompt, duration)

    asyncio.run(main())
