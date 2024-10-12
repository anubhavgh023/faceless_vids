from image_processing import make_video_from_image
from audio_processing import (
    merge_audios,
    generate_word_timings
)
from subtitle_processing import (
    generate_subtitle_file, 
    modify_subtitle_style
)
from video_processing import (
    merge_videos,
    stabilize_video,
    add_subtitles_with_audio,
    add_bg_music,
)

# Main script to process multiple prompts
if __name__ == "__main__":
    images = [f"assets/images/t4_story_img_{i}.png" for i in range(1, 6)]
    audios = [f"assets/audio/prompt_{i}.mp3" for i in range(1, 6)]
    captions = []
    # Read prompts again to use as captions
    with open("prompts/prompts.txt", "r") as f:
        captions = f.read().splitlines()

    processed_videos = []

    # Step 1: Generate videos for each image (without audio)
    for i in range(5):
        output_video = f"assets/videos/t4_story_video_{i + 1}.mp4"
        make_video_from_image(images[i], output_video)
        processed_videos.append(output_video)

    # Step 2: Merge all generated videos
    merged_video = "assets/videos/merged_story_video.mp4"
    merge_videos(processed_videos, merged_video)

    # Step 3: Merge all audios into one
    combined_audio = "assets/audio/combined_story_audio.mp3"
    merge_audios(audios, combined_audio)

    # Step 4: Stabilize the merged video
    stabilized_video = "assets/videos/stabilized_story_video.mp4"
    stabilize_video(merged_video, stabilized_video)

    # Step 5: Generate word-by-word timings for combined captions
    words_with_timings = generate_word_timings(captions)

    # Step 6: Generate subtitle file
    subtitle_file = "assets/subtitles/story_subtitles.srt"
    generate_subtitle_file(words_with_timings, subtitle_file)

    # Step 7: Modify the subtitle style
    modified_subtitle_file = "assets/subtitles/story_subtitles.ass"
    modify_subtitle_style(subtitle_file, modified_subtitle_file)

    # Step 8: Add subtitles with audio to the stabilized video
    final_video_with_subtitles = "assets/videos/final_video_with_subtitles.mp4"
    add_subtitles_with_audio(
        stabilized_video,
        modified_subtitle_file,
        combined_audio,
        final_video_with_subtitles,
    )

    # Step 9: Add background music to the final video
    final_output_video = "assets/videos/final_output_video.mp4"
    bg_music_path = (
        "assets/bg_music/bg_1.mp3"
    )
    add_bg_music(final_video_with_subtitles, bg_music_path, final_output_video)

    print("Video processing completed successfully!")