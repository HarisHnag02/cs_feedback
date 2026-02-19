#!/usr/bin/env python3
"""
Mock/Replicate Query for Word Trip Analysis
Shows exact API call and filtering for specific parameters
"""

print("\n" + "="*80)
print("  REPLICATE QUERY: Word Trip, Android, 2026-01-01 to 2026-01-10")
print("="*80 + "\n")

# Your exact parameters
print("📋 INPUT PARAMETERS:")
print("-" * 80)
print("  Game Name: Word Trip")
print("  OS: Android")
print("  Start Date: 2026-01-01")
print("  End Date: 2026-01-10")
print()

print("="*80)
print("  STAGE 1: FRESHDESK API REQUEST")
print("="*80 + "\n")

print("🔌 EXACT HTTP REQUEST:")
print("-" * 80)
print("""
METHOD: GET

URL:
https://playsimple.freshdesk.com/api/v2/tickets?per_page=100&page=1&order_by=updated_at&order_type=desc

HEADERS:
Authorization: Basic ZzNtVHFIZDlpZmFrcXFFN3lnQzpY
Content-Type: application/json

QUERY PARAMETERS:
  per_page: 100           (fetch 100 tickets per page)
  page: 1                 (start with first page)
  order_by: updated_at    (sort by update date)
  order_type: desc        (newest first)

NO FILTERS IN QUERY:
  • No status filter
  • No game filter
  • No type filter
  • No date filter

Result: Returns first 100 tickets (ALL games, ALL statuses, ALL types)
""")
print("-" * 80)

print("\n" + "="*80)
print("  STAGE 2: CLIENT-SIDE FILTERING (Python Code)")
print("="*80 + "\n")

print("For EACH ticket received from Freshdesk:\n")

print("FILTER 1: Date Range")
print("-" * 80)
print("""
Check: start_date <= ticket['updated_at'] <= end_date

Code:
  updated_at = ticket.get('updated_at')  # e.g., "2026-01-05T10:30:00Z"
  ticket_date = parse_date(updated_at)   # Convert to date object
  
  start_date = datetime.strptime('2026-01-01', '%Y-%m-%d').date()
  end_date = datetime.strptime('2026-01-10', '%Y-%m-%d').date()
  
  if not (start_date <= ticket_date <= end_date):
      REJECT this ticket

Example:
  ✅ updated_at = "2026-01-05T10:30:00Z" → PASS (Jan 5 is in range)
  ❌ updated_at = "2026-01-15T10:30:00Z" → REJECT (Jan 15 is after range)
  ❌ updated_at = "2025-12-30T10:30:00Z" → REJECT (Dec 30 is before range)
""")

print("\nFILTER 2: Game Name")
print("-" * 80)
print("""
Check: 'word trip' in ticket['custom_fields']['game'].lower()

Code:
  game_name_lower = 'word trip'
  custom_fields = ticket.get('custom_fields', {})
  game_field = str(custom_fields.get('game', '')).lower()
  
  if game_name_lower not in game_field:
      REJECT this ticket

Example:
  ✅ custom_fields['game'] = "Word Trip" → PASS
  ✅ custom_fields['game'] = "word trip" → PASS
  ❌ custom_fields['game'] = "WordSearch" → REJECT
  ❌ custom_fields['game'] = "Candy Crush" → REJECT
""")

print("\nFILTER 3: Type = Feedback")
print("-" * 80)
print("""
Check: ticket['type'] == 'Feedback'

Code:
  ticket_type = ticket.get('type')
  
  if ticket_type != 'Feedback':
      REJECT this ticket

Example:
  ✅ type = "Feedback" → PASS
  ❌ type = "Question" → REJECT
  ❌ type = "Bug" → REJECT
  ❌ type = "Incident" → REJECT

Note: Type is in main ticket object, not custom_fields
""")

print("\n" + "="*80)
print("  STAGE 3: SAVE TO LOCAL")
print("="*80 + "\n")

print("Filename:")
print("  data/raw/Feedback_Word_Trip_Android_2026-01-01_to_2026-01-10.json\n")

print("Contains: All Feedback tickets for Word Trip in date range")
print("  • All statuses (Open, Pending, Resolved, Closed, Waiting)")
print("  • All OS (Android + iOS)")
print("  • Only Type = Feedback")
print("  • Fields: id, subject, description, custom_fields, etc.\n")

print("="*80)
print("  STAGE 4: AI CLASSIFIER FILTER")
print("="*80 + "\n")

print("FILTER 4: OS = Android")
print("-" * 80)
print("""
Check: 'android' in ticket['custom_fields']['os'].lower()

Code:
  os_filter = 'Android'
  os_field = str(custom_fields.get('os', ''))
  
  if os_filter.lower() not in os_field.lower():
      REJECT this ticket

Example:
  ✅ custom_fields['os'] = "Android" → PASS
  ✅ custom_fields['os'] = "android" → PASS
  ❌ custom_fields['os'] = "iOS" → REJECT

Only Android tickets sent to ChatGPT.
""")

print("\n" + "="*80)
print("  COMPLETE EXAMPLE")
print("="*80 + "\n")

print("Sample Ticket Journey:\n")

print("📥 RECEIVED FROM FRESHDESK:")
print("-" * 80)
print("""{
  "id": 1462192,
  "subject": "Feedback on WordTrip level 50",
  "description_text": "Love the game but level 50 is too hard",
  "type": "Feedback",
  "status": 5,
  "updated_at": "2026-01-05T10:30:00Z",
  "custom_fields": {
    "game": "Word Trip",
    "os": "Android"
  }
}
""")

print("🔍 FILTERING CHECKS:")
print("-" * 80)
print("""
✅ Filter 1 (Date):
   updated_at = 2026-01-05
   Range: 2026-01-01 to 2026-01-10
   Result: PASS (Jan 5 is in range)

✅ Filter 2 (Game):
   custom_fields['game'] = "Word Trip"
   Looking for: "word trip"
   Result: PASS ("word trip" in "word trip")

✅ Filter 3 (Type):
   ticket['type'] = "Feedback"
   Looking for: "Feedback"
   Result: PASS (exact match)

✅ SAVED TO LOCAL FILE

✅ Filter 4 (OS - in AI step):
   custom_fields['os'] = "Android"
   Looking for: "android"
   Result: PASS (android in android)

✅ SENT TO CHATGPT FOR ANALYSIS
""")

print("="*80)
print("  FILTERING SUMMARY")
print("="*80 + "\n")

print("""
100 tickets from Freshdesk
   ↓ Date filter (2026-01-01 to 2026-01-10)
30 tickets in date range
   ↓ Game filter (Word Trip)
5 Word Trip tickets
   ↓ Type filter (Feedback)
3 Feedback tickets
   ↓ SAVE TO LOCAL (all statuses, all OS)
3 tickets saved
   ↓ OS filter (Android)
2 Android tickets
   ↓ SEND TO CHATGPT
2 tickets classified
""")

print("="*80)
print("\n")
