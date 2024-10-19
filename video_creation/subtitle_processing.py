import os
import random
import pysubs2


# Function to generate a subtitle file with correct .srt formatting
def generate_subtitle_file(words_with_timings, output_subtitle_file):
    try:
        with open(output_subtitle_file, "w") as f:
            for i, (word, start, end) in enumerate(words_with_timings):
                start_time = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02},{int((start % 1) * 1000):03}"
                end_time = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02},{int((end % 1) * 1000):03}"
                f.write(f"{i + 1}\n{start_time} --> {end_time}\n{word}\n\n")

        print(f"Subtitle file saved as '{output_subtitle_file}'")

    except Exception as e:
        print(f"Error generating subtitle file: {e}")

def modify_subtitle_style(srt_file, output_ass_file):
    try:
        # Load the subtitle file
        subs = pysubs2.load(srt_file, encoding="utf-8")

        # Modify the default subtitle style
        for style in subs.styles.values():
            style.fontname = "Open Sans"
            style.fontsize = 28
            style.bold = True
            style.primarycolor = pysubs2.Color(255, 255, 255)  # White
            style.backcolor = pysubs2.Color(0, 0, 0, 255)  # Black background
            style.outlinecolor = pysubs2.Color(0, 0, 0)  # Black outline
            style.outline = 2
            style.alignment = pysubs2.Alignment.MIDDLE_CENTER

        # Apply the color transitions
        for event in subs.events:
            words = event.text.split()

            if len(words) == 1:
                # Single word case, make it yellow for the full duration
                styled_text = f"{{\\c&H00FFFF&}}{words[0]}"
            elif len(words) == 2:
                # First word yellow for first 0.5 seconds, then turns white
                # Second word stays white initially, turns yellow after 0.5 seconds
                styled_text = (
                    f"{{\\c&H00FFFF&}}{words[0]}{{\\t(500,\\c&HFFFFFF&)}}"  # Word 1 changes to white after 0.5s
                    f" {{\\c&HFFFFFF&}}{{\\t(500,\\c&H00FFFF&)}}{words[1]}"  # Word 2 changes to yellow after 0.5s
                )

            # Update the event text with the styled text
            event.text = styled_text

        # Save the modified subtitle file
        subs.save(output_ass_file)
        print(f"Modified subtitles saved as '{output_ass_file}'")
    except Exception as e:
        print(f"Error modifying subtitles: {e}")

