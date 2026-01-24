# Freshdesk API Client Documentation

## Overview

The Freshdesk API client (`src/freshdesk_client.py`) provides a robust interface for fetching feedback tickets from Freshdesk with strict filtering capabilities. It handles authentication, pagination, rate limiting, and error handling.

## Features

✅ **Strict Filtering**
- Type: Feedback only
- Status: Closed/Resolved tickets
- Date range: Between start and end dates
- Game name: Matches user input
- OS/Platform: Android, iOS, or Both

✅ **Pagination Handling**
- Automatic pagination through multiple pages
- Safety limits to prevent infinite loops
- Efficient batching (100 tickets per page)

✅ **Error Handling**
- HTTP error handling with detailed messages
- Rate limiting with automatic retry
- Timeout handling
- Connection testing

✅ **Authentication**
- HTTP Basic Auth using API key
- Secure credential management from environment variables

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Required: Your Freshdesk API key
FRESHDESK_API_KEY=your_api_key_here

# Required: Your Freshdesk domain
FRESHDESK_DOMAIN=yourcompany.freshdesk.com

# Optional: Logging level
LOG_LEVEL=INFO
```

### Getting Your Freshdesk API Key

1. Log in to your Freshdesk account
2. Click on your profile picture (top right)
3. Go to **Profile Settings**
4. Your API key is displayed in the right sidebar under "Your API Key"
5. Click "Copy" or manually copy the key

### Finding Your Freshdesk Domain

Your domain is the part before `.freshdesk.com` in your Freshdesk URL.

Example:
- URL: `https://acmecompany.freshdesk.com/`
- Domain: `acmecompany.freshdesk.com`

## API Reference

### FreshdeskClient Class

Main client class for interacting with Freshdesk API.

#### Initialization

```python
from src.freshdesk_client import FreshdeskClient

# Uses credentials from .env file
client = FreshdeskClient()

# Or provide explicitly
client = FreshdeskClient(
    domain="yourcompany.freshdesk.com",
    api_key="your_api_key"
)
```

#### Methods

##### `test_connection() -> bool`

Test the API connection and authentication.

```python
if client.test_connection():
    print("Connection successful!")
else:
    print("Connection failed!")
```

**Returns:** `True` if successful, `False` otherwise

##### `fetch_feedback_tickets(input_params, max_pages=10) -> List[Dict]`

Fetch feedback tickets with strict filtering.

**Parameters:**
- `input_params` (FeedbackAnalysisInput): Filter criteria
- `max_pages` (int): Maximum pages to fetch (default: 10)

**Returns:** List of ticket dictionaries

**Example:**
```python
from src.input_handler import FeedbackAnalysisInput

params = FeedbackAnalysisInput(
    game_name="Candy Crush",
    os="Android",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

tickets = client.fetch_feedback_tickets(params)
print(f"Found {len(tickets)} tickets")
```

##### `get_ticket_by_id(ticket_id) -> Dict`

Fetch a single ticket by ID.

**Parameters:**
- `ticket_id` (int): Freshdesk ticket ID

**Returns:** Ticket data as dictionary

**Example:**
```python
ticket = client.get_ticket_by_id(12345)
print(ticket['subject'])
```

### High-Level Function

##### `fetch_feedback_data(input_params) -> Dict`

High-level function that fetches and structures feedback data.

**Parameters:**
- `input_params` (FeedbackAnalysisInput): Filter criteria

**Returns:** Dictionary with metadata and feedbacks

**Example:**
```python
from src.freshdesk_client import fetch_feedback_data
from src.input_handler import FeedbackAnalysisInput

params = FeedbackAnalysisInput(
    game_name="Subway Surfers",
    os="iOS",
    start_date="2024-02-01",
    end_date="2024-02-29"
)

data = fetch_feedback_data(params)

print(f"Total tickets: {len(data['feedbacks'])}")
print(f"Fetched at: {data['metadata']['fetched_at']}")
```

**Return Structure:**
```python
{
    'metadata': {
        'game_name': 'Candy Crush',
        'os': 'Android',
        'start_date': '2024-01-01',
        'end_date': '2024-01-31',
        'fetched_at': '2024-01-24T10:30:00',
        'total_records': 150,
        'source': 'freshdesk_api',
        'domain': 'yourcompany.freshdesk.com'
    },
    'feedbacks': [
        {
            'id': 1001,
            'subject': 'Great game!',
            'description': '...',
            'status': 4,
            'created_at': '2024-01-15T09:30:00Z',
            # ... other ticket fields
        },
        # ... more tickets
    ]
}
```

## Filtering Logic

### STRICT Filters Applied

The client applies the following strict filters:

#### 1. Type Filter
```python
# Must be a Feedback ticket
ticket_type == 'Feedback' OR 'feedback' in tags
```

#### 2. Status Filter
```python
# Must be Closed or Resolved
status in [4, 5]  # 4=Resolved, 5=Closed
```

#### 3. Date Range Filter
```python
# Created date must be within range
start_date <= ticket_created_date <= end_date
```

#### 4. Game Name Filter
```python
# Game name must appear in subject, description, or custom fields
game_name.lower() in subject.lower() OR
game_name.lower() in description.lower() OR
game_name.lower() in custom_fields['game_name'].lower()
```

#### 5. OS/Platform Filter
```python
# If OS != 'Both', must match the platform
os.lower() in subject.lower() OR
os.lower() in description.lower() OR
os.lower() in custom_fields['os'].lower() OR
os.lower() in custom_fields['platform'].lower()
```

### Two-Stage Filtering

1. **API-Level Filtering**: Basic filters sent to Freshdesk API
2. **Client-Side Filtering**: Strict additional filters applied locally

This ensures ALL tickets returned match ALL criteria exactly.

## Pagination

### How It Works

```python
# Fetch up to 1000 tickets (10 pages × 100 per page)
tickets = client.fetch_feedback_tickets(params, max_pages=10)
```

The client:
1. Fetches 100 tickets per page (Freshdesk maximum)
2. Continues until no more tickets or max_pages reached
3. Adds small delays between requests (0.5s) to be API-friendly
4. Stops early if fewer than 100 tickets returned (last page)

### Safety Limits

- **Default max_pages**: 10 (max 1000 tickets)
- **Configurable**: Pass `max_pages` parameter to adjust
- **Prevents**: Infinite loops and excessive API calls

## Error Handling

### FreshdeskAPIError Exception

Custom exception for all Freshdesk API errors.

```python
from src.freshdesk_client import FreshdeskAPIError

try:
    data = fetch_feedback_data(params)
except FreshdeskAPIError as e:
    print(f"API error: {e}")
```

### Common Errors

#### 1. Authentication Error (401)
```
Error: HTTP error occurred: 401 Client Error: Unauthorized
```

**Solution:**
- Check `FRESHDESK_API_KEY` in `.env`
- Verify API key is correct
- Ensure API key has proper permissions

#### 2. Domain Not Found (404)
```
Error: HTTP error occurred: 404 Client Error: Not Found
```

**Solution:**
- Check `FRESHDESK_DOMAIN` in `.env`
- Ensure domain is correct (e.g., `yourcompany.freshdesk.com`)
- Verify account is active

#### 3. Rate Limiting (429)
```
Warning: Rate limited. Retrying after 60 seconds...
```

**Automatic Handling:**
- Client automatically waits and retries
- Uses `Retry-After` header from response
- No action needed from user

#### 4. Timeout Error
```
Error: Request timeout: HTTPSConnectionPool...
```

**Solution:**
- Check internet connection
- Verify Freshdesk service is accessible
- Try again later

## Integration with Storage Manager

### Complete Workflow

```python
from src.input_handler import get_validated_inputs
from src.freshdesk_client import fetch_feedback_data
from src import storage_manager

# 1. Get user inputs
params = get_validated_inputs()

# 2. Check cache first
if storage_manager.exists(params):
    # Use cached data
    data = storage_manager.load(params)
    print("Using cached data")
else:
    # Fetch from Freshdesk
    data = fetch_feedback_data(params)
    
    # Save to cache
    storage_manager.save(params, data)
    print("Fetched fresh data and cached")

# 3. Process data
print(f"Processing {len(data['feedbacks'])} tickets...")
```

## Testing

### Run Test Suite

```bash
# Comprehensive test suite
python test_freshdesk_client.py

# Direct module test
python -m src.freshdesk_client
```

### Test Coverage

The test suite includes:
- ✅ Client initialization
- ✅ Connection testing
- ✅ Ticket fetching with various filters
- ✅ Pagination handling
- ✅ Error handling (invalid key, invalid domain)
- ✅ Data structure validation

### Manual Testing

```python
from src.freshdesk_client import FreshdeskClient

# Initialize and test
client = FreshdeskClient()

# Test connection
if client.test_connection():
    print("✓ Connected successfully!")

# Fetch sample
from src.input_handler import FeedbackAnalysisInput

params = FeedbackAnalysisInput(
    game_name="Test Game",
    os="Both",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

tickets = client.fetch_feedback_tickets(params, max_pages=1)
print(f"Found {len(tickets)} tickets")
```

## Ticket Data Structure

### Common Ticket Fields

```python
{
    'id': 12345,                          # Ticket ID
    'subject': 'Bug in level 5',          # Ticket subject
    'description': 'Full description...',  # HTML description
    'description_text': 'Plain text...',   # Plain text description
    'status': 4,                          # Status code (4=Resolved, 5=Closed)
    'priority': 2,                        # Priority (1=Low, 2=Medium, 3=High, 4=Urgent)
    'type': 'Feedback',                   # Ticket type
    'created_at': '2024-01-15T09:30:00Z', # Creation timestamp
    'updated_at': '2024-01-20T14:22:00Z', # Last update timestamp
    'tags': ['feedback', 'bug'],          # Tags
    'custom_fields': {                    # Custom fields (varies by setup)
        'game_name': 'Candy Crush',
        'os': 'Android',
        'platform': 'Mobile'
    },
    # ... many more fields
}
```

### Accessing Ticket Data

```python
for ticket in data['feedbacks']:
    ticket_id = ticket.get('id')
    subject = ticket.get('subject', 'No subject')
    created = ticket.get('created_at')
    
    # Custom fields
    custom = ticket.get('custom_fields', {})
    game = custom.get('game_name', 'Unknown')
    os = custom.get('os', 'Unknown')
    
    print(f"#{ticket_id}: {subject} - {game} ({os})")
```

## Performance Considerations

### API Rate Limits

Freshdesk typically limits API calls:
- **Free/Trial**: ~1000 requests/hour
- **Paid Plans**: Higher limits

The client:
- Adds 0.5s delay between page fetches
- Handles 429 errors automatically
- Uses efficient pagination

### Optimization Tips

1. **Use caching**: Always check `storage_manager.exists()` first
2. **Limit date ranges**: Smaller ranges = fewer tickets to filter
3. **Adjust max_pages**: Don't fetch more than needed
4. **Batch processing**: Process tickets in chunks for large datasets

## Troubleshooting

### No Tickets Found

If `fetch_feedback_tickets()` returns empty list:

1. **Check filters are correct**:
   - Game name matches exactly (case-insensitive)
   - Date range includes ticket creation dates
   - OS filter is appropriate

2. **Verify ticket properties**:
   - Tickets are marked as "Feedback" type
   - Tickets are "Closed" or "Resolved"
   - Custom fields contain expected data

3. **Test with broader filters**:
   ```python
   # Try with 'Both' OS and wider date range
   params.os = "Both"
   params.start_date = "2023-01-01"
   params.end_date = "2024-12-31"
   ```

### Slow Fetching

If fetching is slow:

1. **Reduce date range**: Smaller ranges fetch faster
2. **Lower max_pages**: Limit pagination depth
3. **Check network**: Verify connection speed
4. **Monitor rate limits**: May be hitting rate limits

### Data Not Matching Expectations

If ticket data doesn't look right:

1. **Check custom field names**: May differ from defaults
2. **Examine raw ticket**: Use `get_ticket_by_id()` to inspect
3. **Update filter logic**: Adjust `_filter_tickets_by_criteria()`
4. **Contact Freshdesk**: Verify API version and fields

## Best Practices

1. ✅ **Always test connection first**
   ```python
   if not client.test_connection():
       print("Connection failed!")
       return
   ```

2. ✅ **Use caching**
   ```python
   if storage_manager.exists(params):
       data = storage_manager.load(params)
   ```

3. ✅ **Handle errors gracefully**
   ```python
   try:
       data = fetch_feedback_data(params)
   except FreshdeskAPIError as e:
       logger.error(f"API error: {e}")
   ```

4. ✅ **Log operations**
   ```python
   logger.info(f"Fetching tickets for {params.game_name}")
   ```

5. ✅ **Validate data**
   ```python
   if not data['feedbacks']:
       print("No tickets found - check filters")
   ```

## Next Steps

After fetching Freshdesk data:
1. Process with OpenAI for sentiment analysis
2. Generate reports in JSON and Markdown formats
3. Store processed results

See main application workflow in `main.py` for complete integration.
