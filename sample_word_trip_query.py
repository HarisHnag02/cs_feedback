#!/usr/bin/env python3
"""
Sample API queries for Word Trip game analysis.

This shows the exact queries that would be generated for:
- Game: Word Trip
- OS: Android
- Dates: 2024-01-01 to 2024-01-31
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.input_handler import FeedbackAnalysisInput
from src.context_loader import GameFeatureContext
from src.ai_classifier import build_classification_prompt


def print_section(title: str):
    """Print formatted section."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


# Create sample parameters for Word Trip
params = FeedbackAnalysisInput(
    game_name="Word Trip",
    os="Android",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

print_section("SAMPLE QUERIES FOR WORD TRIP (ANDROID)")

print("📋 Input Parameters:")
print(f"   Game Name: {params.game_name}")
print(f"   OS: {params.os}")
print(f"   Start Date: {params.start_date}")
print(f"   End Date: {params.end_date}")

# ============================================================================
# FRESHDESK API QUERY
# ============================================================================
print_section("1. FRESHDESK API QUERY")

print("🔌 HTTP Request:")
print("-" * 80)
print("METHOD: GET")
print()
print("URL:")
print("https://yourcompany.freshdesk.com/api/v2/tickets")
print()
print("QUERY PARAMETERS:")
print("  ?per_page=100")
print("  &page=1")
print("  &order_by=created_at")
print("  &order_type=desc")
print()
print("FULL URL:")
print("https://yourcompany.freshdesk.com/api/v2/tickets?per_page=100&page=1&order_by=created_at&order_type=desc")
print("-" * 80)

print("\n🔐 AUTHENTICATION:")
print("-" * 80)
print("Header: Authorization")
print("Type: Basic Auth")
print("Username: g3mTqHd9ifakqqE7ygC  (your Freshdesk API key)")
print("Password: X")
print()
print("Encoded as:")
print("Authorization: Basic " + "ZzNtVHFIZDlpZmFrcXFFN3lnQzpY")
print("-" * 80)

print("\n📝 REQUEST HEADERS:")
print("-" * 80)
print("Content-Type: application/json")
print("Authorization: Basic ZzNtVHFIZDlpZmFrcXFFN3lnQzpY")
print("-" * 80)

print("\n📊 RESPONSE (Sample):")
print("-" * 80)
print("""[
  {
    "id": 10001,
    "subject": "Word Trip crashes on level 100",
    "description": "<p>The game crashes when I complete level 100.</p>",
    "description_text": "The game crashes when I complete level 100.",
    "status": 4,
    "priority": 3,
    "type": "Feedback",
    "created_at": "2024-01-15T09:30:00Z",
    "updated_at": "2024-01-20T14:00:00Z",
    "tags": ["android", "bug", "crash"],
    "custom_fields": {
      "game_name": "Word Trip",
      "os": "Android",
      "version": "1.5.2"
    }
  },
  {
    "id": 10002,
    "subject": "Love the daily puzzles!",
    "description": "<p>Great game, play it every day!</p>",
    "description_text": "Great game, play it every day!",
    "status": 5,
    "priority": 1,
    "type": "Feedback",
    "created_at": "2024-01-16T14:20:00Z",
    "tags": ["android", "positive"],
    "custom_fields": {
      "game_name": "Word Trip",
      "os": "Android"
    }
  }
  // ... more tickets up to 100 per page
]""")
print("-" * 80)

print("\n🔍 CLIENT-SIDE FILTERS APPLIED (After fetching):")
print("-" * 80)
print("After getting tickets from Freshdesk, the system will:")
print()
print("1. ✅ Check Status:")
print("   KEEP if: status == 4 (Resolved) OR status == 5 (Closed)")
print("   REJECT if: status == 2 (Open), 3 (Pending), or other")
print()
print("2. ✅ Check Type:")
print("   KEEP if: type == 'Feedback' OR 'feedback' in tags OR type is None")
print("   REJECT if: type is something else and no feedback tag")
print()
print("3. ✅ Check Date Range:")
print(f"   KEEP if: {params.start_date} <= created_at <= {params.end_date}")
print("   REJECT if: outside this date range")
print()
print("4. ✅ Check Game Name:")
print(f"   KEEP if: '{params.game_name.lower()}' found in:")
print("     • subject (case-insensitive)")
print("     • description_text (case-insensitive)")
print("     • custom_fields['game_name']")
print("     • custom_fields['game']")
print("     • custom_fields['product']")
print("   REJECT if: game name not found anywhere")
print()
print("5. ✅ Check OS:")
print(f"   KEEP if: '{params.os.lower()}' found in:")
print("     • subject (case-insensitive)")
print("     • description_text (case-insensitive)")
print("     • custom_fields['os']")
print("     • custom_fields['platform']")
print("     • custom_fields['device_type']")
print(f"   (OS filter skipped if OS='Both')")
print("-" * 80)

# ============================================================================
# OPENAI API QUERY
# ============================================================================
print_section("2. OPENAI API QUERY (Per Ticket)")

print("🔌 HTTP Request:")
print("-" * 80)
print("METHOD: POST")
print()
print("URL:")
print("https://api.openai.com/v1/chat/completions")
print()
print("HEADERS:")
print("  Authorization: Bearer sk-proj-7OQl6iL...wIgtGzoA")
print("  Content-Type: application/json")
print("-" * 80)

print("\n📦 REQUEST BODY:")
print("-" * 80)
print("""{
  "model": "gpt-4-turbo-preview",
  "temperature": 0,
  "response_format": {"type": "json_object"},
  "messages": [
    {
      "role": "system",
      "content": "You are an expert game feedback analyst. Always respond with valid JSON."
    },
    {
      "role": "user",
      "content": "<PROMPT SHOWN BELOW>"
    }
  ]
}""")
print("-" * 80)

print("\n📝 COMPLETE AI PROMPT (Example for one ticket):")
print("-" * 80)

# Sample cleaned ticket
sample_ticket = {
    'subject': 'Word Trip crashes on level 100',
    'clean_feedback': 'The game crashes when I try to complete level 100. Very frustrating! I have tried clearing cache but issue persists.'
}

# Sample game context for Word Trip
sample_context = GameFeatureContext(
    game_name="Word Trip",
    current_features=[
        "Word puzzle game with 3000+ levels",
        "Daily puzzle challenges",
        "Hint system to help solve difficult words",
        "Offline play capability",
        "Cross-word style gameplay"
    ],
    known_constraints=[
        "Performance issues on Android devices with less than 2GB RAM",
        "Level data cached locally for offline play"
    ],
    recent_changes=[
        "v1.5.2 (Jan 2024): Added new daily challenge feature",
        "v1.5.0 (Dec 2023): Performance improvements for Android 14"
    ]
)

# Build the actual prompt
prompt = build_classification_prompt(
    sample_ticket['clean_feedback'],
    sample_ticket['subject'],
    sample_context
)

print(prompt)
print("-" * 80)

print("\n✅ EXPECTED AI RESPONSE (Strict JSON):")
print("-" * 80)
print("""{
  "ticket_id": 10001,
  "category": "Bug",
  "subcategory": "Crash/Freeze",
  "sentiment": "Negative",
  "intent": "Report Bug",
  "confidence": 0.95,
  "key_points": [
    "Game crashes on level 100",
    "Issue persists after clearing cache",
    "Causing player frustration"
  ],
  "short_summary": "Player reports crash on level 100, persists after troubleshooting",
  "is_expected_behavior": false,
  "related_feature": "Level progression system"
}""")
print("-" * 80)

# ============================================================================
# COMPLETE WORKFLOW
# ============================================================================
print_section("3. COMPLETE API CALL SEQUENCE FOR WORD TRIP")

print("📊 Full Workflow:")
print()
print("STEP 1: User Input")
print("  ↓ Game: Word Trip, OS: Android, Dates: 2024-01-01 to 2024-01-31")
print()
print("STEP 2: Cache Check")
print("  ↓ Check: data/raw/Feedback_Word_Trip_Android_2024-01-01_to_2024-01-31.json")
print("  ↓ Result: MISS (first run)")
print()
print("STEP 3: Freshdesk API Call #1 (Connection Test)")
print("  ↓ GET https://yourcompany.freshdesk.com/api/v2/tickets?per_page=1")
print("  ↓ Auth: Basic ZzNtVHFIZDlpZmFrcXFFN3lnQzpY")
print("  ↓ Response: 1 ticket (connection OK)")
print()
print("STEP 4: Freshdesk API Call #2 (Page 1)")
print("  ↓ GET https://yourcompany.freshdesk.com/api/v2/tickets?per_page=100&page=1")
print("  ↓ Response: 100 tickets")
print("  ↓ Apply filters →  X tickets match (you'll see this number)")
print()
print("STEP 5: Freshdesk API Call #3 (Page 2, if needed)")
print("  ↓ GET https://yourcompany.freshdesk.com/api/v2/tickets?per_page=100&page=2")
print("  ↓ Response: 100 tickets")
print("  ↓ Apply filters → Y tickets match")
print("  ↓ ... continues until no more tickets")
print()
print("STEP 6: Save to Cache")
print("  ↓ Save all filtered tickets to data/raw/")
print()
print("STEP 7: Data Cleaning")
print("  ↓ Remove HTML, signatures, auto-replies from each ticket")
print()
print("STEP 8: Load Game Context")
print("  ↓ Load context/game_features.yaml")
print()
print("STEP 9: OpenAI API Calls (One per ticket)")
print("  ↓ For each of the X filtered tickets:")
print("  ↓   POST https://api.openai.com/v1/chat/completions")
print("  ↓   Body: {model: gpt-4-turbo-preview, temperature: 0, messages: [...]}")
print("  ↓   Response: Classification JSON")
print()
print("STEP 10: Aggregate & Generate Reports")
print("  ↓ Group by category, detect patterns")
print("  ↓ Generate Markdown + JSON reports")
print()

print("💰 ESTIMATED COSTS:")
print(f"  Freshdesk API: FREE (2-3 calls)")
print(f"  OpenAI API: ~$X (depends on filtered ticket count)")
print()
print("⏱️  ESTIMATED TIME:")
print(f"  5-10 minutes total")

print("\n" + "="*80)
print("✅ This is the exact query structure for Word Trip analysis")
print("="*80 + "\n")
