import os
import requests
from pydub import AudioSegment
from dotenv import load_dotenv
import io
import logging
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger()

# Load environment variables
load_dotenv()
XI_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Default voices dictionary
DEFAULT_VOICES = {
    "alice": "Xb7hH8MSUJpSbSDYk0k2",
    "aria": "9BWtsMINqrJLrRacOk9x",
    "bill": "pqHfZKP75CvOlQylNhV4",
    "brian": "nPczCjzI2devNBz1zQrb",
    "callum": "N2lVS1w4EtoT3dr4eOWO",
    "charlie": "IKne3meq5aSn9XLyUdCD",
    "charlotte": "XB0fDUnXU5powFXDhCwa",
    "chris": "iP95p4xoKVk53GoZ742B",
    "daniel": "onwK4e9ZLuTAKqWW03F9",
    "eric": "cjVigY5qzO86Huf0OWal",
    "george": "JBFqnCBsd6RMkjVDRZzb",
    "jessica": "cgSgspJ2msm6clMCkdW9",
    "laura": "FGY2WhTYpPnrIDTdsKH5",
    "liam": "TX3LPaxmHKxFdv7VOQHJ",
    "lily": "pFZP5JQG7iQjIQuC4Bku",
    "matilda": "XrExE9yKIg1WjnnlVkGX",
    "river": "SAz9YHcvj6GT2YYXdXww",
    "roger": "CwhRBWXzGAHq8TQ4Fs17",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
    "will": "bIHbv24MWmeRgasZH58o",
}


def create_voice_clone(voice_samples: List[str], voice_name: str) -> Optional[str]:
    """Create a voice clone from provided samples."""
    try:
        files = [
            ('files', (os.path.basename(f), open(f, 'rb'), 'audio/mpeg'))
            for f in voice_samples
        ]

        response = requests.post(
            "https://api.elevenlabs.io/v1/voices/add",
            headers={"xi-api-key": XI_API_KEY},
            data={
                "name": voice_name,
                "description": "Temporary cloned voice"
            },
            files=files,
        )

        if response.status_code != 200:
            raise Exception(f"Voice cloning failed: {response.text}")

        voice_id = response.json()["voice_id"]
        logger.info(f"Successfully created voice clone with ID: {voice_id}")
        return voice_id

    except Exception as e:
        logger.error(f"Error in voice cloning: {str(e)}")
        return None

def delete_cloned_voice(voice_id: str) -> bool:
    """Delete a cloned voice by ID."""
    try:
        response = requests.delete(
            f"https://api.elevenlabs.io/v1/voices/{voice_id}",
            headers={"xi-api-key": XI_API_KEY}
        )

        if response.status_code != 200:
            raise Exception(f"Voice deletion failed: {response.text}")

        logger.info(f"Successfully deleted cloned voice: {voice_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting voice: {str(e)}")
        return False

def generate_audio(
    character: str,
    voice_samples: Optional[List[str]] = None,
    output_path: str = "assets/audio/combined_story_audio.wav",
) -> Tuple[bool, str]:

    try:
        # Read all prompts
        with open("prompts/subtitle_gen_prompts.txt", "r") as f:
            paragraphs = f.read().splitlines()

        # Determine voice ID
        voice_id = None
        is_clone = False

        if character.lower() == "clone":
            if not voice_samples:
                return False, "Voice samples required for cloning"
            
            voice_id = create_voice_clone(voice_samples, "temporary_voice")
            if not voice_id:
                return False, "Voice cloning failed"
            is_clone = True
        else:
            # Using default voice
            character = character.lower()
            if character not in DEFAULT_VOICES:
                return False, f"Voice '{character}' not found in default voices"
            voice_id = DEFAULT_VOICES[character]

        try:
            # Generate audio segments
            segments = []
            for i, paragraph in enumerate(paragraphs):
                is_last_paragraph = i == len(paragraphs) - 1
                is_first_paragraph = i == 0
                
                response = requests.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
                    json={
                        "text": paragraph,
                        "model_id": "eleven_multilingual_v2",
                        "previous_text": None if is_first_paragraph else " ".join(paragraphs[:i]),
                        "next_text": None if is_last_paragraph else " ".join(paragraphs[i + 1:]),
                    },
                    headers={"xi-api-key": XI_API_KEY}
                )

                if response.status_code != 200:
                    raise Exception(f"API Error: {response.status_code} - {response.text}")

                logger.info(f"Generated audio for paragraph {i + 1}/{len(paragraphs)}")
                segments.append(AudioSegment.from_mp3(io.BytesIO(response.content)))

            # Combine all segments
            final_audio = segments[0]
            for segment in segments[1:]:
                final_audio = final_audio + segment

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Export final audio
            final_audio.export(output_path, format="wav")
            logger.info(f"Successfully exported audio to {output_path}")

            return True, output_path

        finally:
            # Clean up cloned voice if used
            if is_clone and voice_id:
                delete_cloned_voice(voice_id)

    except Exception as e:
        error_msg = f"Error in generate_audio: {str(e)}"
        logger.error(error_msg)
        return False, error_msg