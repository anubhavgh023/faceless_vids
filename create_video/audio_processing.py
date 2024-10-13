import subprocess
import os


# Function to merge audios
def merge_audios(input_audios, output_audio):
    try:
        with open("audios_list.txt", "w") as file:
            for audio in input_audios:
                file.write(f"file '{audio}'\n")

        subprocess.run(
            f"ffmpeg -y -f concat -safe 0 -i audios_list.txt -c copy {output_audio}",
            shell=True,
            check=True,
        )
        os.remove("audios_list.txt")
        print(f"Merged audio saved as '{output_audio}'")
    except Exception as e:
        print(f"Error merging audios: {e}")


# Function to generate word-by-word timings (for demonstration purposes)
def generate_word_timings(captions):
    # This function simulates word timings
    words_with_timings = []
    current_time = 0.0
    for caption in captions:
        words = caption.split()
        for word in words:
            start_time = current_time
            end_time = current_time + 0.4  # Assume each word takes 0.4 second
            words_with_timings.append((word, start_time, end_time))
            current_time += 0.4
    return words_with_timings
