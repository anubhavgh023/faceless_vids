import os
import subprocess


# Function to add subtitles with merged audio to the video
def add_subtitles_with_audio(input_video, subtitle_file, audio_file, output_video):
    ffmpeg_command = (
        f"ffmpeg -y "
        f"-i {input_video} "
        f"-stream_loop -1 -i {audio_file} "  # Loop audio if needed
        f'-vf "ass={subtitle_file}:fontsdir=fonts" '
        f"-c:v libx264 "
        f"-pix_fmt yuv420p "
        f"-r 30 "
        f"-c:a aac "
        f"-b:a 192k "
        f"-map 0:v:0 "  # Use video from first input
        f"-map 1:a:0 "  # Use audio from second input
        f"-shortest "  # Match duration to video length
        f"{output_video}"
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
        f'-filter_complex "[1:a]aloop=loop=-1:size=2e+09,volume=0.04[a1];'
        f'[0:a]volume=1.0[a0];[a0][a1]amix=inputs=2:duration=first" '
        f"-c:v copy -c:a aac -b:a 192k {output_video}"
    )
    
    try:
        subprocess.run(ffmpeg_command, shell=True, check=True)
        print(f"Video with background music saved as '{output_video}'")
    except Exception as e:
        print(f"Error adding background music: {e}")
