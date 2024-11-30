import os
import subprocess
import random
import shlex
import logging

VALID_VIDEO_ASPECT_RATIOS = {
    "9:16": {"width": 720, "height": 1280},  # Portrait
    "16:9": {"width": 1280, "height": 720},  # Landscape
    "1:1": {"width": 720, "height": 720},    # Square
}

logger = logging.getLogger()

def make_video_from_image(image: str, i: int, output_video: str, aspect_ratio):
    #default width & height 
    width = 720
    height = 1280
    
    # set video height & width
    width = VALID_VIDEO_ASPECT_RATIOS[aspect_ratio]['width']
    height = VALID_VIDEO_ASPECT_RATIOS[aspect_ratio]['height']
    
    try:
        video_duration = 6  # 6 seconds each video
        zoom_speed = 0.003  # Slow zoom speed
        max_zoom = 1.5
        zoom_area_list = [
            "top-left",
            "top-right",
            "bottom-right",
        ]  # center is producing shakky vids
        zoom_area = random.choice(zoom_area_list)

        # Determine the x, y coordinates for the zoom area
        if zoom_area == "center":
            x = "iw/2-(iw/zoom/2)"
            y = "ih/2-(ih/zoom/2)"
        elif zoom_area == "top-left":
            x = "0"
            y = "0"
        elif zoom_area == "top-right":
            x = "iw-(iw/zoom)"
            y = "0"
        elif zoom_area == "bottom-right":
            x = "iw-(iw/zoom)"
            y = "ih-(ih/zoom)"
        else:
            raise ValueError("Invalid zoom area specified")

        # Even: Zoom in
        zoom_filter = (
            f"zoompan=z='min(max(zoom,pzoom)+{zoom_speed},{max_zoom})':d={video_duration*25}:"
            f"x='{x}':y='{y}':s=576x1024:fps=25"
        )
        # -- working --
        # ffmpeg_command = (
        #     f"ffmpeg -y -loop 1 -i {image} "
        #     f'-vf "{zoom_filter},scale={aspect_ratio},format=yuv420p" '
        #     f"-t {video_duration} -c:v libx264 -pix_fmt yuv420p -r 30 {output_video}"
        # )
        ffmpeg_command = (
            f"ffmpeg -y -loop 1 -i {image} "
            f'-vf "{zoom_filter},scale="{width}:{height}",format=yuv420p" '
            f"-t {video_duration} -c:v libx264 -crf 24 -pix_fmt yuv420p -r 30 {output_video}"
        )

        subprocess.run(ffmpeg_command, shell=True, check=True)

        logger.info(f"Video from image saved as '{output_video}'")
    except Exception as e:
        logger.error(f"Error generating video from image '{image}': {e}")

# working
def merge_videos(videos, output_file):
    try:
        # Prepare input files for ffmpeg command
        input_files = " ".join([f"-i {video}" for video in videos])

        # Unique transition options
        transitions = ["fadeblack", "fadegrays", "fade"]

        # Prepare filter complex string
        filter_complex = ""
        for i in range(len(videos) - 1):
            transition = random.choice(transitions)
            prev_transition = transition

            if i == 0:
                filter_complex += f"[0:v][1:v]xfade=transition={transition}:duration=0.5:offset=4,format=yuv420p[v01]; "
            else:
                filter_complex += f"[v0{i}][{i+1}:v]xfade=transition={transition}:duration=0.5:offset={4*(i+1)},format=yuv420p[v0{i+1}]; "

        # Remove the trailing semicolon and space
        filter_complex = filter_complex.rstrip("; ")

        # Construct the full ffmpeg command
        ffmpeg_command = (
            f"ffmpeg {input_files} "
            f'-filter_complex "{filter_complex}" '
            f'-map "[v0{len(videos)-1}]" -c:v libx264 -crf 24 {output_file}'
        )

        # Execute the ffmpeg command
        subprocess.run(shlex.split(ffmpeg_command), check=True)

        logger.info(f"Final video saved as '{output_file}'")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error concatenating videos: {e}")
        logger.error(f"FFmpeg output: {e.output}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def add_particle_effect(
    input_video,
    output_video_duration,
    particle_video,
    output_video,
    colorkey_color="0x000000",
    colorkey_similarity=0.3,
    colorkey_blend=0.3,
    overlay_x=0,
    overlay_y=0,
):
    try:   
        # Construct the colorkey filter
        colorkey_filter = (
            f"colorkey={colorkey_color}:{colorkey_similarity}:{colorkey_blend}"
        )

        # Construct the overlay filter
        overlay_filter = f"overlay={overlay_x}:{overlay_y}"

        # Use the 2-second particle video, loop it to match the input video duration
        filter_complex = (
            f"[1:v]loop=-1:size={output_video_duration*24},"  # Loop to match input video duration
            f"{colorkey_filter}[particle]; "
            f"[0:v][particle]{overlay_filter}[out]"
        )

        # Construct the full ffmpeg command with optimizations
        # improved: 45 sec -> 30 sec
        ffmpeg_command = (
            f"ffmpeg -i {input_video} -i {particle_video} "
            f'-filter_complex "{filter_complex}" '
            f'-map "[out]" -r 30 -c:v libx264 -crf 24 -preset ultrafast '
            f'-threads {min(12, os.cpu_count())} '
            f'-frame-parallel 1 -pix_fmt yuv420p '
            f'-t {output_video_duration} {output_video}'
        )

        # Execute the ffmpeg command
        subprocess.run(shlex.split(ffmpeg_command), check=True)

        logger.info(f"Video with particle effect saved as '{output_video}'")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error adding particle effect: {e}")
        logger.error(f"FFmpeg output: {e.output}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
