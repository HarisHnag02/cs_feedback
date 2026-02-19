#!/usr/bin/env python3
"""
Mock Query Generator - Shows exact query without running full application
"""

print("\n" + "="*80)
print("  MOCK QUERY FOR WORD TRIP ANALYSIS")
print("="*80 + "\n")

# Mock parameters (you can change these)
GAME_NAME = "Word Trip"
OS = "Android"
START_DATE = "2026-02-01"
END_DATE = "2026-02-19"
DOMAIN = "playsimple.freshdesk.com"
API_KEY = "g3mTqHd9ifakqqE7ygC"

print("📋 PARAMETERS:")
print(f"  Game: {GAME_NAME}")
print(f"  OS: {OS}")
print(f"  Start Date: {START_DATE}")
print(f"  End Date: {END_DATE}")
print()

print("="*80)
print("  EXACT HTTP REQUEST TO FRESHDESK")
print("="*80 + "\n")

endpoint = "/api/v2/tickets"
params = "per_page=100&page=1&order_by=updated_at&order_type=desc"

print("🔌 HTTP REQUEST:")
print("-" * 80)
print(f"""
METHOD: GET

FULL URL:
https://{DOMAIN}{endpoint}?{params}

HEADERS:
  Authorization: Basic ZzNtVHFIZDlpZmFrcXFFN3lnQzpY  (base64({API_KEY}:X))
  Content-Type: application/json

QUERY PARAMETERS:
  per_page=100              → Fetch 100 tickets at a time
  page=1                    → Start with page 1
  order_by=updated_at       → Sort by update date
  order_type=desc           → Newest first

NO FILTERS IN URL:
  • Fetches ALL tickets (all games, all statuses, all types)
  • Filtering happens in Python after receiving response
""")
print("-" * 80)

print("\n" + "="*80)
print("  CLIENT-SIDE FILTERING (Python Code)")
print("="*80 + "\n")

print("For EACH ticket in the response, apply these filters:\n")

print("FILTER 1: Date Range")
print("-" * 80)
print(f"""
Python Code:
  updated_at = ticket['updated_at']  # e.g., "2026-02-15T10:30:00Z"
  ticket_date = datetime.fromisoformat(updated_at).date()
  
  start = datetime.strptime('{START_DATE}', '%Y-%m-%d').date()
  end = datetime.strptime('{END_DATE}', '%Y-%m-%d').date()
  
  if not (start <= ticket_date <= end):
      REJECT

Matches:
  ✅ updated_at: "2026-02-15T10:30:00Z" (Feb 15 - in range)
  ✅ updated_at: "2026-02-01T08:00:00Z" (Feb 1 - in range)
  ❌ updated_at: "2026-01-20T10:00:00Z" (Jan 20 - before range)
  ❌ updated_at: "2026-02-25T10:00:00Z" (Feb 25 - after range)
""")

print("\nFILTER 2: Game Name")
print("-" * 80)
print(f"""
Python Code:
  game_name_lower = '{GAME_NAME.lower()}'
  custom_fields = ticket['custom_fields']
  game_field = str(custom_fields.get('game', '')).lower()
  
  if game_name_lower not in game_field:
      REJECT

Field Used: custom_fields['game']  (lowercase 'game')

Matches:
  ✅ custom_fields['game'] = "Word Trip"
  ✅ custom_fields['game'] = "word trip"
  ✅ custom_fields['game'] = "WORD TRIP"
  ❌ custom_fields['game'] = "WordSearch"
  ❌ custom_fields['game'] = "Candy Crush"
  ❌ No custom_fields
""")

print("\nFILTER 3: Type = Feedback")
print("-" * 80)
print(f"""
Python Code:
  ticket_type = ticket['type']
  
  if ticket_type != 'Feedback':
      REJECT

Field Used: ticket['type']  (main object, not custom_fields)

Matches:
  ✅ type = "Feedback"
  ❌ type = "Question"
  ❌ type = "Bug"
  ❌ type = "Incident"
  ❌ type = None
""")

print("\n" + "="*80)
print("  WHAT GETS SAVED TO LOCAL")
print("="*80 + "\n")

filename = f"Feedback_Word_Trip_{OS}_{START_DATE}_to_{END_DATE}.json"
print(f"File: data/raw/{filename}\n")

print("Contains: ALL Feedback tickets for Word Trip in date range")
print("  • All statuses (Open, Pending, Resolved, Closed, Waiting)")
print("  • All OS (Android + iOS)")
print("  • Only Type = Feedback")
print()

print("Sample ticket structure saved:")
print("-" * 80)
print("""{
  "ticket_id": 1462192,
  "subject": "Feedback on WordTrip level 50",
  "clean_feedback": "Love the game but level 50 is too hard",
  "created_date": "2026-02-15T10:30:00Z",
  "status": 5,
  "priority": 1,
  "tags": ["version-78", "issue-Feedback"],
  "metadata": {
    "type": "Feedback",
    "status": 5,
    "custom_fields": {
      "game": "Word Trip",
      "os": "Android",
      "version": "1.2.3"
    },
    "original_length": 150,
    "cleaned_length": 45,
    "reduction_ratio": 70.0
  }
}
""")

print("\n" + "="*80)
print("  AI CLASSIFIER FILTER (Before ChatGPT)")
print("="*80 + "\n")

print(f"FILTER 4: OS = {OS}")
print("-" * 80)
print(f"""
Python Code:
  os_filter = '{OS}'
  os_field = str(custom_fields.get('os', ''))
  
  if '{OS.lower()}' not in os_field.lower():
      DON'T SEND TO CHATGPT

Field Used: custom_fields['os']  (lowercase 'os')

For OS = "Android":
  ✅ custom_fields['os'] = "Android" → SEND TO CHATGPT
  ✅ custom_fields['os'] = "android" → SEND TO CHATGPT
  ❌ custom_fields['os'] = "iOS" → SKIP

Only {OS} tickets sent to ChatGPT for classification.
""")

print("\n" + "="*80)
print("  COMPLETE FLOW SUMMARY")
print("="*80 + "\n")

print(f"""
API Call:
  GET https://{DOMAIN}/api/v2/tickets?per_page=100&page=1

Response: 100 tickets (example)

Filter 1 (Date {START_DATE} to {END_DATE}):
  100 → 80 tickets (20 outside date range)

Filter 2 (Game = {GAME_NAME}):
  80 → 12 tickets (68 other games)

Filter 3 (Type = Feedback):
  12 → 8 tickets (4 Questions/Bugs)

SAVED: 8 Feedback tickets for {GAME_NAME}
  File: data/raw/{filename}
  Includes: All statuses, All OS (Android + iOS)

Filter 4 (OS = {OS}):
  8 → 5 tickets (3 iOS filtered out)

SENT TO CHATGPT: 5 Feedback+{OS} tickets

REPORTS: Generated based on 5 classified tickets
""")

print("="*80)
print("\n✅ This is the exact query and filtering logic used!")
print("   Run 'python main.py' with recent dates to see real results.\n")
print("="*80 + "\n")
