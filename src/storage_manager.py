"""
Storage manager module for caching Freshdesk feedback data.

This module handles storage and retrieval of raw feedback data with deterministic
filenames, enabling caching to avoid redundant API calls. Data is stored in JSON
format in the data/raw/ directory.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .config import DATA_RAW_DIR
from .input_handler import FeedbackAnalysisInput
from .logger import get_logger
from .utils import load_json, sanitize_filename, save_json


# Initialize logger for this module
logger = get_logger(__name__)


def generate_filename(input_params: FeedbackAnalysisInput) -> str:
    """
    Generate a deterministic filename based on input parameters.
    
    Format: Feedback_<GameName>_<OS>_YYYY-MM-DD_to_YYYY-MM-DD.json
    
    Args:
        input_params: FeedbackAnalysisInput object containing game name, OS, and dates
        
    Returns:
        str: Sanitized filename
        
    Example:
        >>> params = FeedbackAnalysisInput(
        ...     game_name="Candy Crush",
        ...     os="Android",
        ...     start_date="2024-01-01",
        ...     end_date="2024-01-31"
        ... )
        >>> generate_filename(params)
        'Feedback_Candy_Crush_Android_2024-01-01_to_2024-01-31.json'
    """
    # Sanitize game name for filename (replace spaces and special chars)
    safe_game_name = sanitize_filename(input_params.game_name)
    
    # Build filename components
    filename = (
        f"Feedback_{safe_game_name}_{input_params.os}_"
        f"{input_params.start_date}_to_{input_params.end_date}.json"
    )
    
    logger.debug(f"Generated filename: {filename}")
    return filename


def get_file_path(input_params: FeedbackAnalysisInput) -> Path:
    """
    Get the full file path for storing/retrieving feedback data.
    
    Args:
        input_params: FeedbackAnalysisInput object
        
    Returns:
        Path: Complete path to the data file in data/raw/ directory
    """
    filename = generate_filename(input_params)
    file_path = DATA_RAW_DIR / filename
    return file_path


def exists(input_params: FeedbackAnalysisInput) -> bool:
    """
    Check if cached data exists for the given input parameters.
    
    Args:
        input_params: FeedbackAnalysisInput object
        
    Returns:
        bool: True if cached data file exists, False otherwise
        
    Example:
        >>> params = FeedbackAnalysisInput(...)
        >>> if exists(params):
        ...     print("Cache hit!")
        ... else:
        ...     print("Cache miss - need to fetch data")
    """
    file_path = get_file_path(input_params)
    file_exists = file_path.exists()
    
    if file_exists:
        logger.info(f"✓ Cache HIT: Found cached data at {file_path.name}")
    else:
        logger.info(f"✗ Cache MISS: No cached data found for {file_path.name}")
    
    return file_exists


def load(input_params: FeedbackAnalysisInput) -> Dict[str, Any]:
    """
    Load cached feedback data from storage.
    
    Args:
        input_params: FeedbackAnalysisInput object
        
    Returns:
        Dict containing the cached feedback data
        
    Raises:
        FileNotFoundError: If cached data doesn't exist
        JSONDecodeError: If file contains invalid JSON
        
    Example:
        >>> params = FeedbackAnalysisInput(...)
        >>> if exists(params):
        ...     data = load(params)
        ...     print(f"Loaded {len(data['feedbacks'])} feedbacks")
    """
    file_path = get_file_path(input_params)
    
    if not file_path.exists():
        logger.error(f"Attempted to load non-existent cache: {file_path.name}")
        raise FileNotFoundError(
            f"No cached data found at {file_path}. "
            f"Use exists() to check before loading."
        )
    
    logger.info(f"📂 Loading cached data from {file_path.name}")
    
    try:
        data = load_json(file_path)
        
        # Log some metadata about the loaded data
        if isinstance(data, dict):
            record_count = len(data.get('feedbacks', []))
            logger.info(f"✓ Successfully loaded {record_count} feedback records from cache")
        else:
            logger.info(f"✓ Successfully loaded cached data")
        
        return data
        
    except Exception as e:
        logger.error(f"Failed to load cached data from {file_path.name}: {e}")
        raise


def save(input_params: FeedbackAnalysisInput, data: Dict[str, Any]) -> Path:
    """
    Save feedback data to storage with deterministic filename.
    
    Args:
        input_params: FeedbackAnalysisInput object
        data: Dictionary containing feedback data to save
        
    Returns:
        Path: Path where the data was saved
        
    Example:
        >>> params = FeedbackAnalysisInput(...)
        >>> feedback_data = {
        ...     'metadata': {...},
        ...     'feedbacks': [...]
        ... }
        >>> save(params, feedback_data)
    """
    file_path = get_file_path(input_params)
    
    logger.info(f"💾 Saving feedback data to {file_path.name}")
    
    try:
        # Ensure the directory exists
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save the data
        save_json(data, file_path)
        
        # Log some metadata about saved data
        if isinstance(data, dict):
            record_count = len(data.get('feedbacks', []))
            logger.info(f"✓ Successfully saved {record_count} feedback records to cache")
        else:
            logger.info(f"✓ Successfully saved data to cache")
        
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save data to {file_path.name}: {e}")
        raise


def get_cache_info(input_params: FeedbackAnalysisInput) -> Optional[Dict[str, Any]]:
    """
    Get information about cached data without loading it.
    
    Args:
        input_params: FeedbackAnalysisInput object
        
    Returns:
        Dict with cache info (filename, path, exists, size) or None if doesn't exist
        
    Example:
        >>> params = FeedbackAnalysisInput(...)
        >>> info = get_cache_info(params)
        >>> if info:
        ...     print(f"Cache file: {info['filename']}, Size: {info['size_kb']} KB")
    """
    file_path = get_file_path(input_params)
    
    if not file_path.exists():
        return None
    
    file_stat = file_path.stat()
    
    return {
        'filename': file_path.name,
        'path': str(file_path),
        'exists': True,
        'size_bytes': file_stat.st_size,
        'size_kb': round(file_stat.st_size / 1024, 2),
        'modified_time': file_stat.st_mtime
    }


def delete(input_params: FeedbackAnalysisInput) -> bool:
    """
    Delete cached data for the given input parameters.
    
    Args:
        input_params: FeedbackAnalysisInput object
        
    Returns:
        bool: True if file was deleted, False if file didn't exist
        
    Example:
        >>> params = FeedbackAnalysisInput(...)
        >>> if delete(params):
        ...     print("Cache cleared")
    """
    file_path = get_file_path(input_params)
    
    if not file_path.exists():
        logger.warning(f"Attempted to delete non-existent cache: {file_path.name}")
        return False
    
    try:
        file_path.unlink()
        logger.info(f"🗑️  Deleted cached data: {file_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete cache file {file_path.name}: {e}")
        raise


if __name__ == "__main__":
    # Test the storage manager
    from datetime import datetime
    
    print("\n" + "="*60)
    print("  TESTING STORAGE MANAGER")
    print("="*60 + "\n")
    
    # Create test input parameters
    test_params = FeedbackAnalysisInput(
        game_name="Candy Crush Saga",
        os="Android",
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    
    print(f"Test Parameters:")
    print(f"  Game: {test_params.game_name}")
    print(f"  OS: {test_params.os}")
    print(f"  Period: {test_params.start_date} to {test_params.end_date}")
    print()
    
    # Test filename generation
    filename = generate_filename(test_params)
    print(f"Generated Filename: {filename}")
    print()
    
    # Test exists (should be False initially)
    print("Checking if cache exists...")
    cache_exists = exists(test_params)
    print(f"Cache exists: {cache_exists}")
    print()
    
    # Create some test data
    test_data = {
        'metadata': {
            'game_name': test_params.game_name,
            'os': test_params.os,
            'start_date': test_params.start_date,
            'end_date': test_params.end_date,
            'fetched_at': datetime.now().isoformat(),
            'source': 'test'
        },
        'feedbacks': [
            {
                'id': 1,
                'subject': 'Great game!',
                'description': 'Love the new features',
                'status': 'Resolved',
                'priority': 'Medium'
            },
            {
                'id': 2,
                'subject': 'Bug report',
                'description': 'Game crashes on level 10',
                'status': 'Open',
                'priority': 'High'
            },
            {
                'id': 3,
                'subject': 'Feature request',
                'description': 'Please add dark mode',
                'status': 'Open',
                'priority': 'Low'
            }
        ]
    }
    
    # Test save
    print("Saving test data...")
    saved_path = save(test_params, test_data)
    print(f"Data saved to: {saved_path}")
    print()
    
    # Test exists (should be True now)
    print("Checking if cache exists after save...")
    cache_exists = exists(test_params)
    print(f"Cache exists: {cache_exists}")
    print()
    
    # Test cache info
    print("Getting cache info...")
    cache_info = get_cache_info(test_params)
    if cache_info:
        print(f"  Filename: {cache_info['filename']}")
        print(f"  Size: {cache_info['size_kb']} KB")
        print(f"  Path: {cache_info['path']}")
    print()
    
    # Test load
    print("Loading data from cache...")
    loaded_data = load(test_params)
    print(f"Loaded {len(loaded_data['feedbacks'])} feedback records")
    print()
    
    # Verify data integrity
    print("Verifying data integrity...")
    if loaded_data == test_data:
        print("✓ Data integrity verified - loaded data matches saved data")
    else:
        print("✗ Data mismatch!")
    print()
    
    # Test delete
    print("Cleaning up - deleting test cache...")
    deleted = delete(test_params)
    print(f"Cache deleted: {deleted}")
    print()
    
    # Verify deletion
    print("Verifying deletion...")
    cache_exists = exists(test_params)
    print(f"Cache exists after deletion: {cache_exists}")
    print()
    
    print("="*60)
    print("✅ Storage manager tests completed!")
    print("="*60 + "\n")
