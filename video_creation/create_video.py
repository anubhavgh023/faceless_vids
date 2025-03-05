import asyncio
import os
import time
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import logging
from dotenv import load_dotenv
from openai import OpenAI  # Corrected OpenAI import
from config.logger import get_logger,log_time_taken

logger = get_logger(__name__)

# Image processing
from video_creation.image_processing import (
    make_video_from_image,
    merge_videos,
    add_particle_effect,
)

# Audio processing
from video_creation.audio_processing import merge_audios

# Subtitle processing
from video_creation.subtitle_processing import (
    add_subtitle_with_audio
)

# Video processing
from video_creation.video_processing import add_subtitles_with_audio, add_bg_music

# ---- TESTING ---------#
# Image processing
# from image_processing import (
#     make_video_from_image,
#     merge_videos,
#     add_particle_effect,
# )

# # Audio processing
# from audio_processing import merge_audios

# # Subtitle processing
# from subtitle_processing import (
#     generate_subtitle_file,
#     modify_subtitle_style,
# )

# # Video processing
# from video_processing import add_subtitles_with_audio, add_bg_music

#----- LOGGER ---
# logger = logging.getLogger()
# # Function to log timing information
# def log_time_taken(function_name, start_time, end_time):
#     time_taken = end_time - start_time
#     log_message = f"{function_name}: {time_taken:.2f} seconds"
#     logger.info(log_message)
#-----


# Get the current script directory (create_video.py)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define path relative to this script's directory
assets_dir = os.path.join(script_dir, "assets")
images_dir = os.path.join(assets_dir, "images")
audio_dir = os.path.join(assets_dir, "audio")
videos_dir = os.path.join(assets_dir, "videos")
subtitles_dir = os.path.join(assets_dir, "subtitles")
particle_system_dir = os.path.join(videos_dir, "particle_system")
bg_music_dir = os.path.join(assets_dir, "bg_music")
prompts_path = os.path.join(script_dir, "../", "prompts", "subtitle_gen_prompts.txt")

# Load OpenAI Whisper client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Using OpenAI client


# Generate a video from a given image.
def process_image_to_video(image_path, index, aspect_ratio):
    start_time = time.time()  # Start time
    output_video = os.path.join(videos_dir, f"story_video_{index + 1}.mp4")
    make_video_from_image(image_path, index, output_video, aspect_ratio)
    end_time = time.time()  # End time
    log_time_taken(f"process_image_to_video (Image {index + 1})", start_time, end_time)
    return output_video


# Generate subtitles using Whisper from OpenAI.
def generate_subtitles_from_audio():
    start_time = time.time()  # Start time
    audio_file_path = os.path.join(audio_dir, "combined_story_audio.wav")
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )
    end_time = time.time()  # End time
    log_time_taken("generate_subtitles_from_audio (Whisper)", start_time, end_time)
    return transcript


# Main function to create the video from images, audio, and subtitles.
async def create_video(output_video_duration: int,bgm_audio: str,aspect_ratio:str):

# testing
# def create_video(output_video_duration: int, bgm_audio: str, aspect_ratio: str):
    # Ensure directories exist
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(subtitles_dir, exist_ok=True)
    os.makedirs(particle_system_dir, exist_ok=True)
    os.makedirs(bg_music_dir, exist_ok=True)

    # Read the prompts
    with open(prompts_path, "r") as f:
        captions = f.read().splitlines()

    # Count the no. of prompts
    segments = len(captions)
    images = [
        os.path.join(images_dir, f"story_img_{i + 1}.png") for i in range(segments)
    ]
    audios = [os.path.join(audio_dir, f"prompt_{i + 1}.mp3") for i in range(segments)]

    # Step 1: Generate videos from images
    start_time_parallel = time.time()
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        video_futures = [
            executor.submit(process_image_to_video, img, i, aspect_ratio)
            for i, img in enumerate(images)
        ]
        # audio_future = executor.submit(process_audio, audios)
        processed_videos = [future.result() for future in video_futures]
        # combined_audio = audio_future.result()  # Ensure the audio is created

    end_time_parallel = time.time()
    log_time_taken(
        "Parallel tasks: img to videos:",
        start_time_parallel,
        end_time_parallel,
    )

    # # Step 2: Generate transcript synchronously
    start_transcript_time = time.time()
    combined_audio = os.path.join(audio_dir, "combined_story_audio.wav")
    transcript = generate_subtitles_from_audio()
    end_transcript_time = time.time()
    log_time_taken("Transcript generation:", start_transcript_time, end_transcript_time)

    # Step 3: Merge all generated videos (sequential)
    start_time_merge = time.time()
    merged_video = os.path.join(videos_dir, "merged_story_video.mp4")
    merge_videos(processed_videos, merged_video)
    end_time_merge = time.time()
    log_time_taken("merge_videos", start_time_merge, end_time_merge)

    #---------------------------
    # Step 4: Add particle effect (sequential)
    # start_time_particle = time.time()
    # pstyle = "test-rising-embers"
    # particle_video = os.path.join(particle_system_dir, f"{pstyle}.mp4")
    # particle_final_output_file = os.path.join(videos_dir, "particle_final_output.mp4")
    # add_particle_effect(
    #     input_video=merged_video,
    #     output_video_duration=output_video_duration,
    #     particle_video=particle_video,
    #     output_video=particle_final_output_file,
    # )
    # end_time_particle = time.time()
    # log_time_taken("add_particle_effect", start_time_particle, end_time_particle)
    #---------------------------

    #-----
    # # Step 5: Generate subtitle file using the Whisper transcription (sequential)
    # start_time_subtitles = time.time()
    # subtitle_file = os.path.join(subtitles_dir, "story_subtitles.srt")
    # generate_subtitle_file(transcript.words, subtitle_file)
    # end_time_subtitles = time.time()
    # log_time_taken("generate_subtitle_file", start_time_subtitles, end_time_subtitles)

    # # Step 6: Modify the subtitle style (sequential)
    # start_time_modify_subtitle = time.time()
    # modified_subtitle_file = os.path.join(subtitles_dir, "story_subtitles.ass")
    # modify_subtitle_style(subtitle_file, modified_subtitle_file)
    # end_time_modify_subtitle = time.time()
    # log_time_taken(
    #     "modify_subtitle_style", start_time_modify_subtitle, end_time_modify_subtitle
    # )

    # # Step 7: Add subtitles with audio to the video (sequential)
    # start_time_final_video = time.time()
    # final_video_with_subtitles = os.path.join(
    #     videos_dir, "final_output_video_subtitles.mp4"
    # )
    # add_subtitles_with_audio(
    #     merged_video,  # particle_final_output_file,
    #     modified_subtitle_file,
    #     combined_audio,
    #     final_video_with_subtitles,
    # )
    # end_time_final_video = time.time()
    # log_time_taken(
    #     "add_subtitles_with_audio", start_time_final_video, end_time_final_video
    # )
    #-------------

    ##
    # Step:
    final_video_with_subtitles = os.path.join(
        videos_dir, "final_output_video_subtitles.mp4"
    )
    add_subtitle_with_audio(
        merged_video,
        combined_audio,
        transcript,
        final_video_with_subtitles
    )
    

    # If there is no bgm_audio selected, don't do this step.
    # Step 8: Add background music to the final video (sequential)
    if bgm_audio != "":
        start_time_bg_music = time.time()
        final_output_video = os.path.join(videos_dir, "final_output_video_bgm.mp4")
        bg_music_path = os.path.join(
            bg_music_dir, f"{bgm_audio}.mp3"
        )  # passing selected bgm audio
        add_bg_music(final_video_with_subtitles, bg_music_path, final_output_video)
        end_time_bg_music = time.time()
        log_time_taken("add_bg_music", start_time_bg_music, end_time_bg_music)

    logger.info("Video processing completed successfully!")


# Entry point for running this script directly
if __name__ == "__main__":
    asyncio.run(create_video(output_video_duration=45, bgm_audio="dark", aspect_ratio="9:16"))
