# WORKING


import os
import subprocess
import pysubs2

# Function to extract the audio duration using ffprobe
def get_audio_duration(audio_file):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_file,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return float(result.stdout)


# Function to generate word-by-word timings (if needed)
def generate_word_timings(caption, audio_file):
    duration = get_audio_duration(audio_file)
    words = caption.split()
    word_duration = duration / len(words)

    # Create timing list for each word
    return [
        (word, i * word_duration, (i + 1) * word_duration)
        for i, word in enumerate(words)
    ]


def make_video_from_image(image, output_video):
    # Set each video duration
    video_duration = 7

    ffmpeg_command = (
        f"ffmpeg -y -loop 1 -i {image} "
        # Smooth zoom in and out effect
        f"-filter_complex \"zoompan=z='if(lte(mod(it*25,42),10),min(max(zoom,pzoom)+0.005,1.5),max(min(max(zoom,pzoom)-0.002,1.8),1))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=2,scale=1024:1792\" "
        f"-t {video_duration} -c:v libx264 -pix_fmt yuv420p -r 30 {output_video}"
    )

    subprocess.run(ffmpeg_command, shell=True)
    print(f"Video from image saved as '{output_video}'")


# Function to merge videos
def merge_videos(input_videos, output_video):
    with open("videos_list.txt", "w") as file:
        for video in input_videos:
            file.write(f"file '{video}'\n")

    subprocess.run(
        f"ffmpeg -y -f concat -safe 0 -i videos_list.txt -c copy {output_video}",
        shell=True,
    )
    os.remove("videos_list.txt")
    print(f"Merged video saved as '{output_video}'")


# Function to stabilize video
def stabilize_video(input_video, stabilized_video):
    subprocess.run(
        f"ffmpeg -y -i {input_video} -vf vidstabdetect=shakiness=10:accuracy=15 -f null -",
        shell=True,
    )
    subprocess.run(
        f"ffmpeg -y -i {input_video} -vf vidstabtransform=smoothing=30:input=transforms.trf "
        f"-c:v libx264 -pix_fmt yuv420p -r 30 {stabilized_video}",
        shell=True,
    )
    print(f"Stabilized video saved as '{stabilized_video}'")


# Function to merge audios
def merge_audios(input_audios, output_audio):
    with open("audios_list.txt", "w") as file:
        for audio in input_audios:
            file.write(f"file '{audio}'\n")

    subprocess.run(
        f"ffmpeg -y -f concat -safe 0 -i audios_list.txt -c copy {output_audio}",
        shell=True,
    )
    os.remove("audios_list.txt")
    print(f"Merged audio saved as '{output_audio}'")

# Function to generate a subtitle file with correct .srt formatting
def generate_subtitle_file(words_with_timings, output_subtitle_file):
    try:
        with open(output_subtitle_file, "w") as f:
            for i, (word, start, end) in enumerate(words_with_timings):
                # Correct time format: hours:minutes:seconds,milliseconds
                start_time = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02},{int((start % 1) * 1000):03}"
                end_time = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02},{int((end % 1) * 1000):03}"
                
                # Write subtitle block in the correct format
                f.write(f"{i + 1}\n{start_time} --> {end_time}\n{word}\n\n")
        
        print(f"Subtitle file saved as '{output_subtitle_file}'")
    
    except Exception as e:
        print(f"Error generating subtitle file: {e}")

# Function to generate modified subtitles

def modify_subtitle_style(srt_file, output_ass_file):
    try:
        # Load the .srt file
        subs = pysubs2.load(srt_file, encoding="utf-8")

        # Define the style modifications
        for style in subs.styles.values():
            style.fontname = "DK Longreach"  # Change font as needed
            style.fontsize = 28  # Font size
            style.bold = True  # Make the text bold
            style.primarycolor = pysubs2.Color(255, 255, 255)  # White text
            style.backcolor = pysubs2.Color(0, 0, 0, 255) # Black background
            style.outlinecolor = pysubs2.Color(0,0,0) # Black outline
            style.outline = 2  # Outline size
            style.alignment = pysubs2.Alignment.MIDDLE_CENTER # Center the caption at the bottom of the video

        # Apply fade effect to each dialogue
        for event in subs.events:
            fade_in_ms = 100  # Duration of fade-in (100 ms)
            fade_out_ms = 100  # Duration of fade-out  (100 ms)
            event.text = f"{{\\fad({fade_in_ms},{fade_out_ms})}}{event.text}"

        # Save the modified subtitles as .ass file
        subs.save(output_ass_file)
        print(f"Modified subtitles saved as '{output_ass_file}'")
    except Exception as e:
        print(f"Error modifying subtitles: {e}")


# Function to add subtitles with merged audio to the video
def add_subtitles_with_audio(input_video, subtitle_file, audio_file, output_video):
    ffmpeg_command = (
        f"ffmpeg -y -i {input_video} -i {audio_file} "
        f'-vf "ass={subtitle_file}:fontsdir=fonts" ' # adding the fonts dir to select different fonts for caption
        f"-c:v libx264 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k {output_video}"
    )
    try:
        subprocess.run(ffmpeg_command, shell=True, check=True)
        print(f"Video with subtitles and audio saved as '{output_video}'")
    except subprocess.CalledProcessError as e:
        print(f"Error adding subtitles to video '{input_video}': {e}")

# Function to add background music
def add_bg_music(final_video, bg_music_path, output_video):
    """Adds background music to the final video."""
    ffmpeg_command = (
        f"ffmpeg -i {final_video} -i {bg_music_path} "
        f'-filter_complex "[1:a]volume=0.08[a1];[0:a][a1]amix=inputs=2:duration=shortest" '
        f"-c:v copy -c:a aac -b:a 192k {output_video}"
    )
    subprocess.run(ffmpeg_command, shell=True)
    print(f"Video with background music saved as '{output_video}'")

# Main script to process multiple prompts
if __name__ == "__main__":
    images = [f"images/t4_story_img_{i}.png" for i in range(1, 6)]
    audios = [f"audio/prompt_{i}.mp3" for i in range(1, 6)]
    captions = [
        "A knight in shiny silver armor rides a black horse, entering a misty, dense forest.",
        "The knight encounters a mysterious figure with a glowing staff in the dark forest.",
        "The knight battles a fearsome red dragon on the edge of a rocky cliff, flames and sparks filling the air",
        "The knight rests by a fire, his armor reflecting the flames.",
        "The knight returns to a grand castle at dawn, the sun rising behind tall towers.",
    ]

    processed_videos = []

    # Step 1: Generate videos for each image (without audio)
    for i in range(5):
        output_video = f"videos/t4_story_video_{i+1}.mp4"
        make_video_from_image(images[i], output_video)
        processed_videos.append(output_video)

    # Step 2: Merge all generated videos
    merged_video = "videos/merged_story_video.mp4"
    merge_videos(processed_videos, merged_video)

    # Step 3: Merge all audios into one
    combined_audio = "audio/combined_story_audio.mp3"
    merge_audios(audios, combined_audio)

    # Step 4: Stabilize the merged video
    stabilized_video = "videos/stabilized_story_video.mp4"
    stabilize_video(merged_video, stabilized_video)

    # Step 5: Generate word-by-word timings for combined captions
    combined_caption = " ".join(captions)
    words_with_timings = generate_word_timings(combined_caption, combined_audio)

    # Step 6: Generate subtitle file: subtitle.srt
    subtitle_file = "subtitles/subtitle.srt" 
    generate_subtitle_file(words_with_timings, subtitle_file)

    # Step 7: Modify the generated subtitle file: modified_subtitle.ass
    modified_subtitle_file = "subtitles/modified_subtitle.ass"
    modify_subtitle_style(subtitle_file,modified_subtitle_file)

    # Step 8: Apply word-by-word modified subtitles to the stabilized video
    final_video = "videos/final_story_video_with_subtitles.mp4"
    add_subtitles_with_audio(
        stabilized_video, modified_subtitle_file, combined_audio, final_video
    )

    # Step 9: Add background music to the final video with subtitles
    bg_music_path = "bg_music/bg_1.mp3"
    final_video_with_music = "videos/final_story_video_with_bg_music.mp4"
    add_bg_music(final_video, bg_music_path, final_video_with_music)

    print(f"Final video saved as '{final_video_with_music}'")
