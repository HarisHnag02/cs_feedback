# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                      (Interactive CLI)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      main.py (Orchestrator)                      │
│  • Coordinates workflow                                          │
│  • Manages application lifecycle                                 │
└─────┬──────────────┬────────────────┬──────────────┬────────────┘
      │              │                │              │
      ▼              ▼                ▼              ▼
┌───────────┐  ┌──────────┐   ┌─────────────┐  ┌─────────┐
│  Input    │  │ Storage  │   │   Config    │  │ Logger  │
│  Handler  │  │ Manager  │   │  Manager    │  │         │
└───────────┘  └──────────┘   └─────────────┘  └─────────┘
      │              │                │              │
      │              │                │              │
      ▼              ▼                ▼              ▼
┌───────────────────────────────────────────────────────────┐
│                    Core Utilities                          │
│  • File operations (save_json, load_json, etc.)           │
│  • Filename sanitization                                   │
│  • Validation helpers                                      │
└───────────────────────────────────────────────────────────┘
      │
      ▼
┌───────────────────────────────────────────────────────────┐
│                   Data Persistence                         │
│                                                             │
│  data/raw/        - Raw Freshdesk data (cached)           │
│  data/processed/  - Cleaned/processed data                 │
│  reports/         - Generated reports (JSON/Markdown)      │
│  context/         - AI context and prompts                 │
└───────────────────────────────────────────────────────────┘
```

## Module Breakdown

### 1. Input Handler (`src/input_handler.py`)

**Purpose:** Collect and validate user inputs interactively

**Key Components:**
- `FeedbackAnalysisInput` - Dataclass for validated inputs
- `collect_user_inputs()` - Main input collection function
- `get_validated_inputs()` - Entry point with confirmation

**Input Flow:**
```
User → Game Name → OS Selection → Start Date → End Date → Confirmation → Validated Input
         ↓           ↓              ↓            ↓            ↓
      Validate   Validate       Validate     Validate    Review
      (empty)    (options)      (format)     (range)     (confirm)
```

**Validation Rules:**
- Game name: Cannot be empty
- OS: Must be Android, iOS, or Both (case-insensitive)
- Dates: Must match YYYY-MM-DD format
- Date range: Start date ≤ End date

**Output:**
```python
FeedbackAnalysisInput(
    game_name="Candy Crush",
    os="Android",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

### 2. Storage Manager (`src/storage_manager.py`)

**Purpose:** Manage data caching with deterministic filenames

**Key Functions:**
- `exists(params)` - Check if cache exists (logs HIT/MISS)
- `load(params)` - Load cached data
- `save(params, data)` - Save data to cache
- `get_cache_info(params)` - Get cache metadata
- `delete(params)` - Delete cache file

**Filename Generation:**
```
Input Parameters → Sanitize → Build Filename → Store in data/raw/

Example:
  Game: "Candy Crush Saga"
  OS: "Android"
  Dates: 2024-01-01 to 2024-01-31
  
  ↓
  
  Feedback_Candy_Crush_Saga_Android_2024-01-01_to_2024-01-31.json
```

**Cache Logic:**
```
Request Data
     ↓
Does cache exist?
  ├─ YES → Cache HIT  → Load from cache → Return data
  └─ NO  → Cache MISS → Fetch from API → Save to cache → Return data
```

### 3. Configuration Manager (`src/config.py`)

**Purpose:** Centralized configuration and environment management

**Key Components:**
- `Settings` - Pydantic model for configuration
- `get_settings()` - Load and validate settings
- `ensure_directories()` - Create required directories
- Directory path constants

**Configuration Sources:**
1. Environment variables (`.env` file)
2. Default values (fallbacks)
3. Runtime validation (Pydantic)

**Directory Structure:**
```python
PROJECT_ROOT/
├── context/              # CONTEXT_DIR
├── data/
│   ├── raw/             # DATA_RAW_DIR
│   └── processed/       # DATA_PROCESSED_DIR
├── reports/
│   ├── json/            # REPORTS_JSON_DIR
│   └── markdown/        # REPORTS_MARKDOWN_DIR
└── src/                 # SRC_DIR
```

### 4. Logger (`src/logger.py`)

**Purpose:** Consistent logging across all modules

**Features:**
- Colored console output (via `colorlog`)
- File logging (optional)
- Configurable log levels
- Module-specific loggers

**Log Levels:**
```
DEBUG    → Detailed diagnostic information
INFO     → General informational messages
WARNING  → Warning messages
ERROR    → Error messages
CRITICAL → Critical errors
```

**Usage Pattern:**
```python
from src.logger import get_logger

logger = get_logger(__name__)
logger.info("Operation successful")
logger.error("Operation failed")
```

### 5. Utilities (`src/utils.py`)

**Purpose:** Common helper functions

**Functions:**
- `save_json(data, path)` - Save JSON with formatting
- `load_json(path)` - Load JSON from file
- `save_markdown(content, path)` - Save Markdown file
- `get_timestamp()` - Generate timestamp strings
- `sanitize_filename(name)` - Clean filenames
- `create_file_path()` - Build file paths
- `validate_api_key()` - Validate API key format

## Data Flow

### Complete Workflow (When Implemented)

```
1. User Input Collection
   ┌─────────────────┐
   │ Interactive CLI │
   │ (Input Handler) │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Validate Inputs │
   └────────┬────────┘
            │
            ▼

2. Cache Check
   ┌──────────────────┐
   │ Storage Manager  │
   │  exists(params)  │
   └────────┬─────────┘
            │
        ┌───┴───┐
        │       │
    HIT │       │ MISS
        │       │
        ▼       ▼
   ┌────────┐  ┌──────────────┐
   │ Load   │  │ Fetch from   │
   │ Cache  │  │ Freshdesk    │
   └───┬────┘  │ API          │
       │       └──────┬───────┘
       │              │
       │              ▼
       │       ┌──────────────┐
       │       │ Save to      │
       │       │ Cache        │
       │       └──────┬───────┘
       │              │
       └──────┬───────┘
              │
              ▼

3. AI Analysis
   ┌──────────────────┐
   │ OpenAI API       │
   │ • Sentiment      │
   │ • Topics         │
   │ • Trends         │
   └────────┬─────────┘
            │
            ▼

4. Report Generation
   ┌──────────────────┐
   │ Generate Reports │
   ├──────────────────┤
   │ • JSON format    │
   │ • Markdown       │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Save to          │
   │ reports/         │
   └──────────────────┘
```

## Design Patterns

### 1. Separation of Concerns
Each module has a single, well-defined responsibility:
- Input handling ≠ Storage ≠ Configuration ≠ Logging

### 2. Dependency Injection
Configuration and logger are injected where needed:
```python
settings = get_settings()  # Centralized config
logger = get_logger(__name__)  # Module-specific logger
```

### 3. Dataclass for Data Transfer
Using `@dataclass` for clean data structures:
```python
@dataclass
class FeedbackAnalysisInput:
    game_name: str
    os: str
    start_date: str
    end_date: str
```

### 4. Deterministic Operations
Storage filenames are deterministic based on inputs:
- Same inputs → Same filename
- Enables predictable caching

### 5. Error Handling
Comprehensive error handling at each layer:
- Input validation with retry
- File operation error handling
- Configuration validation
- API error handling (to be implemented)

## Testing Strategy

### Unit Tests (Per Module)
```
test_input_handler.py    → Input collection and validation
test_storage_manager.py  → Cache operations
test_config.py           → Configuration loading
test_utils.py            → Utility functions
```

### Integration Tests
```
Test complete workflows:
1. Input → Storage → Load
2. Input → API → Cache → Load
3. Full pipeline end-to-end
```

### Test Execution
```bash
# Individual module tests
python test_input_handler.py
python test_storage_manager.py
python -m src.storage_manager

# Full application test
python main.py
```

## Configuration Management

### Environment Variables
```
.env (git-ignored)
├── FRESHDESK_API_KEY    → Freshdesk authentication
├── OPENAI_API_KEY       → OpenAI authentication
├── FRESHDESK_DOMAIN     → Optional: Your Freshdesk domain
└── LOG_LEVEL            → Optional: Logging level
```

### Loading Order
1. Load `.env` file (if exists)
2. Read environment variables
3. Validate with Pydantic
4. Apply defaults where needed
5. Return validated `Settings` object

## Security Considerations

1. **API Keys:** Never committed to git (`.gitignore`)
2. **Validation:** All inputs validated before use
3. **Sanitization:** Filenames sanitized to prevent injection
4. **Logging:** Sensitive data not logged in plain text
5. **Error Messages:** Don't expose sensitive information

## Extensibility Points

### Adding New Data Sources
1. Create new module in `src/`
2. Follow existing patterns (dataclass, logging)
3. Integrate with storage manager for caching

### Adding New Report Formats
1. Add format-specific generator in `src/`
2. Use existing utilities for file operations
3. Store in appropriate `reports/` subdirectory

### Adding New Validation Rules
1. Extend validation functions in `input_handler.py`
2. Add new error messages
3. Update documentation

## Performance Optimization

### Caching Strategy
- **Cache First:** Always check cache before API calls
- **Deterministic Keys:** Same query → Same cache file
- **Metadata Tracking:** Store fetch time and parameters

### Future Optimizations
- Implement cache expiry (time-based)
- Add cache size limits
- Implement incremental updates
- Add parallel processing for large datasets

## Current Status

### ✅ Completed Components
- Project structure
- Input handler with validation
- Storage manager with caching
- Configuration management
- Logging system
- Core utilities

### 🚧 In Progress
- None (awaiting next implementation phase)

### 📋 Pending Components
- Freshdesk API integration
- OpenAI API integration
- Report generation
- Automated workflows
- Testing framework
