import os
import subprocess


# Function to merge videos
def merge_videos(input_videos, output_video):
    try:
        with open("videos_list.txt", "w") as file:
            for video in input_videos:
                file.write(f"file '{video}'\n")

        subprocess.run(
            f"ffmpeg -y -f concat -safe 0 -i videos_list.txt -c copy {output_video}",
            shell=True,
            check=True,
        )
        # os.remove("videos_list.txt")
        print(f"Merged video saved as '{output_video}'")
    except Exception as e:
        print(f"Error merging videos: {e}")


# Function to stabilize video
def stabilize_video(input_video, stabilized_video):
    try:
        subprocess.run(
            f"ffmpeg -y -i {input_video} -vf vidstabdetect=shakiness=10:accuracy=15 -f null -",
            shell=True,
            check=True,
        )
        subprocess.run(
            f"ffmpeg -y -i {input_video} -vf vidstabtransform=smoothing=30:input=transforms.trf "
            f"-c:v libx264 -pix_fmt yuv420p -r 30 {stabilized_video}",
            shell=True,
            check=True,
        )
        print(f"Stabilized video saved as '{stabilized_video}'")
    except Exception as e:
        print(f"Error stabilizing video '{input_video}': {e}")


# Function to add subtitles with merged audio to the video
def add_subtitles_with_audio(input_video, subtitle_file, audio_file, output_video):
    ffmpeg_command = (
        f"ffmpeg -y -i {input_video} -i {audio_file} "
        f'-vf "ass={subtitle_file}:fontsdir=fonts" '
        f"-c:v libx264 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k {output_video}"
    )
    try:
        subprocess.run(ffmpeg_command, shell=True, check=True)
        print(f"Video with subtitles and audio saved as '{output_video}'")
    except subprocess.CalledProcessError as e:
        print(f"Error adding subtitles to video '{input_video}': {e}")


# Function to add background music
def add_bg_music(final_video, bg_music_path, output_video):
    ffmpeg_command = (
        f"ffmpeg -i {final_video} -i {bg_music_path} "
        f'-filter_complex "[1:a]volume=0.8[a1];[0:a][a1]amix=inputs=2:duration=shortest" '
        f"-c:v copy -c:a aac -b:a 192k {output_video}"
    )
    try:
        subprocess.run(ffmpeg_command, shell=True, check=True)
        print(f"Video with background music saved as '{output_video}'")
    except Exception as e:
        print(f"Error adding background music: {e}")
