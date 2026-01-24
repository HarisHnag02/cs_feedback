# Usage Guide

## Interactive Input Handler

The system includes a robust interactive CLI input handler that collects feedback analysis parameters from the user.

### Running the Application

```bash
# Activate your virtual environment first
source venv/bin/activate

# Run the main application
python main.py
```

### Running Just the Input Handler (for testing)

```bash
# Test the input handler independently
python test_input_handler.py

# Or run it directly
python -m src.input_handler
```

## Input Flow

The application will prompt you for inputs in this order:

### 1. Game Name
```
📱 Enter Game Name: Candy Crush
```
- **Validation**: Cannot be empty
- **Processing**: Trimmed of leading/trailing whitespace

### 2. Operating System
```
💻 Select Operating System:
   Options: Android, iOS, Both
   Enter OS: Android
```
- **Validation**: Must be one of: `Android`, `iOS`, or `Both`
- **Case-insensitive**: `android`, `ANDROID`, `Android` all work
- **Error handling**: Re-prompts if invalid option entered

### 3. Start Date
```
📅 Start Date
   Format: YYYY-MM-DD (e.g., 2024-01-15)
   Enter date: 2024-01-01
```
- **Format**: Must be `YYYY-MM-DD`
- **Validation**: Must be a valid calendar date
- **Examples**: `2024-01-15`, `2023-12-31`

### 4. End Date
```
📅 End Date
   Format: YYYY-MM-DD (e.g., 2024-01-15)
   Enter date: 2024-01-31
```
- **Format**: Must be `YYYY-MM-DD`
- **Validation**: 
  - Must be a valid calendar date
  - Must be >= Start Date
- **Error handling**: If End Date < Start Date, both dates are re-collected

### 5. Confirmation
```
==================================================
  REVIEW YOUR INPUTS
==================================================
  Game Name:   Candy Crush
  Platform:    Android
  Start Date:  2024-01-01
  End Date:    2024-01-31
==================================================

✅ Is this information correct? (yes/no): yes
```
- Enter `yes` or `y` to confirm
- Enter `no` or `n` to start over
- If rejected, the entire input flow restarts

## Example Session

```
==================================================
  FRESHDESK FEEDBACK AI ANALYSIS
==================================================

📱 Enter Game Name: Subway Surfers

💻 Select Operating System:
   Options: Android, iOS, Both
   Enter OS: Both

📅 Start Date
   Format: YYYY-MM-DD (e.g., 2024-01-15)
   Enter date: 2024-01-01

📅 End Date
   Format: YYYY-MM-DD (e.g., 2024-01-15)
   Enter date: 2024-01-31

==================================================
  REVIEW YOUR INPUTS
==================================================
  Game Name:   Subway Surfers
  Platform:    Both
  Start Date:  2024-01-01
  End Date:    2024-01-31
==================================================

✅ Is this information correct? (yes/no): yes

✨ Great! Proceeding with the analysis...
```

## Error Handling Examples

### Empty Input
```
📱 Enter Game Name: 
   ❌ Error: Game name cannot be empty. Please try again.

📱 Enter Game Name: My Game
```

### Invalid OS
```
💻 Select Operating System:
   Options: Android, iOS, Both
   Enter OS: Windows
   ❌ Error: Invalid OS. Must be one of: Android, iOS, Both
   Please try again.

   Enter OS: Android
```

### Invalid Date Format
```
📅 Start Date
   Format: YYYY-MM-DD (e.g., 2024-01-15)
   Enter date: 01/15/2024
   ❌ Error: Invalid date format. Must be YYYY-MM-DD.
   Example: 2024-01-15
   Please try again.

   Enter date: 2024-01-15
```

### Invalid Date Range
```
📅 Start Date
   Format: YYYY-MM-DD (e.g., 2024-01-15)
   Enter date: 2024-01-31

📅 End Date
   Format: YYYY-MM-DD (e.g., 2024-01-15)
   Enter date: 2024-01-01

   ❌ Error: Start Date must be before or equal to End Date.
   Please enter the dates again.

📅 Start Date
   Format: YYYY-MM-DD (e.g., 2024-01-15)
   Enter date: 2024-01-01
```

## Programmatic Usage

You can also use the input handler programmatically in your code:

```python
from src.input_handler import get_validated_inputs

# Collect inputs interactively
inputs = get_validated_inputs()

# Access the values
print(f"Game: {inputs.game_name}")
print(f"OS: {inputs.os}")
print(f"Period: {inputs.start_date} to {inputs.end_date}")

# Convert to dictionary
data = inputs.to_dict()
# {'game_name': 'My Game', 'os': 'Android', 'start_date': '2024-01-01', 'end_date': '2024-01-31'}
```

## Cancelling Input Collection

Press `Ctrl+C` at any prompt to cancel the input collection:

```
📱 Enter Game Name: ^C

❌ Input collection cancelled by user.
```

## Output Format

The validated inputs are returned as a `FeedbackAnalysisInput` dataclass with:
- `game_name`: str
- `os`: str (one of: Android, iOS, Both)
- `start_date`: str (YYYY-MM-DD format)
- `end_date`: str (YYYY-MM-DD format)

You can convert it to a dictionary using the `.to_dict()` method.
