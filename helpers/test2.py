import os
import ffmpeg
from dotenv import load_dotenv
from openai import OpenAI
from moviepy.editor import (
    TextClip,
    CompositeVideoClip,
    VideoFileClip,
    ColorClip,
    AudioFileClip,
)
import subprocess


def setup_imagemagick():
    """Setup ImageMagick policy to allow text operations"""
    try:
        subprocess.run(["which", "convert"], check=True)
    except subprocess.CalledProcessError:
        print("ImageMagick not found. Installing...")
        subprocess.run(["sudo", "apt-get", "install", "-y", "imagemagick"])

    policy_file = "/etc/ImageMagick-6/policy.xml"
    if os.path.exists(policy_file):
        try:
            with open(policy_file, "r") as f:
                if "@" in f.read() and not "+@" in f.read():
                    print("Updating ImageMagick policy...")
                    subprocess.run(["sudo", "sed", "-i", "s/@/+@/g", policy_file])
        except Exception as e:
            print(f"Warning: Could not modify ImageMagick policy: {e}")
            print(
                "You may need to run: sudo sed -i 's/@/+@/g' /etc/ImageMagick-6/policy.xml"
            )


def create_video_from_image(image_path, output_path, duration=6):
    """Convert image to video using ffmpeg"""
    try:
        stream = ffmpeg.input(image_path, loop=1, t=duration)
        stream = ffmpeg.output(stream, output_path, vcodec="libx264", pix_fmt="yuv420p")
        ffmpeg.run(stream, overwrite_output=True)
        return output_path
    except ffmpeg.Error as e:
        print(f"Error creating video: {e.stderr}")
        return None


def generate_subtitles(audio_file_path, api_key):
    """Generate word-level timestamps using OpenAI Whisper"""
    client = OpenAI(api_key=api_key)
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
        return transcript
    except Exception as e:
        print(f"Error generating subtitles: {e}")
        return None


def group_words_into_sentences(words, max_words=3):
    """Group words into sentences based on timing and max words"""
    sentences = []
    current_sentence = []
    word_count = 0
    last_end_time = 0

    for word in words:
        # Start new sentence if max words reached or large time gap (> 0.7s)
        if word_count >= max_words or (
            word.start - last_end_time > 0.7 and word_count > 0
        ):
            if current_sentence:
                sentences.append(current_sentence)
                current_sentence = []
                word_count = 0

        current_sentence.append(word)
        word_count += 1
        last_end_time = word.end

    if current_sentence:  # Add remaining words
        sentences.append(current_sentence)

    return sentences


def create_word_clip(
    word_data,
    frame_size,
    position,
    font="Helvetica",
    color="white",
    stroke_color="black",
    stroke_width=1.5,
):
    """Create a single word clip"""
    try:
        text_clip = TextClip(
            word_data.word,
            font=font,
            fontsize=int(frame_size[1] * 0.035),
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method="label",
        )

        text_clip = text_clip.set_position(position)
        text_clip = text_clip.set_start(word_data.start).set_duration(
            word_data.end - word_data.start
        )

        return text_clip
    except Exception as e:
        print(f"Error creating word clip: {e}")
        return None


def create_sentence_clips(sentence_words, frame_size, font="Helvetica"):
    """Create clips for a sentence with word-level highlighting"""
    clips = []
    base_y = frame_size[1] * 0.8
    total_width = 0
    word_clips = []

    # First pass: create all word clips to calculate total width
    for word in sentence_words:
        clip = TextClip(
            word.word,
            font=font,
            fontsize=int(frame_size[1] * 0.035),
            color="white",
            stroke_color="black",
            stroke_width=1.5,
            method="label",
        )
        word_clips.append((word, clip))
        total_width += clip.w + 10  # Add 10px spacing

    # Calculate starting x position to center the sentence
    start_x = (frame_size[0] - total_width) / 2
    current_x = start_x

    # Second pass: create positioned clips with proper timing
    for word, clip in word_clips:
        # Create white (base) word
        white_clip = clip.set_position((current_x, base_y))
        white_clip = white_clip.set_start(sentence_words[0].start)
        white_clip = white_clip.set_duration(
            sentence_words[-1].end - sentence_words[0].start
        )
        clips.append(white_clip)

        # Create yellow (highlight) word - create new clip instead of changing color
        yellow_clip = TextClip(
            word.word,
            font=font,
            fontsize=int(frame_size[1] * 0.035),
            color="yellow",  # Create new clip with yellow color
            stroke_color="black",
            stroke_width=1.5,
            method="label",
        ).set_position((current_x, base_y))

        yellow_clip = yellow_clip.set_start(word.start)
        yellow_clip = yellow_clip.set_duration(word.end - word.start)
        clips.append(yellow_clip)

        current_x += clip.w + 10  # Add spacing between words

    # Add fade effects to the entire sentence
    clips = [clip.crossfadein(0.1).crossfadeout(0.1) for clip in clips]

    return clips

def create_final_video(video_path, audio_path, transcript, output_path):
    """Create final video with TikTok-style subtitles and audio"""
    try:
        # Load video and audio
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        frame_size = video.size

        # Add audio to video
        video = video.set_audio(audio)

        # Group words into sentences
        sentences = group_words_into_sentences(transcript.words)

        # Create clips for each sentence with word highlighting
        all_clips = []
        for sentence in sentences:
            sentence_clips = create_sentence_clips(sentence, frame_size)
            all_clips.extend(sentence_clips)

        # Create semi-transparent background for subtitles
        # subtitle_bg = ColorClip(
        #     size=(frame_size[0], int(frame_size[1] * 0.15)), color=(0, 0, 0)
        # ).set_opacity(0.6)
        # subtitle_bg = subtitle_bg.set_position((0, frame_size[1] * 0.75))
        # subtitle_bg = subtitle_bg.set_duration(video.duration)

        # Combine all clips
        final_video = CompositeVideoClip(
            # [video, subtitle_bg] + all_clips, size=frame_size
            [video] + all_clips, size=frame_size
        )

        # Write final video
        final_video.write_videofile(
            output_path, fps=24, codec="libx264", audio_codec="aac"
        )

        # Clean up
        video.close()
        audio.close()
        final_video.close()

        return output_path

    except Exception as e:
        print(f"Error creating final video: {e}")
        return None


def main():
    # Load environment variables
    load_dotenv()

    # Step 1: Initialize paths and setup
    image_path = "helpers/story_img_1.png"
    audio_path = "helpers/combined_story_audio.wav"
    temp_video_path = "helpers/temp_video.mp4"
    final_output_path = "helpers/final_video.mp4"

    # Step 2: Setup ImageMagick for text rendering
    setup_imagemagick()

    # Step 3: Create base video from image
    print("Creating video from image...")
    video_path = create_video_from_image(image_path, temp_video_path)
    if not video_path:
        return

    # Step 4: Generate subtitles from audio
    print("Generating subtitles from audio...")
    transcript = generate_subtitles(audio_path, os.getenv("OPENAI_API_KEY"))
    if not transcript:
        return

    # Step 5: Create final video with subtitles and audio
    print("Creating final video with subtitles...")
    final_video = create_final_video(
        video_path, audio_path, transcript, final_output_path
    )

    # Step 6: Clean up temporary files
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)

    if final_video:
        print(f"Successfully created video: {final_output_path}")


if __name__ == "__main__":
    main()
