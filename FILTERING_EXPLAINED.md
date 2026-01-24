# 🔍 How Filtering Works - Step by Step

## Overview

The system fetches tickets from Freshdesk, then applies **5 strict filters** one by one. A ticket must pass **ALL 5 filters** to be included in the analysis.

---

## 📋 The 5 Filters (Applied in Order)

### **Filter 1: Status Check** ✅ **ONLY Status 5 (Closed)**

**Location:** `src/freshdesk_client.py` lines 162-166

```python
status = ticket.get('status')
if status != 5:  # Only Closed
    continue  # REJECT this ticket
```

**What it does:**
- Gets the `status` field from the ticket
- Checks if it equals `5` (Closed)
- If not 5, **REJECT** the ticket immediately

**Freshdesk Status Values:**
- `2` = Open → ❌ REJECTED
- `3` = Pending → ❌ REJECTED
- `4` = Resolved → ❌ REJECTED
- `5` = Closed → ✅ ACCEPTED

**Example:**
```json
{
  "id": 12345,
  "status": 5,  ← Checking this
  ...
}
```
- If status is `5` → Continue to Filter 2
- If status is anything else → Stop, reject ticket

---

### **Filter 2: Type Check** ✅ **Must be "Feedback"**

**Location:** `src/freshdesk_client.py` lines 168-182

```python
ticket_type = ticket.get('type')
tags = ticket.get('tags', [])

is_feedback = (
    ticket_type == 'Feedback' or
    'feedback' in [tag.lower() for tag in tags] or
    'Feedback' in tags
)

if not is_feedback:
    continue  # REJECT
```

**What it does:**
- Checks the `type` field
- Checks all `tags` for "feedback" or "Feedback"
- Accepts if ANY of these are true:
  1. `type` field equals "Feedback" (exact match)
  2. Any tag lowercased equals "feedback"
  3. Any tag exactly equals "Feedback"

**Example Accepted:**
```json
{
  "id": 12345,
  "type": "Feedback",  ← Match! PASS
  "tags": []
}
```

**Example Accepted (via tag):**
```json
{
  "id": 12346,
  "type": null,
  "tags": ["bug", "feedback", "android"]  ← Has "feedback" tag! PASS
}
```

**Example Rejected:**
```json
{
  "id": 12347,
  "type": "Question",  ← Not "Feedback"
  "tags": ["support"]  ← No "feedback" tag
}
```
→ ❌ REJECTED

---

### **Filter 3: Date Range** ✅ **Must be within specified dates**

**Location:** `src/freshdesk_client.py` lines 184-205

```python
created_at = ticket.get('created_at')
ticket_date = parse_date(created_at)  # Converts to date object

start_date = parse('2026-01-10')
end_date = parse('2026-01-14')

if not (start_date <= ticket_date <= end_date):
    continue  # REJECT
```

**What it does:**
- Parses the `created_at` timestamp
- Converts your input dates to date objects
- Checks if ticket date is within the range (inclusive)

**Example:**
```
Your input: 2026-01-10 to 2026-01-14

Ticket created on 2026-01-12 → ✅ PASS (within range)
Ticket created on 2026-01-09 → ❌ REJECT (too early)
Ticket created on 2026-01-15 → ❌ REJECT (too late)
```

---

### **Filter 4: Game Name Match** ✅ **custom_fields['game_name'] ONLY**

**Location:** `src/freshdesk_client.py` lines 207-219

```python
game_name_lower = input_params.game_name.lower()  # "word trip"
game_match = False

# Check custom fields ONLY (NOT subject/description)
custom_fields = ticket.get('custom_fields', {})
if custom_fields:
    game_field = custom_fields.get('game_name', '').lower()
    if game_name_lower in game_field:
        game_match = True

if not game_match:
    continue  # REJECT
```

**What it does:**
- Converts your game name to lowercase: `"Word Trip"` → `"word trip"`
- Searches **ONLY** in:
  - custom_fields['game_name'] (lowercase)
- **DOES NOT search** in subject or description
- If found → PASS
- If not found or no custom_fields → REJECT

**Example Accepted:**
```json
{
  "subject": "Crash issue",
  "description_text": "Game freezes",
  "custom_fields": {
    "game_name": "Word Trip"  ← Contains "word trip"! PASS
  }
}
```

**Example Rejected (no custom_fields):**
```json
{
  "subject": "Word Trip crashes",  ← Has game name in subject but...
  "description_text": "...",
  "custom_fields": {}  ← No custom_fields! REJECTED
}
```
→ ❌ REJECTED (because custom_fields is empty)

**Example Rejected (wrong game):**
```json
{
  "custom_fields": {
    "game_name": "Other Game"  ← Doesn't contain "word trip"
  }
}
```
→ ❌ REJECTED

---

### **Filter 5: OS Match** ✅ **custom_fields['os'] or ['platform'] ONLY**

**Location:** `src/freshdesk_client.py` lines 221-239

```python
os_filter = input_params.os  # "Android"

if os_filter != 'Both':
    os_match = False
    
    # Check custom fields ONLY (NOT subject/description)
    if custom_fields:
        os_field = custom_fields.get('os', '')
        platform_field = custom_fields.get('platform', '')
        
        # Handle iOS variations
        if os_filter.lower() == 'ios':
            if os_field in ['ios', 'iOS', 'IOS'] or platform_field in ['ios', 'iOS', 'IOS']:
                os_match = True
        else:
            # For Android, case-insensitive match
            if os_filter.lower() in os_field.lower() or os_filter.lower() in platform_field.lower():
                os_match = True
    
    if not os_match:
        continue  # REJECT
```

**What it does:**
- Checks **ONLY** in custom_fields:
  - custom_fields['os']
  - custom_fields['platform']
- **DOES NOT search** in subject or description
- For iOS: accepts "ios", "iOS", or "IOS"
- For Android: case-insensitive match

**Example Accepted:**
```json
{
  "subject": "Crash issue",
  "custom_fields": {
    "os": "Android"  ← Match! PASS
  }
}
```

**Example Rejected (OS in subject but not custom_fields):**
```json
{
  "subject": "Word Trip Android crash",  ← Has "Android" in subject but...
  "custom_fields": {
    "os": ""  ← Empty! REJECTED
  }
}
```
→ ❌ REJECTED (because custom_fields['os'] is empty)

**Example Rejected (no custom_fields):**
```json
{
  "subject": "Word Trip iOS crash",
  "custom_fields": {}  ← No os field! REJECTED
}
```
→ ❌ REJECTED

---

## 🔄 **Complete Flow for ONE Ticket**

```
Ticket #12345 from Freshdesk
    ↓
[Filter 1] status == 5?
    ↓ YES → Continue
    ↓ NO  → REJECT (skip to next ticket)
    
[Filter 2] type == 'Feedback' OR 'feedback' in tags?
    ↓ YES → Continue
    ↓ NO  → REJECT
    
[Filter 3] 2026-01-10 <= created_at <= 2026-01-14?
    ↓ YES → Continue
    ↓ NO  → REJECT
    
[Filter 4] 'word trip' in (subject OR description OR custom_fields['game_name'])?
    ↓ YES → Continue
    ↓ NO  → REJECT
    
[Filter 5] 'android' in (subject OR description OR custom_fields['os'])?
    ↓ YES → ACCEPT! Add to filtered list
    ↓ NO  → REJECT

If ticket passes all 5 filters → Goes into your analysis
If ticket fails any filter → Skipped completely
```

---

## 🎯 **Why You're Getting 0 or Few Tickets**

Based on your logs, tickets are failing because they need **ALL conditions true**:

```
Example from logs (Page 10, line 547):
  Status (not Closed): 12      ← 12 tickets had status ≠ 5
  Type (not Feedback): 30      ← 30 tickets had no Feedback type/tag
  Date Range: 8                ← 8 tickets were outside 2026-01-10 to 2026-01-14
  Game Name: 42                ← 42 tickets didn't contain "word trip"
  OS: 8                        ← 8 tickets didn't contain "android"

Total rejected: 12+30+8+42+8 = 100 tickets (some counted multiple times)
```

**The math:** A ticket can fail multiple filters, but must pass ALL to be accepted!

---

## 💡 **To Get More Tickets, You Can:**

1. **Use "Both" for OS** - Skips OS filter entirely
2. **Widen date range** - e.g., last 3 months instead of 5 days
3. **Check your Freshdesk** - Verify tickets actually have:
   - Status = 5
   - Type = "Feedback" or tag "feedback"
   - "Word Trip" in subject/description
   - "Android" in subject/description

---

## 🧪 **Test Individual Filters**

Want to see which filter is rejecting most? The logs now show rejection breakdown!

Look for lines like:
```
Rejection breakdown:
  Status (not Closed): XX
  Type (not Feedback): XX
  Date Range: XX
  Game Name: XX
  OS: XX
```

This tells you exactly which filter is rejecting most tickets!
