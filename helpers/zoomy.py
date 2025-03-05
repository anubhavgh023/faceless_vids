import subprocess

from video_creation.create_video import generate_subtitles_from_audio,generate_subtitle_file
from modules.gen_audio import generate_audio

# Example usage
input_image = "story_img_1.png"
output_video = "output_video.mp4"

transcript = generate_subtitles_from_audio()
# print(transcript.words)
print(transcript)

