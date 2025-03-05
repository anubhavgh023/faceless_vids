import asyncio
from openai import OpenAI
import re
import os
from dotenv import load_dotenv
import logging
# from config.logger import get_logger

load_dotenv()

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

# logger = get_logger(__name__)

# Dictionary of styles
styles = {
    "custom": {
        "prompt": "Write a short, engaging story in a single paragraph with no dialogue or spoken lines. Use third-person narration to describe the events clearly and vividly. The story should begin with a dramatic or whimsical setup, introducing the problem in a way that captures attention. Describe how an unlikely hero steps up to solve the challenge creatively, using actions and descriptions to show their courage, kindness, or ingenuity. End with a satisfying resolution that highlights the main lesson or takeaway. The language should be simple, imaginative, and easy to follow, suitable for all ages, including young children."
    },
    "fun_facts": {
        "prompt": "Write a short and engaging paragraph that presents a surprising or little-known fact. Start with an attention-grabbing statement or statistic to hook the audience. Explain the fact in simple, easy-to-understand terms, adding details or context that make it relatable and memorable. Highlight the implications or a perspective that will leave the audience amazed or thinking differently. Use vivid language and keep the tone light, fun, and conversational."
    },
    "philosophy": {
        "prompt": "Write a short, thought-provoking piece in a single paragraph that connects philosophical ideas to modern life. Begin with an intriguing statement or question to grab attention, and then introduce a key philosophical concept in simple terms. Use relatable examples or practical insights to help the audience apply the idea to their own lives. Highlight timeless lessons or deeper truths while keeping the language accessible and engaging. Conclude with a memorable takeaway that leaves the audience reflecting."
    },
    "how_to": {
        "prompt": "Write a concise and engaging paragraph that provides actionable advice or steps to achieve the goal. Begin with a clear and intriguing statement to grab attention. Break down the solution into simple, easy-to-follow instructions, using vivid and relatable examples where needed. Keep the tone conversational and motivational."
    },
    "listicle": {
        "prompt": "Write a short, engaging listicle in a single paragraph that includes several quick tips or hacks related to the topic. Start with a surprising or attention-grabbing statement. Then, list practical, science-backed, or creative tips in a clear, snappy format."
    },
    "motivational": {
        "prompt": "Write a short, engaging, and motivational story in a single paragraph with no dialogue or spoken lines. Use third-person narration to vividly describe the situation and keep the language simple and easy to understand."
    },
    "business": {
        "prompt": "Write a concise and professional business story or insight in a single paragraph. Begin with a striking statistic, question, or anecdote to grab attention. Introduce a key lesson, strategy, or business concept in simple terms."
    },
    "horror": {
        "prompt": "Write a short, chilling horror story in a single paragraph. Begin with an unsettling or mysterious setup to draw the audience into the scene. Gradually build suspense by describing eerie details and strange occurrences."
    },
    "fantasy": {
        "prompt": "Write a short and imaginative fantasy story in a single paragraph. Start with a dramatic or whimsical moment to immediately immerse the reader in a magical world."
    },
    "life_hack": {
        "prompt": "Write a short and engaging paragraph that shares several practical and easy-to-implement life hacks related to the topic."
    },
    "personal": {
        "prompt": "Write a short, personal, and reflective story in a single paragraph. Start by describing a relatable challenge, struggle, or pivotal moment in life."
    },
    "stoic": {
        "prompt": "Write a short, reflective piece in a single paragraph that draws on Stoic philosophy to address a modern challenge or concept."
    },
}


async def generate_script(style: str, duration: int, topic: str):
    try:
        if style not in styles:
            print("Invalid style selected")
            return None

        duration_map = {45: 7, 60: 11, 75: 14}
        num_of_sentences = duration_map.get(duration)

        if not num_of_sentences:
            print("Invalid duration")
            return None

        style_prompt = styles[style]["prompt"]

        async def request_story():
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a short storyteller."},
                    {
                        "role": "user",
                        "content": (
                            f"{style_prompt} Topic: '{topic}'. The story must have exactly {num_of_sentences} sentences. "
                            f"Each sentence should be approximately 13 words long. "
                            f"A sentence ends when there is a period (.). Use simple, expressive language, "
                            f"punctuation (e.g., !, ?), and capitalization to add emotion. "
                            f"Ensure no extra sentences and no incomplete ones—strictly {num_of_sentences}. "
                            f"The story should flow naturally from beginning to end."
                        ),
                    },
                ],
            )
            return response.choices[0].message.content

        max_retries = 5
        retries = 0

        while retries < max_retries:
            story = await request_story()
            sentences = re.findall(r"[^.!?]+[.!?]", story.strip())
            sentences = [s.strip() for s in sentences]

            if len(sentences) >= num_of_sentences:
                sentences = sentences[:num_of_sentences]
                print(len(sentences))
                return sentences

            retries += 1
            print(
                f"Retry {retries}/{max_retries}: Expected {num_of_sentences} sentences, "
                f"but got {len(sentences)}. Retrying story generation..."
            )

        print(
            "Max retries reached. Could not generate the story with the correct sentence count."
        )
        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    style = "fun_facts"  # Change this to test different styles
    duration = 45  # Choose from 45, 60, 75
    topic = "The mysteries of black holes"  # Change this to test different topics

    # Run the async function
    result = asyncio.run(generate_script(style, duration, topic))

    # # Print the generated output
    # if result:
    #     print("\nGenerated Story:\n")
    #     for sentence in result:
    #         print(sentence)


if __name__ == "__main__":
    main()
