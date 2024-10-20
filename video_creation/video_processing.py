import os
import subprocess

# Function to add subtitles with merged audio to the video
def add_subtitles_with_audio(input_video, subtitle_file, audio_file, output_video):
    # -- working --
    # ffmpeg_command = (
    #     f"ffmpeg -y -i {input_video} -i {audio_file} "
    #     f'-vf "ass={subtitle_file}:fontsdir=fonts" '
    #     f"-c:v libx264 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k "
    #     f"-shortest -t 46 {output_video}"  # Trim the video to match audio duration
    # )
    #--

    # testing
    ffmpeg_command = (
        f"ffmpeg -y -i {input_video} -i {audio_file} "
        f'-vf "ass={subtitle_file}:fontsdir=fonts" '
        f"-c:v libx264 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k "
        f"-preset veryfast -movflags +faststart {output_video}"
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
    f'-filter_complex "[0:a]volume=1.0[a0];[1:a]volume=0.02[a1];[a0][a1]amix=inputs=2:duration=shortest" '
    f"-c:v copy -c:a aac -b:a 192k {output_video}"
)
    try:
        subprocess.run(ffmpeg_command, shell=True, check=True)
        print(f"Video with background music saved as '{output_video}'")
    except Exception as e:
        print(f"Error adding background music: {e}")