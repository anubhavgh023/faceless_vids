import subprocess


def create_video(input_image, output_video):
    """Create a video from a single image with random shake effect."""

    ffmpeg_command = [
        "ffmpeg",
        "-y",  # Overwrite output if exists
        "-loop",
        "1",  # Loop the image
        "-t",
        "5",  # Video duration
        "-framerate",
        "30",  # Set framerate
        "-i",
        input_image,  # Input image path
        "-filter_complex",
        "[0:v]rotate='cos(t*6)*PI/50 + cos(t*4)*PI/80':c=black,scale=800:1424, crop=576:1024:112:256,pad=576:1024:(ow-iw)/3:(oh-ih)/3",  # Apply effect
        "-c:v",
        "libx264",  # Use libx264 codec
        "-pix_fmt",
        "yuv420p",  # Pixel format
        "-r",
        "30",  # Output framerate
        output_video,  # Output file path
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Video saved as {output_video}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating video: {e}")


# Example usage
input_image = "story_img_1.png"
output_video = "output_video.mp4"
create_video(input_image, output_video)
