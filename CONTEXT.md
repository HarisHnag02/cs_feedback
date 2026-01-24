# Game Feature Context Documentation

## Overview

The context loader (`src/context_loader.py`) loads game-specific information from YAML files to provide essential context for AI analysis. This context helps the AI understand game features, constraints, and recent changes when analyzing player feedback.

## Purpose

Player feedback often references specific game features, mechanics, or recent updates. Without context, AI analysis might:
- Misinterpret technical limitations as bugs
- Suggest features that already exist
- Miss connections to recent changes
- Not understand game-specific constraints

The context loader solves this by providing structured game information to the AI.

## Context File Format

### Location

```
context/game_features.yaml
```

### Required Fields

All context files **must** include these four fields:

1. **`game_name`** (string)
   - Name of the game
   - Used to validate context matches the analysis target

2. **`current_features`** (list of strings)
   - All major features currently in the game
   - Helps AI understand what already exists
   - Prevents suggestions for existing features

3. **`known_constraints`** (list of strings)
   - Technical or design limitations
   - Helps AI understand why certain issues exist
   - Prevents unrealistic suggestions

4. **`recent_changes`** (list of strings)
   - Recent updates, patches, or changes
   - Helps AI correlate feedback with specific versions
   - Identifies issues introduced by recent updates

### Optional Fields

You can add any additional fields for extra context:
- `target_audience`
- `platform`
- `monetization_model`
- `known_pain_points`
- `competitive_games`
- etc.

### Example File

```yaml
game_name: Candy Crush Saga

current_features:
  - "Match-3 puzzle gameplay with various candy types"
  - "Hundreds of levels with increasing difficulty"
  - "Daily challenges and special events"
  - "Boosters and power-ups"
  - "Social features and leaderboards"

known_constraints:
  - "Performance issues on older Android devices (pre-2018)"
  - "Limited server capacity during peak hours"
  - "Facebook integration occasionally causes login issues"
  - "Memory limitations on devices with less than 2GB RAM"

recent_changes:
  - "v2.5.0 (Jan 2024): Added new 'Ice Breaker' event"
  - "v2.4.8 (Dec 2023): Fixed crash issue on iOS 17"
  - "v2.4.7 (Dec 2023): Improved loading times by 30%"

target_audience: "Casual mobile gamers, ages 18-45"
platform: "iOS and Android"
```

## API Reference

### GameFeatureContext Class

Main dataclass for structured context data.

**Attributes:**
- `game_name: str` - Name of the game
- `current_features: List[str]` - List of current features
- `known_constraints: List[str]` - List of known limitations
- `recent_changes: List[str]` - List of recent updates
- `additional_info: Dict[str, Any]` - Any additional context fields

**Methods:**

#### `to_dict() -> Dict`

Convert context to dictionary format.

```python
context = load_game_context()
data = context.to_dict()
# Returns: {'game_name': '...', 'current_features': [...], ...}
```

#### `format_for_ai() -> str`

Format context as structured string for AI prompts.

```python
context = load_game_context()
prompt = f"""
Analyze this feedback with the following game context:

{context.format_for_ai()}

Feedback: ...
"""
```

**Output format:**
```
GAME: Candy Crush Saga

CURRENT FEATURES:
  • Match-3 puzzle gameplay
  • Hundreds of levels
  • Daily challenges

KNOWN CONSTRAINTS:
  • Performance issues on older devices
  • Limited server capacity

RECENT CHANGES:
  • v2.5.0: Added new event
  • v2.4.8: Fixed iOS crash
```

### Functions

#### `load_game_context(game_name=None) -> GameFeatureContext`

Load and validate game context from YAML file.

**Parameters:**
- `game_name` (Optional[str]): Game name to validate against context

**Returns:**
- `GameFeatureContext`: Validated context object

**Raises:**
- `ContextLoaderError`: If file missing, invalid, or validation fails

**Example:**
```python
from src.context_loader import load_game_context

# Load context
context = load_game_context()

# Load with validation
context = load_game_context(game_name="Candy Crush")

# Access data
print(f"Game: {context.game_name}")
print(f"Features: {len(context.current_features)}")
```

#### `create_sample_context_file(game_name="Sample Game") -> Path`

Create a sample/template context file.

**Parameters:**
- `game_name` (str): Name for the sample game

**Returns:**
- `Path`: Path to created file

**Example:**
```python
from src.context_loader import create_sample_context_file

# Create sample
file_path = create_sample_context_file("My Game")
print(f"Sample created at: {file_path}")
```

## Validation

The loader performs comprehensive validation:

### 1. File Existence
```python
# Checks if context/game_features.yaml exists
# Raises: ContextLoaderError if missing
```

### 2. YAML Syntax
```python
# Validates YAML can be parsed
# Raises: ContextLoaderError if invalid syntax
```

### 3. Required Fields
```python
# Ensures all 4 required fields present
# Required: game_name, current_features, known_constraints, recent_changes
# Raises: ContextLoaderError if any missing
```

### 4. Field Types
```python
# Validates field types are correct
# game_name: must be string
# current_features: must be list
# known_constraints: must be list
# recent_changes: must be list
# Raises: ContextLoaderError if wrong type
```

### 5. List Contents
```python
# Validates lists contain only non-empty strings
# Raises: ContextLoaderError if list contains non-string or empty string
```

### 6. Game Name Matching (optional)
```python
# If game_name parameter provided, checks match
# Logs warning if mismatch but doesn't fail
# Allows flexibility for similar game names
```

## Error Handling

### ContextLoaderError Exception

Custom exception for all context loading errors.

**Common Errors:**

#### Missing File
```
Error: Context file not found: context/game_features.yaml
Please create the file with required game context.
```

**Solution:** Create `context/game_features.yaml`

#### Empty File
```
Error: YAML file is empty: context/game_features.yaml
Please add game context information.
```

**Solution:** Add content to the file

#### Invalid YAML
```
Error: Invalid YAML syntax in context/game_features.yaml:
...
Please check the YAML file format.
```

**Solution:** Fix YAML syntax errors

#### Missing Required Fields
```
Error: Missing required fields in context file: known_constraints, recent_changes
Required fields: game_name, current_features, known_constraints, recent_changes
```

**Solution:** Add all required fields

#### Wrong Field Type
```
Error: Field 'current_features' must be a list, got str
```

**Solution:** Change field to correct type (use list format with `-` items)

#### Invalid List Contents
```
Error: Field 'current_features' must contain only strings.
Item at index 2 is dict
```

**Solution:** Ensure all list items are strings

## Usage Examples

### Basic Loading

```python
from src.context_loader import load_game_context

try:
    context = load_game_context()
    print(f"Loaded context for: {context.game_name}")
    print(f"Features: {len(context.current_features)}")
except ContextLoaderError as e:
    print(f"Failed to load context: {e}")
```

### With Game Name Validation

```python
from src.input_handler import get_validated_inputs
from src.context_loader import load_game_context

# Get user inputs
params = get_validated_inputs()

# Load context with validation
context = load_game_context(game_name=params.game_name)
```

### AI Integration

```python
from src.context_loader import load_game_context
from src.freshdesk_client import fetch_feedback_data

# Load game context
context = load_game_context()

# Fetch feedback
data = fetch_feedback_data(params)

# Prepare AI prompt with context
ai_prompt = f"""
Analyze the following player feedback for {context.game_name}.

{context.format_for_ai()}

FEEDBACK TO ANALYZE:
{data['feedbacks'][0]['description']}

Provide insights considering the game's features, constraints, and recent changes.
"""

# Send to AI for analysis
# ... (OpenAI integration to be implemented)
```

### Accessing Specific Information

```python
context = load_game_context()

# Check if specific feature exists
if any('multiplayer' in feature.lower() for feature in context.current_features):
    print("Game has multiplayer features")

# Check recent changes
recent_versions = [change for change in context.recent_changes if 'v2.5' in change]
print(f"Recent v2.5 changes: {recent_versions}")

# Access additional info
if 'target_audience' in context.additional_info:
    audience = context.additional_info['target_audience']
    print(f"Target audience: {audience}")
```

### Creating Custom Context

```python
from src.context_loader import create_sample_context_file
from pathlib import Path

# Create sample as template
sample_path = create_sample_context_file("My New Game")

# Edit the file
# Then load it
context = load_game_context()
```

## Integration with Analysis Pipeline

The context loader fits into the analysis pipeline:

```
1. User Input Collection
   ↓
2. Load Game Context ← YOU ARE HERE
   ↓
3. Fetch Freshdesk Data
   ↓
4. AI Analysis (with context)
   ↓
5. Generate Reports
```

### Complete Workflow Example

```python
from src.input_handler import get_validated_inputs
from src.context_loader import load_game_context, ContextLoaderError
from src.freshdesk_client import fetch_feedback_data
from src import storage_manager

# 1. Get user inputs
params = get_validated_inputs()

# 2. Load game context
try:
    context = load_game_context(game_name=params.game_name)
    print(f"✓ Context loaded: {context.game_name}")
except ContextLoaderError as e:
    print(f"⚠️  Context not available: {e}")
    print("Continuing without game context...")
    context = None

# 3. Get feedback data (from cache or Freshdesk)
if storage_manager.exists(params):
    data = storage_manager.load(params)
else:
    data = fetch_feedback_data(params)
    storage_manager.save(params, data)

# 4. Prepare for AI analysis
if context:
    # AI analysis will use context
    ai_context = context.format_for_ai()
else:
    # AI analysis without context
    ai_context = None

# 5. Analyze with AI (to be implemented)
# ...
```

## Best Practices

### 1. Keep Context Updated

Update `game_features.yaml` when:
- New features are released
- Major changes are made
- Known issues are discovered
- Recent changes list gets outdated

### 2. Be Specific

Use detailed, clear descriptions:

❌ Bad:
```yaml
current_features:
  - "Levels"
  - "Items"
```

✅ Good:
```yaml
current_features:
  - "500+ puzzle levels with varying difficulty"
  - "Boosters and power-ups: color bomb, striped candy, wrapped candy"
```

### 3. Document Constraints

Include both technical and design constraints:
```yaml
known_constraints:
  - "Technical: Cannot support more than 100 friends in social features"
  - "Design: Level difficulty cannot be changed post-release"
  - "Business: IAP restrictions in certain countries"
```

### 4. Version Recent Changes

Include version numbers and dates:
```yaml
recent_changes:
  - "v2.5.0 (Jan 2024): Feature description"
  - "v2.4.8 (Dec 2023): Bug fix description"
```

### 5. Use Additional Context

Add relevant extra fields:
```yaml
known_pain_points:
  - "Level 147 is notoriously difficult"
  - "Players complain about life regeneration time"

competitive_games:
  - "Homescapes"
  - "Gardenscapes"
```

## Testing

### Run Test Suite

```bash
# Comprehensive tests
python test_context_loader.py

# Module self-test
python -m src.context_loader
```

### Test Coverage

- ✅ Load existing context
- ✅ Game name validation
- ✅ Context formatting (dict, AI, string)
- ✅ Detail access
- ✅ Sample file creation
- ✅ Error handling (all error types)
- ✅ AI integration simulation

## Troubleshooting

### Context file not found

**Problem:** `ContextLoaderError: Context file not found`

**Solution:**
1. Check file exists at `context/game_features.yaml`
2. Create sample: `python -m src.context_loader`
3. Edit sample with your game's information

### YAML syntax errors

**Problem:** `ContextLoaderError: Invalid YAML syntax`

**Solution:**
1. Validate YAML syntax (use online validator)
2. Check indentation (use spaces, not tabs)
3. Check for unclosed brackets/quotes
4. Look at example in this file

### Empty lists warning

**Problem:** Warning about empty lists

**Solution:**
- Add at least one item to each required list field
- Use meaningful, descriptive entries

## Example: Complete Context File

See `context/game_features.yaml` for a complete example with all fields properly filled out.

## Next Steps

Once context is loaded:
1. Integrate with OpenAI API for analysis
2. Use context in report generation
3. Reference context in feedback insights

The context enhances AI understanding and improves analysis quality significantly!
