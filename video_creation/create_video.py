import os
import concurrent.futures
# from video_creation.image_processing import make_video_from_image, merge_videos, add_particle_effect
# from video_creation.audio_processing import merge_audios,generate_word_timings
# from video_creation.subtitle_processing import generate_subtitle_file, modify_subtitle_style
# from video_creation.video_processing import add_subtitles_with_audio, add_bg_music

# testing: cd video_creation
from image_processing import make_video_from_image, merge_videos, add_particle_effect
from audio_processing import merge_audios,generate_word_timings
from subtitle_processing import generate_subtitle_file, modify_subtitle_style
from video_processing import add_subtitles_with_audio, add_bg_music


def process_image_to_video(image_path, index, aspect_ratio="1024:1728"):
    """Generate a video from a given image."""
    output_video = f"assets/videos/story_video_{index + 1}.mp4"
    make_video_from_image(image_path, index, output_video, aspect_ratio)
    return output_video

def process_audio(audio_paths):
    """Merge audio files into a single audio file."""
    combined_audio = "assets/audio/combined_story_audio.mp3"
    merge_audios(audio_paths, combined_audio)
    return combined_audio

def process_word_timings(captions):
    """Generate word timings based on the given captions."""
    return generate_word_timings(captions)

def create_video():
    """Main function to create the video from images, audio, and subtitles."""

    #  -- Get the subtitles --

    # get path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Create the relative path to the prompts directory
    prompts_path = os.path.join(script_dir, "../..", "faceless_vids","prompts", "subtitle_gen_prompts.txt")
    
    # Normalize the path to handle any potential issues with path separators
    prompts_path = os.path.normpath(prompts_path)
    with open(prompts_path, "r") as f:
        captions = f.read().splitlines()
    # -- Get the subtitles --

    segments = len(captions)
    final_video_duration = segments * 6  # 6 seconds for each video
    images = [f"assets/images/story_img_{i + 1}.png" for i in range(segments)]
    audios = [f"assets/audio/prompt_{i + 1}.mp3" for i in range(segments)]

    # Step 1 & 4: Generate videos from images and process audio in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        video_futures = [executor.submit(process_image_to_video, img, i) for i, img in enumerate(images)]
        audio_future = executor.submit(process_audio, audios)
        word_timing_future = executor.submit(process_word_timings, captions)

        processed_videos = [future.result() for future in video_futures]
        combined_audio = audio_future.result()
        words_with_timings = word_timing_future.result()

    # Step 2: Merge all generated videos (sequential)
    merged_video = "assets/videos/merged_story_video.mp4"
    merge_videos(processed_videos, merged_video)

    # Step 3: Add particle effect (sequential)
    pstyle = "rising_embers"
    particle_video = f"assets/videos/particle_system/{pstyle}.mp4"
    particle_final_output_file = "assets/videos/particle_final_output.mp4"
    add_particle_effect(input_video=merged_video, input_video_duration=final_video_duration, particle_video=particle_video, output_video=particle_final_output_file)

    # Step 5 & 6: Generate subtitle file (sequential)
    subtitle_file = "assets/subtitles/story_subtitles.srt"
    generate_subtitle_file(words_with_timings, subtitle_file)

    # Step 7: Modify the subtitle style (sequential)
    modified_subtitle_file = "assets/subtitles/story_subtitles.ass"
    modify_subtitle_style(subtitle_file, modified_subtitle_file)

    # Step 8: Add subtitles with audio to the video (sequential)
    final_video = particle_final_output_file
    final_video_with_subtitles = "assets/videos/final_video_with_subtitles.mp4"
    add_subtitles_with_audio(final_video, modified_subtitle_file, combined_audio, final_video_with_subtitles)

    # Step 9: Add background music to the final video (sequential)
    final_output_video = "assets/videos/final_output_video.mp4"
    bg_music_path = "assets/bg_music/bgm_4.mp3"
    add_bg_music(final_video_with_subtitles, bg_music_path, final_output_video)

    print("Video processing completed successfully!")

# Entry point for running this script directly
if __name__ == "__main__":
    create_video()
