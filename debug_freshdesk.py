#!/usr/bin/env python3
"""
Debug script to see what Freshdesk API is actually returning.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.freshdesk_client import FreshdeskClient
import json

print("\n" + "="*80)
print("  FRESHDESK API DEBUG - See What's Actually Returned")
print("="*80 + "\n")

try:
    # Initialize client
    client = FreshdeskClient()
    print(f"✅ Connected to: {client.domain}\n")
    
    # Test 1: Fetch first page of ALL tickets
    print("TEST 1: Fetching first 5 tickets (no filters)")
    print("-" * 80)
    
    response = client._make_request("tickets?per_page=5&page=1")
    tickets = response.json()
    
    if tickets and isinstance(tickets, list):
        print(f"✅ Retrieved {len(tickets)} tickets\n")
        
        for i, ticket in enumerate(tickets, 1):
            print(f"TICKET {i}:")
            print(f"  ID: {ticket.get('id')}")
            print(f"  Subject: {ticket.get('subject', 'N/A')[:60]}...")
            print(f"  Status: {ticket.get('status')} (2=Open, 3=Pending, 4=Resolved, 5=Closed, 6=Waiting)")
            print(f"  Created: {ticket.get('created_at', 'N/A')[:10]}")
            print(f"  Updated: {ticket.get('updated_at', 'N/A')[:10]}")
            
            custom_fields = ticket.get('custom_fields', {})
            if custom_fields:
                print(f"  Custom Fields:")
                for key, value in custom_fields.items():
                    print(f"    {key}: {value}")
            else:
                print(f"  Custom Fields: (none)")
            print()
    else:
        print(f"❌ Unexpected response: {tickets}\n")
    
    # Test 2: Check for Word Trip tickets
    print("\nTEST 2: Looking for Word Trip tickets in first 100")
    print("-" * 80)
    
    response = client._make_request("tickets?per_page=100&page=1")
    all_tickets = response.json()
    
    if isinstance(all_tickets, list):
        print(f"Fetched {len(all_tickets)} tickets\n")
        
        # Count by status
        status_counts = {}
        for t in all_tickets:
            status = t.get('status')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("Status Breakdown:")
        status_names = {2: "Open", 3: "Pending", 4: "Resolved", 5: "Closed", 6: "Waiting"}
        for status, count in sorted(status_counts.items()):
            print(f"  {status} ({status_names.get(status, 'Unknown')}): {count} tickets")
        print()
        
        # Count by game
        game_counts = {}
        for t in all_tickets:
            cf = t.get('custom_fields', {})
            game = cf.get('Game', 'No Game Field')
            game_counts[game] = game_counts.get(game, 0) + 1
        
        print("Game Breakdown:")
        for game, count in sorted(game_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {game}: {count} tickets")
        print()
        
        # Find Word Trip tickets
        word_trip_tickets = [
            t for t in all_tickets
            if 'word trip' in str(t.get('custom_fields', {}).get('Game', '')).lower()
        ]
        
        print(f"Word Trip Tickets Found: {len(word_trip_tickets)}")
        
        if word_trip_tickets:
            print("\nSample Word Trip Ticket:")
            sample = word_trip_tickets[0]
            print(f"  ID: {sample.get('id')}")
            print(f"  Status: {sample.get('status')}")
            print(f"  Subject: {sample.get('subject')}")
            print(f"  Updated: {sample.get('updated_at')}")
            print(f"  Custom Fields: {json.dumps(sample.get('custom_fields', {}), indent=4)}")
        
    else:
        print(f"❌ Unexpected response format\n")
    
    print("\n" + "="*80)
    print("  DEBUG COMPLETE")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
