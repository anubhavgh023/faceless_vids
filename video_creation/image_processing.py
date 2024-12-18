import os
import subprocess
import random
import shlex
import logging

VALID_VIDEO_ASPECT_RATIOS = {
    "9:16": {"width": 720, "height": 1280},  # Portrait
    "16:9": {"width": 1280, "height": 720},  # Landscape
    "1:1": {"width": 720, "height": 720},  # Square
}

logger = logging.getLogger()


# new
def make_video_from_image(image: str, i: int, output_video: str, aspect_ratio):
    """Generate a video from an image with optional shaky effect applied alternately."""
    # Validate input image exists
    if not os.path.exists(image):
        logger.error(f"Image file not found: {image}")
        return False

    # Validate output path
    output_dir = os.path.dirname(output_video)
    os.makedirs(output_dir, exist_ok=True)

    # Use predefined aspect ratios
    width = VALID_VIDEO_ASPECT_RATIOS[aspect_ratio]["width"]
    height = VALID_VIDEO_ASPECT_RATIOS[aspect_ratio]["height"]

    try:
        video_duration = 7  # 7 seconds each video
        zoom_speed = 0.003  # Slow zoom speed
        max_zoom = 1.5
        zoom_area_list = ["top-left", "top-right", "bottom-right"]
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

        # Apply alternate shaky effect
        if i % 2 == 0:
            filter_complex = (
                f"rotate='cos(t*4)*PI/100 + cos(t*3)*PI/100':c=black,"
                f"scale={width}:{height},crop={width}:{height}:0:0,"
                f"pad={width}:{height}:(ow-iw)/3:(oh-ih)/3"
            )
        else:
            filter_complex = (
                f"zoompan=z='min(max(zoom,pzoom)+{zoom_speed},{max_zoom})':d={video_duration*25}:"
                f"x='{x}':y='{y}':s={width}x{height}:fps=25,"
                f"scale={width}:{height}"
            )

        # FFmpeg command
        ffmpeg_command = (
            f"ffmpeg -loglevel verbose -y -loop 1 -i {shlex.quote(image)} "
            f'-vf "{filter_complex},format=yuv420p" '
            f"-t {video_duration} "
            f"-color_range pc -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
            f"-c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p -r 30 {shlex.quote(output_video)}"
        )

        # Execute the FFmpeg command
        result = subprocess.run(
            ffmpeg_command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
        )

        # Check subprocess result
        if result.returncode != 0:
            logger.error(f"FFmpeg error converting {image}:")
            logger.error(result.stderr)
            return False

        if not os.path.exists(output_video):
            logger.error(f"Video was not created for {image}")
            return False

        logger.info(f"Video from image saved as '{output_video}'")
        return True

    except Exception as e:
        logger.error(f"Error generating video from image '{image}': {e}")
        return False


# no shakky effect, COLOR PIXEL
# def make_video_from_image(image: str, i: int, output_video: str, aspect_ratio):
#     # Validate input image exists
#     if not os.path.exists(image):
#         logger.error(f"Image file not found: {image}")
#         return False

#     # Validate output path
#     output_dir = os.path.dirname(output_video)
#     os.makedirs(output_dir, exist_ok=True)

#     # Use predefined aspect ratios
#     width = VALID_VIDEO_ASPECT_RATIOS[aspect_ratio]["width"]
#     height = VALID_VIDEO_ASPECT_RATIOS[aspect_ratio]["height"]

#     try:
#         video_duration = 7  # 7 seconds each video
#         zoom_speed = 0.003  # Slow zoom speed
#         max_zoom = 1.5
#         zoom_area_list = [
#             "top-left",
#             "top-right",
#             "bottom-right",
#         ]
#         zoom_area = random.choice(zoom_area_list)

#         # Determine the x, y coordinates for the zoom area
#         if zoom_area == "center":
#             x = "iw/2-(iw/zoom/2)"
#             y = "ih/2-(ih/zoom/2)"
#         elif zoom_area == "top-left":
#             x = "0"
#             y = "0"
#         elif zoom_area == "top-right":
#             x = "iw-(iw/zoom)"
#             y = "0"
#         elif zoom_area == "bottom-right":
#             x = "iw-(iw/zoom)"
#             y = "ih-(ih/zoom)"
#         else:
#             raise ValueError("Invalid zoom area specified")

#         # Adjust FFmpeg command to handle color range and pixel format explicitly
#         ffmpeg_command = (
#             f"ffmpeg -loglevel verbose -y -loop 1 -i {shlex.quote(image)} "
#             f"-vf \"zoompan=z='min(max(zoom,pzoom)+{zoom_speed},{max_zoom})':d={video_duration*25}:"
#             f"x='{x}':y='{y}':s={width}x{height}:fps=25,"
#             f"scale={width}:{height},"
#             f'format=yuv420p" '
#             f"-t {video_duration} "
#             f"-color_range pc "  # Explicitly set color range to full range
#             f"-color_primaries bt709 "  # Specify color primaries
#             f"-color_trc bt709 "  # Specify transfer characteristics
#             f"-colorspace bt709 "  # Specify colorspace
#             f"-c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p -r 30 {shlex.quote(output_video)}"
#         )

#         # Use subprocess with better error checking
#         result = subprocess.run(
#             ffmpeg_command, 
#             shell=True, 
#             check=False,  # Don't raise exception on non-zero exit
#             capture_output=True,  # Capture stdout and stderr
#             text=True
#         )

#         # Check subprocess result
#         if result.returncode != 0:
#             logger.error(f"FFmpeg error converting {image}:")
#             logger.error(result.stderr)
#             return False

#         if not os.path.exists(output_video):
#             logger.error(f"Video was not created for {image}")
#             return False

#         logger.info(f"Video from image saved as '{output_video}'")
#         return True

#     except Exception as e:
#         logger.error(f"Error generating video from image '{image}': {e}")
#         return False

# # ORIGINAL
# def make_video_from_image(image: str, i: int, output_video: str, aspect_ratio):
#     # default width & height
#     width = 720
#     height = 1280

#     # set video height & width
#     width = VALID_VIDEO_ASPECT_RATIOS[aspect_ratio]["width"]
#     height = VALID_VIDEO_ASPECT_RATIOS[aspect_ratio]["height"]

#     try:
#         video_duration = 7  # 7 seconds each video
#         zoom_speed = 0.003  # Slow zoom speed
#         max_zoom = 1.5
#         zoom_area_list = [
#             "top-left",
#             "top-right",
#             "bottom-right",
#         ]  # center is producing shakky vids
#         zoom_area = random.choice(zoom_area_list)

#         # Determine the x, y coordinates for the zoom area
#         if zoom_area == "center":
#             x = "iw/2-(iw/zoom/2)"
#             y = "ih/2-(ih/zoom/2)"
#         elif zoom_area == "top-left":
#             x = "0"
#             y = "0"
#         elif zoom_area == "top-right":
#             x = "iw-(iw/zoom)"
#             y = "0"
#         elif zoom_area == "bottom-right":
#             x = "iw-(iw/zoom)"
#             y = "ih-(ih/zoom)"
#         else:
#             raise ValueError("Invalid zoom area specified")

#         # Even: Zoom in
#         zoom_filter = (
#             f"zoompan=z='min(max(zoom,pzoom)+{zoom_speed},{max_zoom})':d={video_duration*25}:"
#             f"x='{x}':y='{y}':s=576x1024:fps=25"
#         )
#         # Define the rotation effect filter

#         # cropping too much
#         # rotation_filter = (
#         #     "[0:v]rotate='(cos(t*6)*PI/40 + cos(t*5)*PI/70)*abs(cos(t*0.3))':c=black,"
#         #     f"scale={width}:{height},crop=576:1024:112:256,pad=576:1024:(ow-iw)/2:(oh-ih)/2"
#         # )

#         rotation_filter = (
#             "[0:v]rotate='(cos(t*8)*PI/100 + cos(t*6)*PI/100)*abs(cos(t*0.3))':c=black,"
#             f"scale={width}:{height},crop=684:1216:18:32"
#         )

#         # Randomly choose between zoom effect or rotation effect
#         chosen_filter = zoom_filter if random.choice([True, False]) else rotation_filter

#         # Final Command
#         ffmpeg_command = (
#             f"ffmpeg -y -loop 1 -i {image} "
#             f'-vf "{chosen_filter},scale="{width}:{height}",format=yuv420p" '
#             f"-t {video_duration} -c:v libx264 -crf 24 -pix_fmt yuv420p -r 30 {output_video}"
#         )

#         subprocess.run(ffmpeg_command, shell=True, check=True)

#         logger.info(f"Video from image saved as '{output_video}'")
#     except Exception as e:
#         logger.error(f"Error generating video from image '{image}': {e}")


# shakky move not working
# def merge_videos(videos, output_file):
#     try:
#         # Prepare input files for ffmpeg command
#         input_files = " ".join([f"-i {video}" for video in videos])

#         # Unique transition options
#         transitions = ["fadeblack", "fadegrays", "pixelize"]

#         # Prepare filter complex string
#         filter_complex = ""
#         duration = 7  # Duration of each video
#         transition_duration = 0.5  # Duration of each transition
#         for i in range(len(videos) - 1):
#             transition = random.choice(transitions)

#             # Set the correct offset, taking transition duration into account
#             offset = duration * (i + 1) - (transition_duration * i)

#             if i == 0:
#                 filter_complex += f"[0:v][1:v]xfade=transition={transition}:duration={transition_duration}:offset={offset},format=yuv420p[v01]; "
#             else:
#                 filter_complex += f"[v0{i}][{i+1}:v]xfade=transition={transition}:duration={transition_duration}:offset={offset},format=yuv420p[v0{i+1}]; "

#         # Remove the trailing semicolon and space
#         filter_complex = filter_complex.rstrip("; ")

#         # Construct the full ffmpeg command
#         ffmpeg_command = (
#             f"ffmpeg {input_files} "
#             f'-filter_complex "{filter_complex}" '
#             f'-map "[v0{len(videos)-1}]" -c:v libx264 -crf 24 {output_file}'
#         )

#         # Execute the ffmpeg command
#         subprocess.run(shlex.split(ffmpeg_command), check=True)

#         logger.info(f"Final video saved as '{output_file}'")
#     except subprocess.CalledProcessError as e:
#         logger.error(f"Error concatenating videos: {e}")
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")


# # working
# # time isssue
# def merge_videos(videos, output_file):
#     try:
#         # Prepare input files for ffmpeg command
#         input_files = " ".join([f"-i {video}" for video in videos])

#         # Unique transition options
#         # transitions = ["fadeblack", "fadegrays", "fade"]
#         transitions = ["fadeblack", "fadegrays", "pixelize"]

#         # Prepare filter complex string
#         filter_complex = ""
#         for i in range(len(videos) - 1):
#             transition = random.choice(transitions)
#             prev_transition = transition

#             if i == 0:
#                 filter_complex += f"[0:v][1:v]xfade=transition={transition}:duration=0.5:offset=4,format=yuv420p[v01]; "
#             else:
#                 filter_complex += f"[v0{i}][{i+1}:v]xfade=transition={transition}:duration=0.5:offset={4*(i+1)},format=yuv420p[v0{i+1}]; "

#         # Remove the trailing semicolon and space
#         filter_complex = filter_complex.rstrip("; ")

#         # Construct the full ffmpeg command
#         ffmpeg_command = (
#             f"ffmpeg {input_files} "
#             f'-filter_complex "{filter_complex}" '
#             f'-map "[v0{len(videos)-1}]" -c:v libx264 -crf 18 {output_file}'
#         )

#         # Execute the ffmpeg command
#         subprocess.run(shlex.split(ffmpeg_command), check=True)

#         logger.info(f"Final video saved as '{output_file}'")
#     except subprocess.CalledProcessError as e:
#         logger.error(f"Error concatenating videos: {e}")
#         logger.error(f"FFmpeg output: {e.output}")
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")


# transistion effect issue
# def merge_videos(videos, output_file):
#     try:
#         # Prepare input files for ffmpeg command
#         input_files = " ".join([f"-i {video}" for video in videos])
#         # Unique transition options
#         transitions = ["fadeblack", "fadegrays", "pixelize"]

#         # Calculate the total desired duration and individual segment duration
#         total_desired_duration = len(videos) * 7  # 7 seconds per video
#         transition_duration = 0.5

#         # Prepare filter complex string
#         filter_complex = ""
#         for i in range(len(videos) - 1):
#             transition = random.choice(transitions)

#             if i == 0:
#                 # First transition
#                 filter_complex += f"[0:v][1:v]xfade=transition={transition}:duration={transition_duration}:offset={7 - transition_duration/2},format=yuv420p[v01]; "
#             else:
#                 # Subsequent transitions
#                 offset = (i + 1) * 7 - transition_duration/2
#                 filter_complex += f"[v0{i}][{i+1}:v]xfade=transition={transition}:duration={transition_duration}:offset={offset},format=yuv420p[v0{i+1}]; "

#         # Remove the trailing semicolon and space
#         filter_complex = filter_complex.rstrip("; ")

#         # Construct the full ffmpeg command
#         ffmpeg_command = (
#             f"ffmpeg {input_files} "
#             f'-filter_complex "{filter_complex}" '
#             f'-map "[v0{len(videos)-1}]" -c:v libx264 -crf 24 {output_file}'
#         )

#         # Execute the ffmpeg command
#         subprocess.run(shlex.split(ffmpeg_command), check=True)
#         logger.info(f"Final video saved as '{output_file}'")

#     except subprocess.CalledProcessError as e:
#         logger.error(f"Error concatenating videos: {e}")
#         logger.error(f"FFmpeg output: {e.output}")
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")


# currently using
def merge_videos(videos, output_file):
    try:
        # Prepare input files for ffmpeg command
        input_files = " ".join([f"-i {video}" for video in videos])

        # Unique transition options
        transitions = ["fadeblack", "fadegrays", "pixelize"]
        transition_duration = 0.5  # Duration of each transition (in seconds)
        video_duration = 7  # Duration of each video (in seconds)

        # Prepare filter complex string
        filter_complex = ""
        current_offset = 0  # Tracks the current timestamp for transitions

        for i in range(len(videos) - 1):
            transition = random.choice(transitions)

            # Add transition between videos
            if i == 0:
                # First transition
                filter_complex += f"[0:v][1:v]xfade=transition={transition}:duration={transition_duration}:offset={video_duration - transition_duration},format=yuv420p[v01]; "
                current_offset = video_duration - transition_duration
            else:
                # Subsequent transitions
                current_offset += video_duration - transition_duration
                filter_complex += f"[v0{i}][{i+1}:v]xfade=transition={transition}:duration={transition_duration}:offset={current_offset},format=yuv420p[v0{i+1}]; "

        # Remove the trailing semicolon and space
        filter_complex = filter_complex.rstrip("; ")

        # Construct the full ffmpeg command
        ffmpeg_command = (
            f"ffmpeg {input_files} "
            f'-filter_complex "{filter_complex}" '
            f'-map "[v0{len(videos)-1}]" -c:v libx264 -crf 22 {output_file}'
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
            f"-threads {min(12, os.cpu_count())} "
            f"-frame-parallel 1 -pix_fmt yuv420p "
            f"-t {output_video_duration} {output_video}"
        )

        # Execute the ffmpeg command
        subprocess.run(shlex.split(ffmpeg_command), check=True)

        logger.info(f"Video with particle effect saved as '{output_video}'")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error adding particle effect: {e}")
        logger.error(f"FFmpeg output: {e.output}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
