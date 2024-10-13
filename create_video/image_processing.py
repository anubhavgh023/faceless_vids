import os
import subprocess


# Function to generate video from image
def make_video_from_image(image: str, output_video: str, aspect_ratio: str):
    try:
        video_duration = 8
        ffmpeg_command = (
            f"ffmpeg -y -loop 1 -i {image} "
            f"-filter_complex \"zoompan=z='if(lte(mod(it*25,42),10),min(max(zoom,pzoom)+0.005,1.5),max(min(max(zoom,pzoom)-0.002,1.8),1))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=2,scale={aspect_ratio}\" "
            f"-t {video_duration} -c:v libx264 -pix_fmt yuv420p -r 15 {output_video}"
        )  # changed framerate

        subprocess.run(ffmpeg_command, shell=True, check=True)
        print(f"Video from image saved as '{output_video}'")
    except Exception as e:
        print(f"Error generating video from image '{image}': {e}")
