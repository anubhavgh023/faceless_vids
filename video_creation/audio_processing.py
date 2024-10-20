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

# This function generates timings for pairs of words
def generate_word_timings(captions):
    words_with_timings = []
    current_time = 0.0
    for caption in captions:
        words = caption.split()
        i = 0
        while i < len(words):
            # Pair words in twos, or single if it's the last word
            if i + 1 < len(words):
                word_pair = f"{words[i]} {words[i + 1]}"
            else:
                word_pair = words[i]
            
            start_time = current_time
            end_time = current_time + 0.8  # Assume each pair takes 1 second
            words_with_timings.append((word_pair, start_time, end_time))
            current_time += 0.8  # Move time forward by 1 second
            i += 2  # Skip two words each iteration
    return words_with_timings
