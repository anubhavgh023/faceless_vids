# normal generation of sentences, improved prompts
import asyncio
from openai import OpenAI
import os
from dotenv import load_dotenv
import concurrent.futures
import asyncio
import re
import logging

load_dotenv()

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

async def img_gen_prompts_from_script(script):
    """
    Takes a list of script sentences, enhances each into a vivid cinematic description (max 50 words),
    and writes them to a file while maintaining the original script's length.
    """
    try:
        # Ensure script is a valid non-empty list
        if not isinstance(script, list) or not script:
            print("Error: Script must be a non-empty list of sentences.")
            return

        enhanced_sentences = []

        # Process each line separately
        for line in script:
            if not line.strip():  # Skip empty lines
                continue

            try:
                # Send the line to OpenAI for enhancement with a max word limit
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a storyteller. Your job is to enhance a simple sentence into a visually rich, cinematic description, limited to 50 words.",
                        },
                        {
                            "role": "user",
                            "content": f"""
                            Enhance the following script line into a vivid, cinematic description (max 50 words):
                            '{line}'
                            
                            - Describe the character's appearance and surroundings.
                            - Use a cinematic, slightly distant perspective, capturing the subject in their environment.
                            - Add atmospheric details like lighting, shadows, and weather.
                            - Use dynamic and sensory-rich language to evoke a film-like scene.
                            - Ensure the description is **at most 50 words**.
                            """,
                        },
                    ],
                )

                # Extract the enhanced description
                enhanced_line = response.choices[0].message.content.strip()

                # Ensure word limit compliance (sometimes AI may exceed the limit)
                enhanced_line = " ".join(
                    enhanced_line.split()[:50]
                )  # Trim to max 50 words

                enhanced_sentences.append(enhanced_line)

            except Exception as api_error:
                print(f"Error processing line: '{line}' - {api_error}")
                enhanced_sentences.append(
                    line
                )  # Fallback: Use original line if API fails

        # Ensure sentence count matches the original script
        while len(enhanced_sentences) < len(script):
            enhanced_sentences.append(
                "Description unavailable."
            )  # Placeholder for missing entries

        # Write enhanced prompts to file
        with open("prompts/img_gen_prompts.txt", "w", encoding="utf-8") as f:
            for enhanced_line in enhanced_sentences:
                f.write(enhanced_line + "\n")

        print(
            f"Successfully written {len(enhanced_sentences)} sentences to img_gen_prompts.txt"
        )

    except Exception as e:
        print(f"Unexpected error: {e}")


# Example Usage
script_lines = [
    "A man walks alone on an empty street.",
    "The rain drizzles softly, reflecting neon lights.",
    "A shadow moves behind the alleyway.",
]

# Run the async function
asyncio.run(img_gen_prompts_from_script(script_lines))
