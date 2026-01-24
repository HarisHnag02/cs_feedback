"""
Utility functions for the Freshdesk Feedback AI Analysis System.

This module contains helper functions used across different parts of the application,
including file operations, data validation, and common transformations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logger import get_logger


# Initialize logger for this module
logger = get_logger(__name__)


def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """
    Save data to a JSON file with proper formatting.
    
    Args:
        data: Dictionary to save as JSON
        file_path: Path where the JSON file should be saved
        
    Raises:
        IOError: If file cannot be written
    """
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON with indentation for readability
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully saved JSON to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        raise


def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file to load
        
    Returns:
        Dict containing the loaded JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        JSONDecodeError: If file contains invalid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Successfully loaded JSON from {file_path}")
        return data
        
    except FileNotFoundError:
        logger.error(f"JSON file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise


def save_markdown(content: str, file_path: Path) -> None:
    """
    Save content to a Markdown file.
    
    Args:
        content: String content to save
        file_path: Path where the Markdown file should be saved
        
    Raises:
        IOError: If file cannot be written
    """
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Successfully saved Markdown to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save Markdown to {file_path}: {e}")
        raise


def get_timestamp(format: str = "%Y%m%d_%H%M%S") -> str:
    """
    Get current timestamp as a formatted string.
    
    Args:
        format: strftime format string (default: YYYYmmdd_HHMMSS)
        
    Returns:
        Formatted timestamp string
        
    Example:
        >>> get_timestamp()
        '20260124_143022'
    """
    return datetime.now().strftime(format)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a safe filename.
    
    Removes or replaces characters that are invalid in filenames.
    
    Args:
        filename: Original filename string
        
    Returns:
        Sanitized filename safe for use across different operating systems
        
    Example:
        >>> sanitize_filename("Report: 2024/01/15")
        'Report_2024_01_15'
    """
    # Characters to replace with underscore
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    return sanitized


def create_file_path(
    directory: Path,
    filename: str,
    extension: str,
    add_timestamp: bool = True
) -> Path:
    """
    Create a file path with optional timestamp.
    
    Args:
        directory: Directory where file should be located
        filename: Base filename (without extension)
        extension: File extension (with or without leading dot)
        add_timestamp: Whether to add timestamp to filename
        
    Returns:
        Complete Path object for the file
        
    Example:
        >>> create_file_path(Path("reports"), "analysis", ".json")
        PosixPath('reports/analysis_20260124_143022.json')
    """
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Add timestamp if requested
    if add_timestamp:
        timestamp = get_timestamp()
        safe_filename = f"{safe_filename}_{timestamp}"
    
    # Ensure extension starts with a dot
    if not extension.startswith('.'):
        extension = f".{extension}"
    
    # Create full path
    file_path = directory / f"{safe_filename}{extension}"
    
    return file_path


def validate_api_key(api_key: str, key_name: str = "API Key") -> bool:
    """
    Validate that an API key is not empty and has reasonable length.
    
    Args:
        api_key: API key string to validate
        key_name: Name of the key for error messages
        
    Returns:
        True if API key appears valid, False otherwise
    """
    if not api_key:
        logger.error(f"{key_name} is empty")
        return False
    
    if len(api_key) < 10:
        logger.warning(f"{key_name} seems too short (length: {len(api_key)})")
        return False
    
    return True


if __name__ == "__main__":
    # Test utility functions
    print("Testing utility functions...\n")
    
    # Test timestamp
    timestamp = get_timestamp()
    print(f"Current timestamp: {timestamp}")
    
    # Test filename sanitization
    test_filename = "Report: 2024/01/15 - Q1 Results?"
    sanitized = sanitize_filename(test_filename)
    print(f"Sanitized filename: {sanitized}")
    
    # Test file path creation
    test_path = create_file_path(
        Path("reports/json"),
        "test_report",
        "json",
        add_timestamp=True
    )
    print(f"Generated path: {test_path}")
    
    # Test API key validation
    valid = validate_api_key("sk-1234567890abcdef", "Test Key")
    print(f"API key valid: {valid}")
