from openai import OpenAI
import requests
import os
from dotenv import load_dotenv
import datetime
import pysubs2
import logging

load_dotenv()

logger = logging.getLogger()

# client = OpenAI()
# client.api_key = os.getenv("OPENAI_API_KEY")

# audio_file = open("assets/audio/combined_story_audio.mp3", "rb")

# transcript = client.audio.transcriptions.create(
#   file=audio_file,
#   model="whisper-1",
#   response_format="verbose_json",
#   timestamp_granularities=["word"]
# )


# check the str file for missing milliseconds
def format_time_with_default_milliseconds(seconds):
    time_str = str(datetime.timedelta(seconds=seconds))
    if "." not in time_str:
        time_str += ".0600"  # Add default milliseconds if missing
    time_str = time_str.replace('.', ',')[:12]
    return time_str

# Function to generate a subtitle file with correct .srt formatting
def generate_subtitle_file(transcript_words, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as srt_file:
            subtitle_index = 1
            current_line = []
            line_start = transcript_words[0].start

            for i, word in enumerate(transcript_words):
                current_line.append(word.word)
                
                if len(current_line) == 2 or i == len(transcript_words) - 1:
                    line_end = word.end
                    line_text = ' '.join(current_line)
                    
                    start_time = format_time_with_default_milliseconds(line_start)
                    end_time = format_time_with_default_milliseconds(line_end)
                    
                    srt_file.write(f"{subtitle_index}\n")
                    srt_file.write(f"{start_time} --> {end_time}\n")
                    srt_file.write(f"{line_text}\n\n")
                    
                    subtitle_index += 1
                    current_line = []
                    if i < len(transcript_words) - 1:
                        line_start = transcript_words[i + 1].start

        logger.info(f"SRT file has been generated: {output_file}")

    except Exception as e:
        logger.error(f"Error generating subtitle file: {e}")

def modify_subtitle_style(srt_file, ass_file):
    # Load the SRT file
    subs = pysubs2.load(srt_file, encoding="utf-8")

    # Modify the default subtitle style
    for style in subs.styles.values():
        style.fontname = "Open Sans"
        style.fontsize = 16
        style.bold = True
        style.primarycolor = pysubs2.Color(255, 255, 255)  # White
        style.backcolor = pysubs2.Color(0, 0, 0, 255)  # Black background
        style.outlinecolor = pysubs2.Color(0, 0, 0)  # Black outline
        style.outline = 1.5
        style.alignment = pysubs2.Alignment.MIDDLE_CENTER

        # style.backcolor = pysubs2.Color(255,192,18,80) # yellow
        # style.backcolor = pysubs2.Color(0, 0, 139, 80)  # Dark Blue
        # style.backcolor = pysubs2.Color(75, 0, 130, 100)  # Dark Purple
        # style.shadow = 1

    # Ensure subtitles and timings are handled properly
    for line in subs:
        # Ensure no timing info is appended to the text
        line_text = line.text.strip()  # Clean any leading/trailing whitespace
        words = line_text.split()  # Split text into words
        word_duration = line.duration / len(words) if words else 0

        current_time = line.start
        new_events = []

        for i, word in enumerate(words):
            end_time = current_time + word_duration
            # highlighted_text = f"{{\\c&HCC99FF&}}{word}{{\\c&HFFFFFF&}}" # purple/white
            # highlighted_text = f"{{\\c&H00D7FF&}}{word}{{\\c&HFFFFFF&}}"  # gold/white
            highlighted_text = f"{{\\c&HB3EBFF&}}{word}{{\\c&HFFFFFF&}}"  # off-white/white

            # Create a new event for each word with highlighting
            new_line = pysubs2.SSAEvent(
                start=current_time, end=end_time, text=highlighted_text
            )
            new_events.append(new_line)

            current_time = end_time

        # Replace the original line with multiple word-level events
        subs.events.remove(line)
        subs.events.extend(new_events)

    # Save the result to ASS format
    subs.save(ass_file)

    logger.info(f"str file modified: {ass_file}")
