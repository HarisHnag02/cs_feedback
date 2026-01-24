# Freshdesk Search API Usage

## Updated Implementation

The system now uses Freshdesk's **Search API** instead of the regular Tickets API for better server-side filtering.

## API Endpoint

**OLD:** `GET /api/v2/tickets?per_page=100&page=1`  
**NEW:** `GET /api/v2/search/tickets?query="type:Feedback AND status:5"&page=1`

## Search Query

```
"type:Feedback AND status:5"
```

This query is sent to Freshdesk and filtering happens **on the server** for:
- ✅ Type = Feedback
- ✅ Status = 5 (Closed)

## Client-Side Filtering

After receiving results from Search API, we filter for:
- ✅ Date range (created_at between start and end dates)
- ✅ Game name (custom_fields['game_name'] contains your input)
- ✅ OS (custom_fields['os'] or ['platform'] contains Android/iOS)

## Benefits

1. **Server-side filtering** - Freshdesk does Type and Status filtering
2. **Fewer API calls** - Only relevant tickets returned
3. **Better performance** - Less data to transfer and process
4. **More accurate** - Uses Freshdesk's query syntax

## Example Query

For: Game="Word Trip", OS="Android", Dates="2026-01-10 to 2026-01-14"

```
Search API: /api/v2/search/tickets?query="type:Feedback AND status:5"&page=1

Then filter results by:
  - created_at in 2026-01-10 to 2026-01-14
  - custom_fields['game_name'] contains "word trip"
  - custom_fields['os'] contains "android"
```

This is much more efficient than the old approach!
