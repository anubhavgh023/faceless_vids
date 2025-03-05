import os
import ffmpeg
from dotenv import load_dotenv
from openai import OpenAI
from moviepy.editor import TextClip, CompositeVideoClip, VideoFileClip, ColorClip
import numpy as np
import subprocess


class VideoSubtitleGenerator:
    def __init__(self):
        # Load environment variables and initialize OpenAI client
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.setup_imagemagick()

    def setup_imagemagick(self):
        """Setup ImageMagick policy to allow text operations"""
        try:
            # Check if ImageMagick is installed
            subprocess.run(["which", "convert"], check=True)
        except subprocess.CalledProcessError:
            print("ImageMagick not found. Installing...")
            subprocess.run(["sudo", "apt-get", "install", "-y", "imagemagick"])

        # Modify ImageMagick policy to allow text operations
        policy_file = "/etc/ImageMagick-6/policy.xml"
        if os.path.exists(policy_file):
            try:
                with open(policy_file, "r") as f:
                    policy_content = f.read()

                if "@" in policy_content and not "+@" in policy_content:
                    print("Updating ImageMagick policy...")
                    subprocess.run(["sudo", "sed", "-i", "s/@/+@/g", policy_file])
            except Exception as e:
                print(f"Warning: Could not modify ImageMagick policy: {e}")
                print(
                    "You may need to run: sudo sed -i 's/@/+@/g' /etc/ImageMagick-6/policy.xml"
                )

    def create_video_from_image(self, image_path, output_path, duration=6):
        """Convert image to video using ffmpeg"""
        try:
            stream = ffmpeg.input(image_path, loop=1, t=duration)
            stream = ffmpeg.output(
                stream, output_path, vcodec="libx264", pix_fmt="yuv420p"
            )
            ffmpeg.run(stream, overwrite_output=True)
            return output_path
        except ffmpeg.Error as e:
            print(f"Error creating video: {e.stderr}")
            return None

    def generate_subtitles_from_audio(self, audio_file_path):
        """Generate word-level timestamps using OpenAI Whisper"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                )
            return transcript
        except Exception as e:
            print(f"Error generating subtitles: {e}")
            return None

    def create_caption_clip(
        self,
        word_data,
        frame_size,
        font="Helvetica",
        color="white",
        highlight_color="yellow",
        stroke_color="black",
        stroke_width=1.5,
    ):
        """Create caption clip for a single word"""
        try:
            word_clip = TextClip(
                word_data.word,
                font=font,
                fontsize=int(frame_size[1] * 0.025),  # 7.5% of video height
                color=color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method="label",  # Try using 'label' method instead of default
            )

            duration = word_data.end - word_data.start
            word_clip = word_clip.set_start(word_data.start).set_duration(duration)

            # Create highlight clip
            highlight_clip = TextClip(
                word_data.word,
                font=font,
                fontsize=int(frame_size[1] * 0.025),
                color=highlight_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method="label",
            )
            highlight_clip = highlight_clip.set_start(word_data.start).set_duration(
                duration
            )

            return word_clip, highlight_clip
        except Exception as e:
            print(f"Error creating caption clip: {e}")
            # Try fallback method
            return self.create_caption_clip_fallback(
                word_data, frame_size, font, color, highlight_color
            )

    def create_caption_clip_fallback(
        self, word_data, frame_size, font, color, highlight_color
    ):
        """Fallback method for creating caption clips without stroke effects"""
        word_clip = TextClip(
            word_data.word,
            font=font,
            fontsize=int(frame_size[1] * 0.045),
            color=color,
            method="caption",  # Try alternative method
        )

        duration = word_data.end - word_data.start
        word_clip = word_clip.set_start(word_data.start).set_duration(duration)

        highlight_clip = TextClip(
            word_data.word,
            font=font,
            fontsize=int(frame_size[1] * 0.045),
            color=highlight_color,
            method="caption",
        )
        highlight_clip = highlight_clip.set_start(word_data.start).set_duration(
            duration
        )

        return word_clip, highlight_clip

    def create_final_video(self, video_path, transcript, output_path):
        """Create final video with scrolling subtitles"""
        try:
            video = VideoFileClip(video_path)
            frame_size = video.size

            # Create clips for each word
            word_clips = []
            x_pos = frame_size[0] * 0.1  # 10% margin from left
            y_pos = frame_size[1] * 0.8  # 80% down from top

            for word in transcript.words:
                try:
                    base_clip, highlight_clip = self.create_caption_clip(
                        word, frame_size
                    )

                    # Position clips
                    base_clip = base_clip.set_position((x_pos, y_pos))
                    highlight_clip = highlight_clip.set_position((x_pos, y_pos))

                    word_clips.extend([base_clip, highlight_clip])

                    # Update x position for next word
                    x_pos += base_clip.w + 10  # Add 10px spacing between words
                except Exception as e:
                    print(f"Warning: Skipping word '{word.word}' due to error: {e}")
                    continue

            # Create background for subtitles
            subtitle_bg = ColorClip(
                size=(frame_size[0], int(frame_size[1] * 0.3)), color=(0, 0, 0)
            ).set_opacity(0.6)
            subtitle_bg = subtitle_bg.set_position((0, frame_size[1] * 0.7))
            subtitle_bg = subtitle_bg.set_duration(video.duration)

            # Combine all clips
            final_video = CompositeVideoClip(
                [video, subtitle_bg] + word_clips, size=frame_size
            )

            # Write final video
            final_video.write_videofile(
                output_path, fps=24, codec="libx264", audio_codec="aac"
            )

            # Clean up
            video.close()
            final_video.close()

            return output_path

        except Exception as e:
            print(f"Error creating final video: {e}")
            return None


def main():
    # Initialize the generator
    generator = VideoSubtitleGenerator()

    # Paths
    image_path = "helpers/story_img_1.png"
    audio_path = "helpers/combined_story_audio.wav"
    temp_video_path = "helpers/temp_video.mp4"
    final_output_path = "helpers/final_video.mp4"

    # Create video from image
    print("Creating video from image...")
    video_path = generator.create_video_from_image(image_path, temp_video_path)
    if not video_path:
        return

    # Generate subtitles from audio
    print("Generating subtitles from audio...")
    transcript = generator.generate_subtitles_from_audio(audio_path)
    if not transcript:
        return

    # Create final video with subtitles
    print("Creating final video with subtitles...")
    final_video = generator.create_final_video(
        video_path, transcript, final_output_path
    )
    if final_video:
        print(f"Successfully created video: {final_output_path}")

    # Clean up temporary files
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)


if __name__ == "__main__":
    main()
