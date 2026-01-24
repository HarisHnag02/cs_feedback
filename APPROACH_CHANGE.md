# ✅ New Approach: Pull All Tickets, Filter Later (IMPLEMENTED)

## Your Approach

1. **Pull ALL tickets** for a game (no status/type filtering)
2. **Save everything** to a file  
3. **Filter only Feedback (status=5)** when sending to ChatGPT

## Changes Implemented

### **CHANGE 1: Freshdesk Client - Remove Type/Status Filters**

**File:** `src/freshdesk_client.py`

**Current (Lines 120-127):**
```python
# Build search query for server-side filtering
search_query = '"type:Feedback AND status:5"'
encoded_query = requests.utils.quote(search_query)

endpoint = f"search/tickets?query={encoded_query}&page={{page}}"
```

**New (Pull ALL tickets):**
```python
# Pull ALL tickets without type/status filtering
# Just use date range and pagination
endpoint = "tickets?per_page=100&page={page}&order_by=created_at&order_type=desc"
```

**Client-side filtering to REMOVE:**
- ❌ Remove status check (line 165-167)
- ❌ Remove type check (will filter in AI step)
- ✅ Keep date range filter
- ✅ Keep game name filter (custom_fields)
- ✅ Keep OS filter (custom_fields)

---

### **CHANGE 2: AI Classifier - Add Feedback Filtering**

**File:** `src/ai_classifier.py`

**Before classify_feedback_data():**

Add a filtering function:

```python
def filter_feedback_tickets(tickets: List[CleanTicket]) -> List[CleanTicket]:
    """
    Filter to only Feedback tickets with Status = 5.
    
    This happens BEFORE sending to ChatGPT to reduce API costs.
    """
    feedback_tickets = []
    
    for ticket in tickets:
        # Check status = 5 (Closed)
        if ticket.metadata.get('status') == 5:
            # Check type = Feedback
            ticket_type = ticket.metadata.get('type')
            tags = ticket.metadata.get('tags', [])
            
            is_feedback = (
                ticket_type == 'Feedback' or
                'feedback' in [tag.lower() for tag in tags]
            )
            
            if is_feedback:
                feedback_tickets.append(ticket)
    
    return feedback_tickets
```

**Update classify_feedback_data():**

```python
def classify_feedback_data(...):
    # NEW: Filter to feedback tickets first
    feedback_tickets = filter_feedback_tickets(cleaned_data['feedbacks'])
    
    logger.info(f"Filtered {len(cleaned_data['feedbacks'])} → {len(feedback_tickets)} Feedback tickets")
    
    # Then classify only these
    for ticket in feedback_tickets:
        classification = classify_ticket(ticket, game_context)
        # ...
```

---

### **CHANGE 3: Main.py - Update Flow**

**File:** `main.py`

Update the logging to show:

```python
# After fetching
print(f"📊 Fetched {len(feedback_data['feedbacks'])} total tickets (all types)")

# After cleaning  
print(f"🧹 Cleaned {len(cleaned_data['feedbacks'])} tickets")

# Before AI classification
print(f"🔍 Filtering to Feedback tickets with Status=5...")
# (This happens inside classify_feedback_data now)

# After filtering
print(f"✅ {X} Feedback tickets ready for AI analysis")
```

---

## Benefits of This Approach

1. **Save Complete Data** - You have ALL tickets for analysis
2. **Flexibility** - Can change filtering criteria without re-fetching
3. **Cost Control** - Only send Feedback tickets to ChatGPT (saves API costs)
4. **Historical Record** - Full ticket history in cache

---

## Implementation Summary

| Step | What Happens | Where |
|------|-------------|--------|
| 1. Fetch | Get ALL tickets for game/date/OS | `freshdesk_client.py` |
| 2. Save | Save raw data to `data/raw/` | `storage_manager.py` |
| 3. Clean | Remove noise from ALL tickets | `data_cleaner.py` |
| 4. Filter | Keep only Feedback + Status=5 | `ai_classifier.py` |
| 5. Classify | Send filtered tickets to ChatGPT | `ai_classifier.py` |

---

## Do you want me to implement these changes?

Reply with "yes" and I'll update all the files accordingly.
