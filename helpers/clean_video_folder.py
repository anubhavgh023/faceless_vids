import os
import glob
import logging

logger = logging.getLogger()

def clean_video_folder():
    video_folder = "video_creation/assets/videos/"
    # Find all .mp4 files directly in the videos/ folder (not in subfolders)
    mp4_files = glob.glob(os.path.join(video_folder, "*.mp4"))

    # Delete the files
    for file_path in mp4_files:
        try:
            os.remove(file_path)
            logger.info(f"Deleted: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")
