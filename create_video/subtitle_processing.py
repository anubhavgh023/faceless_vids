import os
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


# Function to modify subtitle style
def modify_subtitle_style(srt_file, output_ass_file):
    try:
        subs = pysubs2.load(srt_file, encoding="utf-8")
        for style in subs.styles.values():
            style.fontname = "DK Longreach"
            style.fontsize = 28
            style.bold = True
            style.primarycolor = pysubs2.Color(255, 255, 255)
            style.backcolor = pysubs2.Color(0, 0, 0, 255)
            style.outlinecolor = pysubs2.Color(0, 0, 0)
            style.outline = 2
            style.alignment = pysubs2.Alignment.MIDDLE_CENTER

        for event in subs.events:
            fade_in_ms = 100
            fade_out_ms = 100
            event.text = f"{{\\fad({fade_in_ms},{fade_out_ms})}}{event.text}"

        subs.save(output_ass_file)
        print(f"Modified subtitles saved as '{output_ass_file}'")
    except Exception as e:
        print(f"Error modifying subtitles: {e}")
