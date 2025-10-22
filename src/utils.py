"""
Utility functions for the Charlie application.

This module contains various helper functions used throughout the application.
"""

import os
import json
import logging
import platform
from datetime import datetime
import psutil
import sys

logger = logging.getLogger('Charlie.Utils')

def get_system_info():
    """
    Get system information.
    
    Returns:
        dict: Dictionary containing system information.
    """
    info = {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Architecture": platform.machine(),
        "Python Version": platform.python_version(),
        "CPU Cores": psutil.cpu_count(logical=False),
        "Logical CPUs": psutil.cpu_count(logical=True),
        "Memory Total (GB)": round(psutil.virtual_memory().total / (1024**3), 2),
        "Memory Available (GB)": round(psutil.virtual_memory().available / (1024**3), 2),
    }
    
    # Add environment information
    info["Environment"] = "Development" if os.environ.get("CHARLIE_DEV") else "Production"
    
    # Add path information
    info["Script Path"] = os.path.abspath(sys.argv[0])
    info["Working Directory"] = os.getcwd()
    
    return info

def create_directory_if_not_exists(directory_path):
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory_path (str): Path to the directory to create.
        
    Returns:
        bool: True if directory exists or was created, False otherwise.
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            logger.info(f"Created directory: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {e}")
        return False

def save_json(data, file_path):
    """
    Save data as JSON to a file.
    
    Args:
        data: Data to save (must be JSON serializable).
        file_path (str): Path to save the file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Data saved to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def load_json(file_path, default=None):
    """
    Load JSON data from a file.
    
    Args:
        file_path (str): Path to the JSON file.
        default: Default value to return if file doesn't exist or is invalid.
        
    Returns:
        The loaded data or default value if loading fails.
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return default
            
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return default

def format_timestamp(timestamp=None, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Format a timestamp.
    
    Args:
        timestamp (datetime, optional): Timestamp to format. Defaults to current time.
        format_str (str, optional): Format string. Defaults to "%Y-%m-%d %H:%M:%S".
        
    Returns:
        str: Formatted timestamp.
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return timestamp.strftime(format_str)

def parse_timestamp(timestamp_str, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Parse a timestamp string into a datetime object.
    
    Args:
        timestamp_str (str): Timestamp string to parse.
        format_str (str, optional): Format string. Defaults to "%Y-%m-%d %H:%M:%S".
        
    Returns:
        datetime: Parsed datetime object or None if parsing fails.
    """
    try:
        return datetime.strptime(timestamp_str, format_str)
    except Exception as e:
        logger.error(f"Error parsing timestamp {timestamp_str}: {e}")
        return None

def is_valid_file_path(path):
    """
    Check if a file path is valid.
    
    Args:
        path (str): Path to check.
        
    Returns:
        bool: True if path is valid, False otherwise.
    """
    if not path:
        return False
    
    try:
        # Check if the directory exists
        dir_path = os.path.dirname(os.path.abspath(path))
        if not os.path.exists(dir_path):
            return False
        
        # Try to open the file to check write permissions
        if os.path.exists(path):
            with open(path, 'a'):
                pass
        else:
            with open(path, 'w'):
                pass
            os.remove(path)  # Clean up the test file
            
        return True
    except (IOError, OSError):
        return False


def sanitize_filename(filename):
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename (str): Filename to sanitize.
        
    Returns:
        str: Sanitized filename.
    """
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Ensure filename is not too long
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename
