from pydub import AudioSegment

def get_audio_duration(file_path: str) -> float:

    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000  # Convert milliseconds to seconds
    except Exception as e:
        raise ValueError(f"Error reading audio file: {e}")
