# File: config/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    """
    Configure centralized logging for the application.

    - Logs to a file in the logs directory
    - Uses RotatingFileHandler to manage log file size
    - Sets up logging format with timestamp, log level, and message
    """
    # Ensure logs directory exists
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Full path to the log file
    log_file = os.path.join(logs_dir, "application.log")

    # Configure the root logger
    logging.basicConfig(
        level=logging.WARN,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # File handler with log rotation
            RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,  # Keep 5 backup files
            ),
            # Optional: Console handler for development
            logging.StreamHandler(),
        ],
    )


# Optional: Create a function to get a logger for specific modules
def get_logger(name):
    """
    Get a logger for a specific module.

    Args:
        name (str): Name of the logger (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


# Function to log timing information
def log_time_taken(function_name, start_time, end_time):
    logger = get_logger(__name__)
    time_taken = end_time - start_time
    log_message = f"{function_name}: {time_taken:.2f} seconds"
    logger.info(log_message)
