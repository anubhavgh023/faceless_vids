import os
import subprocess
import random
import shlex


def make_video_from_image(image: str, i: int, output_video: str, aspect_ratio: str):
    try:
        video_duration = 6 # 6 seconds each video
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
        ffmpeg_command = (
            f"ffmpeg -y -loop 1 -i {image} "
            f'-vf "{zoom_filter},scale={aspect_ratio},format=yuv420p" '
            f"-t {video_duration} -c:v libx264 -pix_fmt yuv420p -r 30 {output_video}"
        )

        subprocess.run(ffmpeg_command, shell=True, check=True)

        print(f"Video from image saved as '{output_video}'")
    except Exception as e:
        print(f"Error generating video from image '{image}': {e}")


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
                filter_complex += f"[0:v][1:v]xfade=transition={transition}:duration=1:offset=4,format=yuv420p[v01]; "
            else:
                filter_complex += f"[v0{i}][{i+1}:v]xfade=transition={transition}:duration=1:offset={4*(i+1)},format=yuv420p[v0{i+1}]; "

        # Remove the trailing semicolon and space
        filter_complex = filter_complex.rstrip('; ')

        # Construct the full ffmpeg command
        ffmpeg_command = (
            f"ffmpeg {input_files} "
            f'-filter_complex "{filter_complex}" '
            f'-map "[v0{len(videos)-1}]" -c:v libx264 -crf 23 {output_file}'
        )

        # Print the command for debugging
        print(f"FFmpeg command: {ffmpeg_command}")

        # Execute the ffmpeg command
        subprocess.run(shlex.split(ffmpeg_command), check=True)

        print(f"Final video saved as '{output_file}'")
    except subprocess.CalledProcessError as e:
        print(f"Error concatenating videos: {e}")
        print(f"FFmpeg output: {e.output}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        

def add_particle_effect(input_video,input_video_duration, particle_video, output_video, 
                        colorkey_color="0x000000", colorkey_similarity=0.3, 
                        colorkey_blend=0.3, overlay_x=0, overlay_y=0):
    try:
        # input video duration
        input_duration = input_video_duration
        
        # Construct the colorkey filter
        colorkey_filter = f"colorkey={colorkey_color}:{colorkey_similarity}:{colorkey_blend}"
        
        # Construct the overlay filter
        overlay_filter = f"overlay={overlay_x}:{overlay_y}"
        
        # Construct the full filter complex with trim and loop for particle video
        filter_complex = (
            f"[1:v]trim=duration={input_duration},loop=-1:size={input_duration*25},"
            f"{colorkey_filter}[particle]; "
            f"[0:v][particle]{overlay_filter}[out]"
        )
        
        # Construct the full ffmpeg command
        ffmpeg_command = (
            f"ffmpeg -i {input_video} -i {particle_video} "
            f'-filter_complex "{filter_complex}" '
            f'-map "[out]" -c:v libx264 -crf 23 -pix_fmt yuv420p '
            f'-t {input_duration} {output_video}'
        )

        # Print the command for debugging
        print(f"FFmpeg command: {ffmpeg_command}")

        # Execute the ffmpeg command
        subprocess.run(shlex.split(ffmpeg_command), check=True)

        print(f"Video with particle effect saved as '{output_video}'")
    except subprocess.CalledProcessError as e:
        print(f"Error adding particle effect: {e}")
        print(f"FFmpeg output: {e.output}")
    except Exception as e:
        print(f"Unexpected error: {e}")



# Testing

# ## TODO: pass the no. of prompts from main.py here
# # # -- img to vid working ---
# images = [f"assets/images/story_img_{i+1}.png" for i in range(10)]  # give the length of prompts
# videos = []

# for i, image in enumerate(images):
#     output_video = f"assets/videos/output_video_{i+1}.mp4"
#     make_video_from_image(image, i, output_video, "576:1024")
#     videos.append(output_video)
# # #----


# # # -- concat videos with transition -- 
# merge_video_file = "assets/videos/merged_video_output.mp4"
# merge_videos(videos, output_video)
# # #---

# # this is the final output video
# particle_final_output_file = "assets/videos/final_output.mp4"

# pstyle = "rising_embers"
# particle_video = f"assets/videos/particle_system/{pstyle}.mp4"

# # adding particle system
# add_particle_effect(input_video=merge_video_file, particle_video=particle_video, output_video=particle_final_output_file)

# # # Clean up intermediate video files
# for video in video_files:
#     os.remove(video)