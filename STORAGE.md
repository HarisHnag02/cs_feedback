# Storage Manager Documentation

## Overview

The storage manager module (`src/storage_manager.py`) provides caching functionality for Freshdesk feedback data. It generates deterministic filenames based on input parameters and manages data persistence in the `data/raw/` directory.

## Filename Format

All cached data files follow this deterministic naming pattern:

```
Feedback_<GameName>_<OS>_YYYY-MM-DD_to_YYYY-MM-DD.json
```

### Examples

| Input Parameters | Generated Filename |
|-----------------|-------------------|
| Game: "Candy Crush"<br>OS: "Android"<br>Dates: 2024-01-01 to 2024-01-31 | `Feedback_Candy_Crush_Android_2024-01-01_to_2024-01-31.json` |
| Game: "Subway Surfers"<br>OS: "iOS"<br>Dates: 2024-02-01 to 2024-02-29 | `Feedback_Subway_Surfers_iOS_2024-02-01_to_2024-02-29.json` |
| Game: "Clash of Clans"<br>OS: "Both"<br>Dates: 2024-03-15 to 2024-03-31 | `Feedback_Clash_of_Clans_Both_2024-03-15_to_2024-03-31.json` |

### Special Character Handling

Game names with special characters are sanitized:
- Spaces are preserved
- Invalid filename characters (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) are replaced with `_`

Example:
- Input: `"My Game: Special Edition!"`
- Output: `Feedback_My_Game__Special_Edition__Android_2024-01-01_to_2024-01-31.json`

## API Functions

### `exists(input_params)`

Check if cached data exists for given parameters.

**Parameters:**
- `input_params` (FeedbackAnalysisInput): Input parameters object

**Returns:**
- `bool`: True if cached data exists, False otherwise

**Logging:**
- Cache HIT: Logs info message with filename
- Cache MISS: Logs info message indicating no cache found

**Example:**
```python
from src.input_handler import FeedbackAnalysisInput
from src import storage_manager

params = FeedbackAnalysisInput(
    game_name="Candy Crush",
    os="Android",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

if storage_manager.exists(params):
    print("Cache found!")
else:
    print("No cache - need to fetch data")
```

### `load(input_params)`

Load cached feedback data from storage.

**Parameters:**
- `input_params` (FeedbackAnalysisInput): Input parameters object

**Returns:**
- `Dict[str, Any]`: Cached feedback data

**Raises:**
- `FileNotFoundError`: If cached data doesn't exist
- `JSONDecodeError`: If file contains invalid JSON

**Logging:**
- Logs info when loading starts
- Logs record count after successful load
- Logs errors on failure

**Example:**
```python
if storage_manager.exists(params):
    data = storage_manager.load(params)
    print(f"Loaded {len(data['feedbacks'])} feedbacks")
```

### `save(input_params, data)`

Save feedback data to storage with deterministic filename.

**Parameters:**
- `input_params` (FeedbackAnalysisInput): Input parameters object
- `data` (Dict[str, Any]): Feedback data to save

**Returns:**
- `Path`: Path where data was saved

**Logging:**
- Logs info when saving starts
- Logs record count after successful save
- Logs errors on failure

**Example:**
```python
feedback_data = {
    'metadata': {
        'game_name': 'Candy Crush',
        'fetched_at': '2024-01-24T10:30:00',
        'total_records': 150
    },
    'feedbacks': [
        {
            'id': 1,
            'subject': 'Great game!',
            'description': 'Love it!',
            'status': 'Closed'
        },
        # ... more feedbacks
    ]
}

saved_path = storage_manager.save(params, feedback_data)
print(f"Data saved to: {saved_path}")
```

## Additional Utility Functions

### `get_cache_info(input_params)`

Get metadata about cached data without loading it.

**Returns:**
- `Dict` with cache info or `None` if doesn't exist

**Cache Info Structure:**
```python
{
    'filename': 'Feedback_Game_Android_2024-01-01_to_2024-01-31.json',
    'path': '/full/path/to/file.json',
    'exists': True,
    'size_bytes': 45678,
    'size_kb': 44.61,
    'modified_time': 1706097600.0
}
```

**Example:**
```python
info = storage_manager.get_cache_info(params)
if info:
    print(f"Cache: {info['filename']}")
    print(f"Size: {info['size_kb']} KB")
```

### `delete(input_params)`

Delete cached data for given parameters.

**Returns:**
- `bool`: True if deleted, False if didn't exist

**Example:**
```python
if storage_manager.delete(params):
    print("Cache cleared successfully")
```

### `generate_filename(input_params)`

Generate deterministic filename (mainly for internal use).

**Returns:**
- `str`: Sanitized filename

**Example:**
```python
filename = storage_manager.generate_filename(params)
# Returns: "Feedback_Game_Android_2024-01-01_to_2024-01-31.json"
```

## Cache Hit/Miss Logging

The storage manager automatically logs cache hits and misses:

### Cache HIT
```
INFO - ✓ Cache HIT: Found cached data at Feedback_Candy_Crush_Android_2024-01-01_to_2024-01-31.json
INFO - 📂 Loading cached data from Feedback_Candy_Crush_Android_2024-01-01_to_2024-01-31.json
INFO - ✓ Successfully loaded 150 feedback records from cache
```

### Cache MISS
```
INFO - ✗ Cache MISS: No cached data found for Feedback_New_Game_iOS_2024-02-01_to_2024-02-28.json
```

## Typical Workflow

### 1. Check Cache Before Fetching

```python
from src.input_handler import get_validated_inputs
from src import storage_manager

# Get user inputs
params = get_validated_inputs()

# Check if we have cached data
if storage_manager.exists(params):
    # Cache hit - load existing data
    print("Using cached data...")
    data = storage_manager.load(params)
else:
    # Cache miss - fetch from API
    print("Fetching fresh data from Freshdesk...")
    data = fetch_from_freshdesk_api(params)  # To be implemented
    
    # Save to cache for future use
    storage_manager.save(params, data)
```

### 2. Force Refresh

```python
# Delete old cache
if storage_manager.exists(params):
    storage_manager.delete(params)
    print("Old cache cleared")

# Fetch fresh data
data = fetch_from_freshdesk_api(params)

# Save new cache
storage_manager.save(params, data)
```

### 3. Cache Management

```python
# Get cache info without loading
info = storage_manager.get_cache_info(params)
if info:
    print(f"Cache exists: {info['filename']}")
    print(f"Size: {info['size_kb']} KB")
    print(f"Last modified: {info['modified_time']}")
    
    # Option to use or refresh
    use_cache = input("Use cached data? (y/n): ")
    if use_cache.lower() == 'y':
        data = storage_manager.load(params)
    else:
        storage_manager.delete(params)
        data = fetch_fresh_data()
```

## Testing

Run the comprehensive test suite:

```bash
# Test storage manager functionality
python test_storage_manager.py

# Or test directly
python -m src.storage_manager
```

## Data Format

Recommended structure for cached data:

```json
{
  "metadata": {
    "game_name": "Candy Crush",
    "os": "Android",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "fetched_at": "2024-01-24T10:30:00Z",
    "total_records": 150,
    "source": "freshdesk_api"
  },
  "feedbacks": [
    {
      "id": 1001,
      "subject": "Bug report",
      "description": "Game crashes on startup",
      "status": "Open",
      "priority": "High",
      "created_at": "2024-01-15T09:30:00Z",
      "tags": ["bug", "crash"]
    }
  ]
}
```

## Best Practices

1. **Always check cache first** - Use `exists()` before fetching new data
2. **Log cache operations** - Storage manager handles this automatically
3. **Include metadata** - Store fetch time and parameters in the data
4. **Handle errors** - Use try/except when loading cached data
5. **Clean up tests** - Delete test caches after testing

## File Storage Location

All cached data is stored in:
```
data/raw/Feedback_*.json
```

This directory is created automatically if it doesn't exist.
